"""Scheduler wiring tests (LIFE-02, D-01/D-02).

The sweep is scheduled at 03:00 UTC once a day. These tests pin the trigger
and the start/shutdown lifecycle without letting a real sweep run: the
scheduler only executes at the cron instant, so starting it here is
side-effect free. Sweeps run on the same event loop as the app and the
shared pool (CR-01); the actual database behaviour is covered by
``test_expiry_sweep_integration``.
"""

import asyncio

import pytest

from app.core import scheduler as scheduler_module
from app.core.config import get_settings


@pytest.fixture(autouse=True)
async def _clean_scheduler():
    """Never leak a running scheduler from one test into the next."""
    await scheduler_module.shutdown_scheduler()
    yield
    await scheduler_module.shutdown_scheduler()


async def test_scheduler_runs_daily_at_0300_utc():
    scheduler = scheduler_module.start_scheduler()

    assert scheduler is not None
    assert scheduler.running is True

    job = scheduler.get_job(scheduler_module.EXPIRY_JOB_ID)
    assert job is not None
    assert job.next_run_time.hour == 3
    assert job.next_run_time.minute == 0
    assert job.next_run_time.utcoffset().total_seconds() == 0  # UTC


async def test_start_scheduler_is_idempotent():
    first = scheduler_module.start_scheduler()
    second = scheduler_module.start_scheduler()

    assert first is second
    assert len(first.get_jobs()) == 1


async def test_shutdown_stops_the_scheduler():
    scheduler_module.start_scheduler()

    await scheduler_module.shutdown_scheduler()

    assert scheduler_module.get_scheduler() is None


async def test_shutdown_is_safe_to_call_twice():
    scheduler_module.start_scheduler()

    await scheduler_module.shutdown_scheduler()
    await scheduler_module.shutdown_scheduler()

    assert scheduler_module.get_scheduler() is None


async def test_shutdown_waits_for_inflight_sweep():
    """An in-flight sweep completes before shutdown returns (WR-05)."""
    started = asyncio.Event()
    release = asyncio.Event()

    async def fake_sweep():
        started.set()
        await release.wait()
        return 7

    original = scheduler_module._run_expiry_sweep
    scheduler_module._run_expiry_sweep = fake_sweep
    try:
        task = asyncio.create_task(scheduler_module.expire_jobs_job())
        await started.wait()

        shutdown = asyncio.create_task(scheduler_module.shutdown_scheduler())
        await asyncio.sleep(0.05)
        assert not shutdown.done()  # drain is blocking on the sweep
        assert task in scheduler_module._inflight

        release.set()
        assert await asyncio.wait_for(shutdown, timeout=5) is None
        assert (await task) == 7
        assert scheduler_module._inflight == set()
    finally:
        scheduler_module._run_expiry_sweep = original


async def test_scheduler_can_be_disabled(monkeypatch):
    """SCHEDULER_ENABLED=false leaves the in-process clock off (external cron)."""
    monkeypatch.setattr(get_settings(), "SCHEDULER_ENABLED", False)

    assert scheduler_module.start_scheduler() is None
    assert scheduler_module.get_scheduler() is None
