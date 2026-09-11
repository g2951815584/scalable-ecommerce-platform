"""Application factory shared by all service modules."""

from collections.abc import Iterable
from typing import Any

from fastapi import APIRouter, FastAPI

from .errors import install_exception_handlers
from .health import ReadinessCheck, build_health_router
from .metrics import add_metrics_route
from .middleware import TraceMiddleware


def create_service_app(
    service_name: str,
    *,
    version: str = "0.1.0",
    routers: Iterable[tuple[APIRouter, str | None]] = (),
    readiness_checks: dict[str, ReadinessCheck] | None = None,
    lifespan: Any | None = None,
) -> FastAPI:
    """Create a service app with the platform's cross-cutting middleware."""

    app = FastAPI(title=service_name, version=version, lifespan=lifespan)
    app.add_middleware(TraceMiddleware)
    install_exception_handlers(app)
    add_metrics_route(app)
    app.include_router(build_health_router(service_name, readiness_checks))
    for router, prefix in routers:
        app.include_router(router, prefix=prefix or "")

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, Any]:
        return {"service": service_name, "version": version, "docs": "/docs"}

    return app
