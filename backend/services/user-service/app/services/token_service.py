"""JWT access-token signing and opaque refresh-token generation.

Access tokens are RS256-signed and carry ``sub``/``roles``/``jti``/``iat``/``exp``
as mandated by the shared conventions.  Refresh tokens are high-entropy opaque
strings hashed with a pepper before persistence.
"""

from __future__ import annotations

import hashlib
import secrets
import time
from uuid import uuid4

import jwt

from app.core.config import get_settings


def _credentials() -> tuple[str, str]:
    """Return (signing key, algorithm) honouring the RSA configuration.

    Falls back to HMAC for local development so the service can run without an
    injected key pair; production must supply ``JWT_PRIVATE_KEY``.
    """
    settings = get_settings()
    if settings.jwt_private_key:
        return settings.jwt_private_key, "RS256"
    return "dev-insecure-shared-secret-0123456789abcdef", "HS256"


def sign_access_token(user_id: int, roles: list[str]) -> str:
    settings = get_settings()
    key, algorithm = _credentials()
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "roles": roles,
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + settings.access_token_ttl_seconds,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }
    return jwt.encode(payload, key, algorithm=algorithm)


def decode_access_token(token: str) -> dict:
    """Validate an access token (used by tests and the gateway contract)."""
    settings = get_settings()
    if settings.jwt_public_key:
        return jwt.decode(
            token,
            settings.jwt_public_key,
            algorithms=["RS256"],
            audience=settings.jwt_audience,
        )
    key, algorithm = _credentials()
    return jwt.decode(token, key, algorithms=[algorithm], audience=settings.jwt_audience)


def generate_refresh_token() -> str:
    """Return a 32-byte CSPRNG refresh token (base64url, ~43 chars)."""
    return secrets.token_urlsafe(32)


def hash_refresh_token(raw_token: str) -> str:
    settings = get_settings()
    digest = hashlib.sha256(f"{raw_token}{settings.refresh_token_pepper}".encode()).hexdigest()
    return digest


def new_token_family_id():
    return uuid4()


def hash_verification_code(code: str, account: str, scene: str) -> str:
    settings = get_settings()
    return hashlib.sha256(f"{code}{account}{scene}{settings.verify_code_pepper}".encode()).hexdigest()