"""Liveness/readiness probes used by Compose and Kubernetes."""

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

ReadinessCheck = Callable[[], Awaitable[bool] | bool]


def build_health_router(service_name: str, readiness_checks: dict[str, ReadinessCheck] | None = None) -> APIRouter:
    router = APIRouter(tags=["health"])
    checks = readiness_checks or {}

    @router.get("/health", include_in_schema=False)
    async def health() -> dict[str, Any]:
        return {"status": "ok", "service": service_name}

    @router.get("/ready", include_in_schema=False)
    async def ready(request: Request) -> JSONResponse:
        active: dict[str, ReadinessCheck] = getattr(request.app.state, "readiness_checks", None) or checks
        results: dict[str, bool] = {}
        for name, check in active.items():
            value = check()
            results[name] = bool(await value) if hasattr(value, "__await__") else bool(value)
        healthy = all(results.values()) if results else True
        status_code = 200 if healthy else 503
        return JSONResponse(
            status_code=status_code,
            content={"status": "ready" if healthy else "not_ready", "service": service_name, "checks": results},
        )

    return router
