"""Shared contracts for the e-commerce service modules."""

from .clock import freeze, unfreeze, utc_now
from .db import (
    Base,
    IdMixin,
    TimestampMixin,
    create_engine_and_session_factory,
    dispose_engine,
)
from .errors import AppError
from .events import EventEnvelope, EventType, InMemoryOutbox, new_event
from .ids import new_id, next_id
from .masking import RedactingFilter, mask_email, mask_mapping, mask_phone
from .outbox import dispatch_pending, make_outbox_event
from .response import ApiResponse, ErrorDetail, failure, success

__all__ = [
    "ApiResponse",
    "AppError",
    "Base",
    "ErrorDetail",
    "EventEnvelope",
    "EventType",
    "IdMixin",
    "InMemoryOutbox",
    "RedactingFilter",
    "TimestampMixin",
    "create_engine_and_session_factory",
    "dispatch_pending",
    "dispose_engine",
    "failure",
    "freeze",
    "make_outbox_event",
    "mask_email",
    "mask_mapping",
    "mask_phone",
    "new_event",
    "new_id",
    "next_id",
    "success",
    "unfreeze",
    "utc_now",
]
