"""Internal service-to-service routes."""

from common.auth import require_internal
from common.response import success
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import session_dep
from app.schemas.user import BatchUsersRequest
from app.services import address_service, user_service


def build_router() -> APIRouter:
    router = APIRouter(dependencies=[Depends(require_internal())])

    @router.post("/users/batch")
    async def batch_users(payload: BatchUsersRequest, request: Request, session: AsyncSession = Depends(session_dep)):
        items, missing = [], []
        for uid in payload.user_ids:
            try:
                item = await user_service.get_user(session, int(uid))
            except Exception:
                missing.append(uid)
                continue
            if payload.fields:
                item = {"user_id": uid, **{f: item[f] for f in payload.fields if f in item}}
            items.append(item)
        return success({"items": items, "missing_user_ids": missing}, trace_id=request.state.trace_id)

    @router.get("/users/{user_id}/profile")
    async def profile(user_id: int, request: Request, session: AsyncSession = Depends(session_dep)):
        item = await user_service.get_user(session, user_id)
        return success(item, trace_id=request.state.trace_id)

    @router.get("/users/{user_id}/addresses/{address_id}")
    async def address(user_id: int, address_id: int, request: Request, session: AsyncSession = Depends(session_dep)):
        item = await address_service.get_address_flow(session, user_id, address_id)
        return success(
            {"address_id": str(address_id), "user_id": str(user_id), "belongs_to_user": True,
             "snapshot": item, "version": item["version"]},
            trace_id=request.state.trace_id,
        )

    return router
