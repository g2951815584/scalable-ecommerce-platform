"""Header-based identity dependencies.

The gateway validates JWTs and injects these headers.  Service modules never
trust a user id supplied in a JSON body or query string for ownership checks.
"""

from collections.abc import Callable

from fastapi import Header

from .config import CommonSettings, get_common_settings
from .errors import AppError


def optional_user_id(x_user_id: str | None = Header(default=None)) -> str | None:
    return x_user_id


def user_id(x_user_id: str | None = Header(default=None)) -> str:
    if not x_user_id:
        raise AppError("COMMON-2001", "缺少访问令牌", 401)
    return x_user_id


def roles(x_user_roles: str | None = Header(default=None)) -> set[str]:
    return {role.strip().upper() for role in (x_user_roles or "").split(",") if role.strip()}


def require_role(*required: str) -> Callable:
    required_roles = {role.upper() for role in required}

    def dependency(x_user_roles: str | None = Header(default=None)) -> set[str]:
        actual = roles(x_user_roles)
        if not actual.intersection(required_roles):
            raise AppError("COMMON-3001", "无权限执行该操作", 403)
        return actual

    return dependency


def require_internal(settings: CommonSettings | None = None) -> Callable:
    config = settings or get_common_settings()

    def dependency(x_internal_token: str | None = Header(default=None)) -> None:
        if not config.internal_token or x_internal_token != config.internal_token:
            raise AppError("COMMON-2002", "访问令牌无效或已过期", 401)

    return dependency
