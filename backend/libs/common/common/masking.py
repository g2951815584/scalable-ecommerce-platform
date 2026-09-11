"""Field-level masking required by the detailed design's data-protection list.

The log filter masks values by key name (email, phone, password, token, code)
and by shape (E.164 phone, common email addresses).  It operates on structured
``extra`` dictionaries so it never depends on a line-oriented regex pass.
"""

import logging
import re

_EMAIL_RE = re.compile(r"(?P<head>[^@\s]{1,3})[^@\s]*(?P<tail>@[^@\s]+\.[^@\s]+)")
_PHONE_RE = re.compile(r"(\+?\d{3})\d{4,}(\d{4})")

_SENSITIVE_KEYS = {
    "password",
    "access_token",
    "refresh_token",
    "token",
    "authorization",
    "x_internal_token",
    "internal_token",
    "code",
    "verification_code",
    "card_number",
    "cvv",
    "cvc",
    "security_code",
}


def mask_email(value: str) -> str:
    match = _EMAIL_RE.search(value)
    if not match:
        return value
    return f"{match.group('head')}***{match.group('tail')}"


def mask_phone(value: str) -> str:
    match = _PHONE_RE.search(value)
    if not match:
        return value
    return f"{match.group(1)}****{match.group(2)}"


def mask_value(key: str, value: object) -> object:
    """Mask one structured value by its key name; returns the masked value."""
    if not isinstance(value, str):
        return value
    lowered = key.replace(" ", "_").lower()
    if any(sensitive in lowered for sensitive in _SENSITIVE_KEYS):
        return "***"
    if lowered.endswith("email") or "email" in lowered:
        return mask_email(value)
    if lowered.endswith("phone") or "phone" in lowered:
        return mask_phone(value)
    return value


def mask_mapping(mapping: dict) -> dict:
    """Return a new dict with sensitive values masked by key name."""
    return {key: mask_value(str(key), value) for key, value in mapping.items()}


class RedactingFilter(logging.Filter):
    """A logging filter that masks sensitive fields on each record's ``extra``."""

    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            record.extra = mask_mapping(record.extra)  # type: ignore[attr-defined]
        return True