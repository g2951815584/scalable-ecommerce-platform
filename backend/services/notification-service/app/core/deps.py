"""FastAPI dependencies for notification-service."""

from collections.abc import AsyncIterator

from common.auth import require_internal as _require_internal
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession


def get_session(request: Request) -> AsyncSession:
    return request.app.state.session_factory()


async def session_dep(request: Request) -> AsyncIterator[AsyncSession]:
    session = get_session(request)
    try:
        yield session
    finally:
        await session.close()


require_internal = _require_internal