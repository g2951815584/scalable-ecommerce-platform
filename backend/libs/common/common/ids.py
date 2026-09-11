"""Snowflake id generator.

The detailed design mandates 64-bit Snowflake identifiers stored as BIGINT and
serialised as strings in JSON (to avoid JavaScript precision loss).  Layout:

    1 bit  | 41 bits timestamp (ms since epoch) | 10 bits worker | 12 bits sequence
"""

import os
import threading
import time

# 2026-01-01T00:00:00Z in milliseconds.  Keeps the 41-bit field valid for ~69 years.
_EPOCH_MS = 1767225600000
_WORKER_BITS = 10
_SEQUENCE_BITS = 12
_MAX_SEQUENCE = (1 << _SEQUENCE_BITS) - 1

_worker_id = int(os.environ.get("SNOWFLAKE_WORKER_ID", "0")) & ((1 << _WORKER_BITS) - 1)
_lock = threading.Lock()
_last_timestamp = 0
_sequence = 0


def _now_ms() -> int:
    return int(time.time() * 1000)


def next_id() -> int:
    """Return the next 64-bit Snowflake id as an int."""
    global _last_timestamp, _sequence
    with _lock:
        timestamp = _now_ms()
        if timestamp == _last_timestamp:
            _sequence = (_sequence + 1) & _MAX_SEQUENCE
            if _sequence == 0:
                # Sequence exhausted within this millisecond: spin to the next one.
                while timestamp <= _last_timestamp:
                    timestamp = _now_ms()
        else:
            _sequence = 0

        _last_timestamp = timestamp
        relative = timestamp - _EPOCH_MS
        return (
            (relative << (_WORKER_BITS + _SEQUENCE_BITS))
            | (_worker_id << _SEQUENCE_BITS)
            | _sequence
        )


def new_id() -> str:
    """"Return the Snowflake id in its canonical JSON string form."""
    return str(next_id())

