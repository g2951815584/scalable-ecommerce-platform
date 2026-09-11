"""Forward-auth service for the Traefik gateway.

Traefik delegates every request on a protected router to this service via the
``forwardAuth`` middleware.  The service validates the bearer token, then
returns the resolved identity as response headers that Traefik copies onto the
forwarded request (``authResponseHeaders``).  Because Traefik *replaces* any
same-named request header, a client supplied ``X-User-Id`` / ``X-User-Roles``
can never reach the downstream service — this is the identity-header spoofing
defence required by the platform design.

Signing scheme:

* ``JWT_PUBLIC_KEY`` set  -> RS256 verification with the injected public key.
* ``JWT_PUBLIC_KEY`` empty -> HS256 with the shared dev secret, mirroring the
  user-service fallback so the whole stack can boot without key plumbing.
"""

from __future__ import annotations

import os

import jwt
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

app = FastAPI(title="gateway-auth", version="0.1.0")

_DEV_SECRET = "dev-insecure-shared-secret-0123456789abcdef"


def _settings() -> tuple[str, list[str], str]:
    public_key = os.getenv("JWT_PUBLIC_KEY", "")
    issuer = os.getenv("JWT_ISSUER", "user-service")
    audience = os.getenv("JWT_AUDIENCE", "ecommerce-platform")
    if public_key:
        return public_key, ["RS256"], audience
    return _DEV_SECRET, ["HS256"], audience


def _verify(token: str) -> dict | None:
    key, algorithms, audience = _settings()
    try:
        payload = jwt.decode(token, key, algorithms=algorithms, audience=audience)
        if "sub" not in payload or not payload["sub"]:
            return None
        return payload
    except jwt.PyJWTError:
        return None


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.headers.get("X-Real-Ip", "")


def _identity_response(payload: dict | None, request: Request, allow_anonymous: bool) -> Response:
    if payload is None:
        if not allow_anonymous:
            return JSONResponse(
                {"code": "COMMON-2002", "message": "访问令牌无效或已过期", "data": None},
                status_code=401,
            )
        # Anonymous access (guest cart): explicitly blank the identity headers so
        # Traefik overwrites any spoofed client value with an empty string.
        response = Response(status_code=200)
    else:
        response = Response(status_code=200)
        roles = payload.get("roles") or []
        response.headers["X-User-Id"] = str(payload["sub"])
        response.headers["X-User-Roles"] = ",".join(str(r) for r in roles)

    # Ensure the identity headers are always present on the response so Traefik
    # can copy them downstream (and blank out spoofed upstream values).
    response.headers.setdefault("X-User-Id", "")
    response.headers.setdefault("X-User-Roles", "")
    # Never let a client-supplied internal token survive to the backend.
    response.headers["X-Internal-Token"] = ""
    response.headers["X-Client-Ip"] = _client_ip(request)
    return response


@app.api_route("/auth", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
async def auth_required(request: Request) -> Response:
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        return JSONResponse(
            {"code": "COMMON-2001", "message": "缺少访问令牌", "data": None}, status_code=401
        )
    payload = _verify(authorization[7:].strip())
    return _identity_response(payload, request, allow_anonymous=False)


@app.api_route(
    "/auth-optional",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def auth_optional(request: Request) -> Response:
    authorization = request.headers.get("Authorization", "")
    payload = None
    if authorization.startswith("Bearer "):
        payload = _verify(authorization[7:].strip())
    return _identity_response(payload, request, allow_anonymous=True)


@app.get("/health")
async def health() -> dict:
    return {"status": "UP", "service": "gateway-auth"}