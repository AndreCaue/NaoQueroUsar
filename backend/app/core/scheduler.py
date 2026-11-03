"""In-process expiry scheduler (LIFE-02, LIFE-03 — D-01/D-02).

A ``AsyncIOScheduler`` runs one sweep a day at 03:00 UTC that hard deletes
every job past ``expires_at``. The sweep itself lives in
``app.crud.jobs.delete_expired_jobs``; this module only owns the clock and the
short-lived session it runs in.

Why ``AsyncIOScheduler`` (and not a thread + ``asyncio.run``):
APScheduler's ``AsyncIOScheduler`` schedules coroutine jobs as tasks on the
*same* event loop that serves FastAPI and owns the shared asyncpg pool. The
sweep therefore never checks out connections from a different — or an already
closed — loop. The previous ``BackgroundScheduler`` + ``asyncio.run`` model
ran each sweep in a worker thread against a brand-new event loop while sharing
the module-level ``AsyncEngine``; pooled connections could cross loops, and
subsequent requests could receive connections bound to a dead loop (CR-01).

Operational notes:
- The job is idempotent (deleting nothing is a no-op), so duplicate runs — a
  restart catching up, or a second worker in the same box — are harmless
  (T-06-02/T-06-03).
- Shutdown is deterministic: the scheduler is paused (no new sweep starts),
  in-flight sweeps are awaited with a bounded timeout, and only then is the
  engine disposed in the lifespan (WR-05). APScheduler's asyncio executor
  cannot truly wait — it cancels pending futures — so the bounded drain here
  is the real guarantee that the pool is not disposed mid-``DELETE``.
- ``SCHEDULER_ENABLED=false`` turns the in-process clock off entirely; the
  ``POST /api/v1/admin/expire`` endpoint remains available for an external
  cron (LIFE-04). Free-tier hosts that spin down do not run the scheduler
  while asleep, which is exactly what that endpoint is here for.
"""

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.crud.jobs import delete_expired_jobs
from app.db.session import async_session_factory

logger = logging.getLogger(__name__)

# D-02: one daily sweep at 03:00 UTC (quiet hour for a pt-BR audience).
EXPIRY_HOUR_UTC = 3
EXPIRY_MINUTE_UTC = 0

# Stable id so a re-start replaces instead of duplicating the job.
EXPIRY_JOB_ID = "expire-jobs"

# Upper bound for draining an in-flight sweep during shutdown. The delete is
# a single statement; 30 s is generous and still bounded.
_DRAIN_TIMEOUT_SECONDS = 30.0

__all__ = [
    "EXPIRY_HOUR_UTC",
    "EXPIRY_MINUTE_UTC",
    "EXPIRY_JOB_ID",
    "expire_jobs_job",
    "get_scheduler",
    "start_scheduler",
    "shutdown_scheduler",
]

_scheduler: AsyncIOScheduler | None = None

# Tasks currently executing a sweep (registered by ``expire_jobs_job`` itself,
# since the scheduler creates the task). Tracked so shutdown can drain them
# before the engine is disposed (WR-05).
_inflight: set[asyncio.Task] = set()


async def _run_expiry_sweep() -> int:
    """Open a session, hard delete expired jobs, commit, and return the count."""
    async with async_session_factory() as session:
        try:
            deleted = await delete_expired_jobs(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise
    return deleted


async def expire_jobs_job() -> int:
    """Scheduler entry point: run one expiry sweep on the app's event loop.

    Never raises: a transient database failure is logged and the next daily
    run (or the ``CRON_SECRET`` catch-up) retries, so one bad night cannot
    kill the scheduler.
    """
    task = asyncio.current_task()
    if task is not None:
        _inflight.add(task)
    try:
        deleted = await _run_expiry_sweep()
    except Exception:
        logger.exception("expiry sweep falhou; nova tentativa no proximo ciclo")
        return 0
    finally:
        if task is not None:
            _inflight.discard(task)

    logger.info("expiry sweep removeu %s vaga(s) expirada(s)", deleted)
    return deleted


def get_scheduler() -> AsyncIOScheduler | None:
    """Return the running scheduler, or ``None`` when it was never started."""
    return _scheduler


def start_scheduler() -> AsyncIOScheduler | None:
    """Start the daily expiry sweep (idempotent; returns ``None`` if disabled).

    Must be called from inside the event loop (the lifespan does so) —
    ``AsyncIOScheduler.start`` binds itself to the running loop.
    """
    global _scheduler

    if not get_settings().SCHEDULER_ENABLED:
        logger.info("scheduler de expiracao desativado (SCHEDULER_ENABLED=false)")
        return None

    if _scheduler is not None and _scheduler.running:
        return _scheduler

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        expire_jobs_job,
        CronTrigger(
            hour=EXPIRY_HOUR_UTC,
            minute=EXPIRY_MINUTE_UTC,
            timezone="UTC",
        ),
        id=EXPIRY_JOB_ID,
        replace_existing=True,
        # One sweep at a time; a skipped night collapses into a single run
        # instead of a burst of catch-ups (coalesce), with an hour of slack.
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info(
        "scheduler de expiracao iniciado (diario as %02d:%02d UTC)",
        EXPIRY_HOUR_UTC,
        EXPIRY_MINUTE_UTC,
    )
    return scheduler


async def _drain_inflight(timeout: float) -> None:
    """Wait (bounded, non-cancelling) for in-flight sweeps to finish."""
    pending = [task for task in _inflight if not task.done()]
    if not pending:
        return

    logger.info(
        "aguardando %d sweep(s) de expiracao em andamento (ate %.0fs)",
        len(pending),
        timeout,
    )
    # ``asyncio.wait`` does not cancel the tasks on timeout — an in-flight
    # DELETE is left to finish (or to be cancelled by the caller's teardown).
    _, still_pending = await asyncio.wait(pending, timeout=timeout)
    if still_pending:
        logger.warning(
            "sweep de expiracao nao concluiu em %.0fs; seguindo com o shutdown "
            "(a delecao e idempotente — o proximo ciclo refaz)",
            timeout,
        )


async def shutdown_scheduler() -> None:
    """Stop the scheduler and drain in-flight sweeps (safe to call twice).

    Called by the lifespan **before** ``engine.dispose()``: the scheduler is
    paused so no new sweep starts, in-flight sweeps are awaited with a
    bounded timeout, and only then is the clock stopped. Disposal of the
    pool therefore never happens underneath a running ``DELETE``.
    """
    global _scheduler

    scheduler, _scheduler = _scheduler, None

    if scheduler is not None and scheduler.running:
        # Pause first: no new sweep may start while we drain the current one.
        # ``pause`` raises only when the scheduler is already stopped.
        try:
            scheduler.pause()
        except Exception:
            logger.debug("scheduler.pause() ignorado (ja parado?)", exc_info=True)

    # Drain whether or not a scheduler instance exists — a sweep launched
    # manually (or by an earlier scheduler) shares the same pool, and the
    # engine is disposed right after this returns.
    await _drain_inflight(_DRAIN_TIMEOUT_SECONDS)

    if scheduler is not None:
        # AsyncIOScheduler dispatches shutdown through ``call_soon_threadsafe``;
        # it also cancels pending futures instead of waiting for them — the
        # drain above is the real guarantee. ``wait=True`` keeps the contract
        # explicit and correct for schedulers whose executors do honor it.
        try:
            scheduler.shutdown(wait=True)
        except Exception:
            logger.warning("scheduler.shutdown falhou", exc_info=True)
        # Let the loop run the deferred shutdown callback before the lifespan
        # proceeds to ``engine.dispose()``.
        await asyncio.sleep(0)
        logger.info("scheduler de expiracao encerrado")
