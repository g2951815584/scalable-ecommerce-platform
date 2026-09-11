"""RabbitMQ event publisher/consumer primitives.

Events flow over the persistent topic exchange ``ecommerce.events`` with the
routing key equal to ``event_type``.  Consumers declare a durable queue named
``{service}.{event_type}`` and a dead-letter exchange ``ecommerce.events.dlx``.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

logger = logging.getLogger("ecommerce.mq")

EXCHANGE = "ecommerce.events"
DLX_EXCHANGE = "ecommerce.events.dlx"

MessageHandler = Callable[[dict[str, Any]], Awaitable[None]]


class EventPublisher:
    """Publish event envelopes to the topic exchange."""

    def __init__(self, url: str) -> None:
        self._url = url
        self._connection = None
        self._exchange = None

    async def connect(self) -> None:
        import aio_pika

        self._connection = await aio_pika.connect_robust(self._url)
        channel = await self._connection.channel()
        await channel.declare_exchange(DLX_EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
        self._exchange = await channel.declare_exchange(
            EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True
        )

    async def publish(self, envelope: dict[str, Any]) -> None:
        import aio_pika

        if self._exchange is None:
            raise RuntimeError("EventPublisher.connect() must be called first")
        body = json.dumps(envelope, ensure_ascii=False, default=str).encode("utf-8")
        message = aio_pika.Message(body=body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT)
        await self._exchange.publish(message, routing_key=str(envelope.get("event_type")))

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()


class EventConsumer:
    """Consume one queue; delegates each JSON envelope to a handler."""

    def __init__(self, url: str, queue_name: str, routing_key: str, handler: MessageHandler) -> None:
        self._url = url
        self._queue_name = queue_name
        self._routing_key = routing_key
        self._handler = handler
        self._connection = None

    async def start(self) -> None:
        import aio_pika

        self._connection = await aio_pika.connect_robust(self._url)
        channel = await self._connection.channel()
        await channel.set_qos(prefetch_count=10)
        exchange = await channel.declare_exchange(EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
        await channel.declare_exchange(DLX_EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
        queue = await channel.declare_queue(
            self._queue_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": DLX_EXCHANGE,
                "x-dead-letter-routing-key": f"{self._queue_name}.dlq",
            },
        )
        await queue.bind(exchange, routing_key=self._routing_key)

        async def on_message(message) -> None:  # type: ignore[no-untyped-def]
            async with message.process():
                try:
                    envelope = json.loads(message.body.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                    logger.warning("undecodable event body on %s: %s", self._queue_name, exc)
                    return
                await self._handler(envelope)

        await queue.consume(on_message)

    async def stop(self) -> None:
        if self._connection is not None:
            await self._connection.close()