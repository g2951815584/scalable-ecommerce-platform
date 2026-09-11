"""FastAPI dependencies: database session, identity and roles."""

from collections.abc import AsyncIterator

from common.auth import require_role as _require_role
from common.auth import roles as _roles
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
    """Resolve the gateway-injected identity as an int, or 401."""
    if not x_user_id:
        raise AppError("COMMON-2001", "缺少访问令牌", 401)
    return int(x_user_id)


def current_roles(x_user_roles: str | None = Header(default=None)) -> set[str]:
    return _roles(x_user_roles)


require_role = _require_role