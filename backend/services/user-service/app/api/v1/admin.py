"""Admin routes under /api/v1/admin."""

from common.auth import require_role
from common.response import success
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_user_id, session_dep
from app.schemas.admin import AssignRolesRequest, SetStatusRequest
from app.services import user_service


def build_router() -> APIRouter:
    router = APIRouter(dependencies=[Depends(require_role("ADMIN"))])

    @router.get("/users")
    async def list_users(request: Request, session: AsyncSession = Depends(session_dep),
                         page: int = 1, page_size: int = 20, status: str | None = None,
                         keyword: str | None = None):
        result = await user_service.list_users(session, page=page, page_size=page_size,
                                               status=status, keyword=keyword)
        return success(result, trace_id=request.state.trace_id)

    @router.put("/users/{user_id}/roles")
    async def assign_roles(user_id: int, payload: AssignRolesRequest, request: Request,
                           admin_id: int = Depends(current_user_id), session: AsyncSession = Depends(session_dep)):
        result = await user_service.assign_roles(session, user_id, payload.role_codes,
                                                 admin_id=admin_id, reason=payload.reason)
        return success(result, trace_id=request.state.trace_id)

    @router.put("/users/{user_id}/status")
    async def set_status(user_id: int, payload: SetStatusRequest, request: Request,
                         admin_id: int = Depends(current_user_id), session: AsyncSession = Depends(session_dep)):
        result = await user_service.set_status(session, user_id, payload.status,
                                               admin_id=admin_id, reason=payload.reason)
        return success(result, trace_id=request.state.trace_id)

    @router.get("/roles")
    async def list_roles(request: Request, session: AsyncSession = Depends(session_dep)):
        return success({"items": await user_service.list_roles(session), "total": 0},
                       trace_id=request.state.trace_id)

    @router.get("/permissions")
    async def list_permissions(request: Request, session: AsyncSession = Depends(session_dep)):
        return success({"items": await user_service.list_permissions(session), "total": 0,
                        "modules": []}, trace_id=request.state.trace_id)

    return router