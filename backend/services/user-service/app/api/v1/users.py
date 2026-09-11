"""Buyer-facing account routes under /api/v1/users."""

from common.response import success
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_user_id, session_dep
from app.schemas.auth import ChangePasswordRequest, CloseAccountRequest
from app.schemas.user import AddressCreate, AddressUpdate, ProfilePatch
from app.services import address_service, user_service


def build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/users/me")
    async def get_me(request: Request, uid: int = Depends(current_user_id), session: AsyncSession = Depends(session_dep)):
        return success(await user_service.get_user(session, uid), trace_id=request.state.trace_id)

    @router.patch("/users/me")
    async def patch_me(payload: ProfilePatch, request: Request, uid: int = Depends(current_user_id), session: AsyncSession = Depends(session_dep)):
        return success(await user_service.patch_profile(session, uid, payload), trace_id=request.state.trace_id)

    @router.put("/users/me/password")
    async def change_password(payload: ChangePasswordRequest, request: Request, uid: int = Depends(current_user_id), session: AsyncSession = Depends(session_dep)):
        result = await user_service.change_password(session, uid, payload.current_password, payload.new_password)
        return success(result, trace_id=request.state.trace_id, message="密码修改成功")

    @router.delete("/users/me", status_code=204)
    async def close_account(payload: CloseAccountRequest, uid: int = Depends(current_user_id), session: AsyncSession = Depends(session_dep)):
        await user_service.close_account(session, uid, payload.reason)
        return Response(status_code=204)

    @router.get("/users/me/addresses")
    async def list_addresses(request: Request, uid: int = Depends(current_user_id), session: AsyncSession = Depends(session_dep)):
        return success(await address_service.list_addresses_flow(session, uid), trace_id=request.state.trace_id)

    @router.post("/users/me/addresses", status_code=201)
    async def add_address(payload: AddressCreate, request: Request, uid: int = Depends(current_user_id), session: AsyncSession = Depends(session_dep)):
        result = await address_service.add_address_flow(session, uid, payload)
        return success(
            {"address_id": result["address_id"], "is_default": result["is_default"], "created_at": result["created_at"]},
            trace_id=request.state.trace_id,
        )

    @router.get("/users/me/addresses/{address_id}")
    async def get_address(address_id: int, request: Request, uid: int = Depends(current_user_id), session: AsyncSession = Depends(session_dep)):
        return success(await address_service.get_address_flow(session, uid, address_id), trace_id=request.state.trace_id)

    @router.put("/users/me/addresses/{address_id}")
    async def update_address(address_id: int, payload: AddressUpdate, request: Request, uid: int = Depends(current_user_id), session: AsyncSession = Depends(session_dep)):
        result = await address_service.update_address_flow(session, uid, address_id, payload)
        return success(
            {"address_id": result["address_id"], "version": result["version"], "updated_at": result["updated_at"]},
            trace_id=request.state.trace_id,
        )

    @router.delete("/users/me/addresses/{address_id}", status_code=204)
    async def delete_address(address_id: int, uid: int = Depends(current_user_id), session: AsyncSession = Depends(session_dep)):
        await address_service.delete_address_flow(session, uid, address_id)
        return Response(status_code=204)

    @router.put("/users/me/addresses/{address_id}/default")
    async def set_default(address_id: int, request: Request, uid: int = Depends(current_user_id), session: AsyncSession = Depends(session_dep)):
        return success(await address_service.set_default_flow(session, uid, address_id), trace_id=request.state.trace_id)

    return router