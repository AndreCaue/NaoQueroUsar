"""In-process expiry scheduler (LIFE-02, LIFE-03 — D-01/D-02).

A ``BackgroundScheduler`` runs one sweep a day at 03:00 UTC that hard deletes
every job past ``expires_at``. The sweep itself lives in
``app.crud.jobs.delete_expired_jobs``; this module only owns the clock and the
short-lived session it runs in.

Why a thread scheduler and ``asyncio.run``:
APScheduler 3.x's ``BackgroundScheduler`` calls jobs from a worker thread, so
the async CRUD entry point is driven through a fresh event loop in that thread
instead of reusing the request loop (which may not exist — the scheduler also
runs before/after traffic).

Operational notes:
- The job is idempotent (deleting nothing is a no-op), so duplicate runs — a
  restart catching up, or a second worker in the same box — are harmless
  (T-06-02/T-06-03).
- ``SCHEDULER_ENABLED=false`` turns the in-process clock off entirely; the
  ``POST /api/v1/admin/expire`` endpoint remains available for an external
  cron (LIFE-04). Free-tier hosts that spin down do not run the scheduler
  while asleep, which is exactly what that endpoint is here for.
"""

import asyncio
import logging

from apscheduler.schedulers.background import BackgroundScheduler
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

__all__ = [
    "EXPIRY_HOUR_UTC",
    "EXPIRY_MINUTE_UTC",
    "EXPIRY_JOB_ID",
    "expire_jobs_job",
    "get_scheduler",
    "start_scheduler",
    "shutdown_scheduler",
]

_scheduler: BackgroundScheduler | None = None


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


def expire_jobs_job() -> int:
    """Scheduler entry point: run one expiry sweep in this (worker) thread.

    Never raises: a transient database failure is logged and the next daily
    run (or the ``CRON_SECRET`` catch-up) retries, so one bad night cannot kill
    the scheduler's worker thread.
    """
    try:
        deleted = asyncio.run(_run_expiry_sweep())
    except Exception:
        logger.exception("expiry sweep falhou; nova tentativa no proximo ciclo")
        return 0

    logger.info("expiry sweep removeu %s vaga(s) expirada(s)", deleted)
    return deleted


def get_scheduler() -> BackgroundScheduler | None:
    """Return the running scheduler, or ``None`` when it was never started."""
    return _scheduler


def start_scheduler() -> BackgroundScheduler | None:
    """Start the daily expiry sweep (idempotent; returns ``None`` if disabled)."""
    global _scheduler

    if not get_settings().SCHEDULER_ENABLED:
        logger.info("scheduler de expiracao desativado (SCHEDULER_ENABLED=false)")
        return None

    if _scheduler is not None and _scheduler.running:
        return _scheduler

    scheduler = BackgroundScheduler(timezone="UTC")
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


def shutdown_scheduler() -> None:
    """Stop the scheduler if it is running (safe to call twice)."""
    global _scheduler

    if _scheduler is None:
        return

    if _scheduler.running:
        # ``wait=False``: never block application shutdown on a sweep that is
        # already in flight. The delete is idempotent, so an interrupted run is
        # simply repeated by the next one.
        _scheduler.shutdown(wait=False)
        logger.info("scheduler de expiracao encerrado")

    _scheduler = None
