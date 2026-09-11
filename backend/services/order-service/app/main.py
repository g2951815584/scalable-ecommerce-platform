"""order-service application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from common.app import create_service_app
from common.db import create_engine_and_session_factory, dispose_engine
from common.mq import EventConsumer, EventPublisher
from fastapi import FastAPI

from app.api.internal.routes import build_router as build_internal_router
from app.api.v1.orders import build_router
from app.core.config import get_settings
from app.events.consumer import handle_payment_succeeded
from app.tasks.scheduler import build_scheduler

logger = logging.getLogger("order-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    engine, session_factory = create_engine_and_session_factory(settings.database_url)
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.settings = settings

    publisher: EventPublisher | None = None
    consumers: list[EventConsumer] = []
    try:
        publisher = EventPublisher(settings.rabbitmq_url)
        await publisher.connect()
        consumers.append(EventConsumer(
            settings.rabbitmq_url, "order.payment.succeeded", "payment.succeeded",
            lambda e: handle_payment_succeeded(session_factory, e)))
        for consumer in consumers:
            await consumer.start()
    except Exception:
        logger.warning("RabbitMQ unavailable; consumers disabled", exc_info=True)
        publisher = None
    app.state.publisher = publisher

    scheduler = build_scheduler(session_factory, publisher)
    scheduler.start()
    app.state.scheduler = scheduler

    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
        for consumer in consumers:
            await consumer.stop()
        if publisher is not None:
            await publisher.close()
        await dispose_engine(engine)


app = create_service_app(
    get_settings().service_name,
    routers=[(build_router(), "/api/v1"), (build_internal_router(), "/internal/v1")],
    lifespan=lifespan,
)