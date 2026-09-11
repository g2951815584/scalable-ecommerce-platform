"""Aggregate all /api/v1 routers for a single include."""

from fastapi import APIRouter

from .admin import build_router as build_admin_router
from .auth import build_router as build_auth_router
from .users import build_router as build_users_router


def build_router() -> APIRouter:
    router = APIRouter()
    router.include_router(build_auth_router())
    router.include_router(build_users_router())
    router.include_router(build_admin_router())
    return router
