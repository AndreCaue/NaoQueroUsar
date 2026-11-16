from datetime import datetime, timezone
from types import SimpleNamespace

from app.services.social.publish_pipeline import compute_next_retry


def _settings(max_attempts=5, delays="300,900,3600,10800,21600"):
    return SimpleNamespace(
        SOCIAL_MAX_ATTEMPTS=max_attempts,
        social_retry_delays_list=[int(x) for x in delays.split(",")],
    )


def test_compute_next_retry_uses_defaults_and_progressive_backoff():
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    settings = _settings(5, "300,900,3600,10800,21600")

    r1 = compute_next_retry(1, settings, now=now)
    r2 = compute_next_retry(2, settings, now=now)
    r3 = compute_next_retry(3, settings, now=now)
    r4 = compute_next_retry(4, settings, now=now)

    assert r1 == datetime(2026, 1, 1, 12, 5, tzinfo=timezone.utc)
    assert r2 == datetime(2026, 1, 1, 12, 15, tzinfo=timezone.utc)
    assert r3 == datetime(2026, 1, 1, 13, 0, tzinfo=timezone.utc)
    assert r4 == datetime(2026, 1, 1, 15, 0, tzinfo=timezone.utc)


def test_compute_next_retry_returns_none_when_exhausted():
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    settings = _settings(5, "300,900,3600,10800,21600")

    assert compute_next_retry(5, settings, now=now) is None
    assert compute_next_retry(6, settings, now=now) is None


def test_compute_next_retry_respects_configured_max_attempts_and_delays():
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    settings = _settings(3, "60,120,240")

    assert compute_next_retry(1, settings, now=now) == datetime(2026, 1, 1, 12, 1, tzinfo=timezone.utc)
    assert compute_next_retry(2, settings, now=now) == datetime(2026, 1, 1, 12, 2, tzinfo=timezone.utc)
    assert compute_next_retry(3, settings, now=now) is None
