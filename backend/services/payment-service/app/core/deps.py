"""FastAPI dependencies for payment-service."""

from collections.abc import AsyncIterator

from common.auth import require_internal as _require_internal
from common.errors import AppError
from fastapi import Header, Request
from sqlalchemy.ext.asyncio import AsyncSession


def get_session(request: Request) -> AsyncSession:
    return request.app.state.session_factory()


async def session_dep(request: Request) -> AsyncIterator[AsyncSession]:
    session = get_session(request)
    try:
        yield session
    finally:
        await session.close()


def current_user_id(x_user_id: str | None = Header(default=None)) -> int:
    if not x_user_id:
        raise AppError("COMMON-2001", "缺少访问令牌", 401)
    return int(x_user_id)


require_internal = _require_internal