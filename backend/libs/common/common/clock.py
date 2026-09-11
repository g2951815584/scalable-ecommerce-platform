"""Injectable clock.

Business rules around timeouts, locks and expiries must be reproducible in tests.
Modules import :func:`utc_now` instead of calling ``datetime.now`` directly so a
test can freeze or advance time without touching wall-clock code.
"""

from datetime import UTC, datetime

_override: datetime | None = None


def utc_now() -> datetime:
    """Return the current UTC time, honouring any injected clock override."""
    if _override is not None:
        return _override
    return datetime.now(UTC)


def freeze(at: datetime) -> None:
    """Override the clock for the current process (test helper)."""
    global _override
    _override = at


def unfreeze() -> None:
    """Clear any clock override."""
    global _override
    _override = None