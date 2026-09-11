"""Redis-backed idempotency primitives.

The general pattern is ``SET key value NX EX ttl``: only the request that wins the
NAND lock proceeds; every other request reads back the stored value.  Services
wrap this in their own idempotency stores and always keep a DB unique index as
the final fallback.
"""

from typing import Any

import redis.asyncio as aioredis


async def acquire(
    client: aioredis.Redis, key: str, value: str | bytes, ttl: int
) -> bool:
    """Try to claim ``key``; return True only when the claim was won."""
    return bool(await client.set(key, value, nx=True, ex=ttl))


async def read(client: aioredis.Redis, key: str) -> str | None:
    """Read the stored claim value, if any."""
    return await client.get(key)


async def release(client: aioredis.Redis, key: str) -> None:
    """Drop a claim (used when a business operation fails and should retry)."""
    await client.delete(key)


async def get_del(client: aioredis.Redis, key: str) -> str | None:
    """Atomically read and delete a key (one-shot tickets / OAuth state)."""
    return await client.getdel(key)


def settle_key(namespace: str, *parts: Any) -> str:
    """Join idempotency key parts into ``{namespace}:{p1}:{p2}``."""
    return ":".join([namespace, *(str(part) for part in parts)])