"""Scheduler wiring tests (LIFE-02, D-01/D-02).

The sweep is scheduled at 03:00 UTC once a day. These tests pin the trigger
and the start/shutdown lifecycle without letting a real sweep run: the
scheduler thread only executes at the cron instant, so starting it here is
side-effect free.
"""

import pytest

from app.core import scheduler as scheduler_module
from app.core.config import get_settings


@pytest.fixture(autouse=True)
def _clean_scheduler():
    """Never leak a running scheduler from one test into the next."""
    scheduler_module.shutdown_scheduler()
    yield
    scheduler_module.shutdown_scheduler()


def test_scheduler_runs_daily_at_0300_utc():
    scheduler = scheduler_module.start_scheduler()

    assert scheduler is not None
    assert scheduler.running is True

    job = scheduler.get_job(scheduler_module.EXPIRY_JOB_ID)
    assert job is not None
    assert job.next_run_time.hour == 3
    assert job.next_run_time.minute == 0
    assert job.next_run_time.utcoffset().total_seconds() == 0  # UTC


def test_start_scheduler_is_idempotent():
    first = scheduler_module.start_scheduler()
    second = scheduler_module.start_scheduler()

    assert first is second
    assert len(first.get_jobs()) == 1


def test_shutdown_stops_the_scheduler():
    scheduler_module.start_scheduler()

    scheduler_module.shutdown_scheduler()

    assert scheduler_module.get_scheduler() is None


def test_scheduler_can_be_disabled(monkeypatch):
    """SCHEDULER_ENABLED=false leaves the in-process clock off (external cron)."""
    monkeypatch.setattr(get_settings(), "SCHEDULER_ENABLED", False)

    assert scheduler_module.start_scheduler() is None
    assert scheduler_module.get_scheduler() is None
