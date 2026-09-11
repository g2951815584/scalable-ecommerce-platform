"""cart-service application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from common.app import create_service_app
from common.db import create_engine_and_session_factory, dispose_engine
from common.redis import close_redis, create_redis
from fastapi import FastAPI

from app.api.internal.routes import build_router as build_internal_router
from app.api.v1.cart import build_router
from app.core.config import get_settings

logger = logging.getLogger("cart-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    engine, session_factory = create_engine_and_session_factory(settings.database_url)
    redis = create_redis(settings.redis_url)
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.redis = redis
    app.state.settings = settings
    try:
        yield
    finally:
        await close_redis(redis)
        await dispose_engine(engine)


app = create_service_app(
    get_settings().service_name,
    routers=[
        (build_router(), "/api/v1"),
        (build_internal_router(), "/internal/v1"),
    ],
    lifespan=lifespan,
)