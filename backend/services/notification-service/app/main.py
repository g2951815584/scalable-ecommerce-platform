"""notification-service application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from common.app import create_service_app
from common.db import create_engine_and_session_factory, dispose_engine
from common.mq import EventConsumer
from fastapi import FastAPI

from app.api.v1.notifications import build_router
from app.core.config import get_settings
from app.events.consumer import SUBSCRIBED_EVENTS, handle_event

logger = logging.getLogger("notification-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    engine, session_factory = create_engine_and_session_factory(settings.database_url)
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.settings = settings

    consumers: list[EventConsumer] = []
    try:
        for event_type in SUBSCRIBED_EVENTS:
            queue = f"notification.{event_type}"
            consumers.append(EventConsumer(
                settings.rabbitmq_url, queue, event_type,
                lambda e, et=event_type: handle_event(session_factory, settings, e)))
        for consumer in consumers:
            await consumer.start()
    except Exception:
        logger.warning("RabbitMQ unavailable; consumers disabled", exc_info=True)

    try:
        yield
    finally:
        for consumer in consumers:
            await consumer.stop()
        await dispose_engine(engine)


app = create_service_app(
    get_settings().service_name,
    routers=[(build_router(), "/api/v1")],
    lifespan=lifespan,
)