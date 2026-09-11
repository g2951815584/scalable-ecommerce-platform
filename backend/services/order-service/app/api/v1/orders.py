"""Order routes under /api/v1/orders and admin."""

from common.response import success
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_user_id, session_dep
from app.services import order_service


def build_router() -> APIRouter:
    router = APIRouter()

    @router.post("/orders", status_code=201)
    async def create_order(payload: dict, request: Request, uid: int = Depends(current_user_id),
                           session: AsyncSession = Depends(session_dep)):
        items = payload.get("items", [])
        if not items:
            from common.errors import AppError
            raise AppError("ORD-1010", "请选择要购买的商品", 400)
        created = await order_service.create_order(
            session, user_id=uid, items=items, address=payload.get("address"),
            idempotency_key=request.headers.get("Idempotency-Key"), source="WEB")
        return success(created, trace_id=request.state.trace_id)

    @router.get("/orders")
    async def list_orders(request: Request, uid: int = Depends(current_user_id),
                          session: AsyncSession = Depends(session_dep),
                          status: str | None = None, page: int = 1, page_size: int = 20):
        return success(await order_service.list_orders(session, uid, status, page, page_size),
                       trace_id=request.state.trace_id)

    @router.get("/orders/{order_no}")
    async def get_order(order_no: str, request: Request, session: AsyncSession = Depends(session_dep)):
        return success(await order_service.get_order(session, order_no), trace_id=request.state.trace_id)

    @router.post("/orders/{order_no}/cancel")
    async def cancel(order_no: str, payload: dict, request: Request, uid: int = Depends(current_user_id),
                     session: AsyncSession = Depends(session_dep)):
        return success(await order_service.cancel(session, order_no, uid, payload.get("reason", "买家取消")),
                       trace_id=request.state.trace_id)

    @router.post("/orders/{order_no}/confirm")
    async def confirm(order_no: str, request: Request, uid: int = Depends(current_user_id),
                      session: AsyncSession = Depends(session_dep)):
        return success(await order_service.confirm_receipt(session, order_no, uid),
                       trace_id=request.state.trace_id)

    @router.post("/admin/orders/{order_no}/ship")
    async def ship(order_no: str, payload: dict, request: Request, session: AsyncSession = Depends(session_dep)):
        return success(await order_service.ship(session, order_no, payload.get("carrier", "SF"),
                                                payload.get("tracking_no", "")),
                       trace_id=request.state.trace_id)

    return router