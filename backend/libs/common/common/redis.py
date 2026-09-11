"""Async Redis client factory.

Services hold one ``redis.asyncio.Redis`` instance for caching, idempotency keys,
distributed locks, counters and cart primary storage.  The connection is created
from ``REDIS_URL`` in the service settings.
"""

import redis.asyncio as aioredis


def create_redis(url: str, *, decode_responses: bool = True) -> aioredis.Redis:
    """Return a Redis client seeded from the service settings."""
    return aioredis.from_url(url, decode_responses=decode_responses)


async def close_redis(client: aioredis.Redis) -> None:
    """Close the Redis connection pool during shutdown."""
    await client.aclose()