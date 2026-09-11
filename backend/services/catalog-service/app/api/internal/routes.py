"""Internal inventory and SKU routes for cart/order services."""

from common.auth import require_internal
from common.response import success
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import session_dep
from app.schemas import BatchQueryRequest, ConfirmRequest, ReleaseRequest, ReserveRequest
from app.services import inventory_service


def build_router() -> APIRouter:
    router = APIRouter(dependencies=[Depends(require_internal())])

    @router.post("/inventory/batch-query")
    async def batch_query(payload: BatchQueryRequest, request: Request, session: AsyncSession = Depends(session_dep)):
        result = await inventory_service.batch_query(session, [int(s) for s in payload.sku_ids])
        return success(result, trace_id=request.state.trace_id)

    @router.post("/inventory/reserve")
    async def reserve(payload: ReserveRequest, request: Request, session: AsyncSession = Depends(session_dep)):
        items = [{"sku_id": i.sku_id, "quantity": i.quantity} for i in payload.items]
        result = await inventory_service.reserve(session, order_no=payload.order_no, items=items)
        return success(result, trace_id=request.state.trace_id)

    @router.post("/inventory/release")
    async def release(payload: ReleaseRequest, request: Request, session: AsyncSession = Depends(session_dep)):
        items = None
        if payload.items:
            items = [{"sku_id": i.sku_id, "quantity": i.quantity} for i in payload.items]
        result = await inventory_service.release(
            session, order_no=payload.order_no, items=items, reason=payload.reason)
        return success(result, trace_id=request.state.trace_id)

    @router.post("/inventory/confirm")
    async def confirm(payload: ConfirmRequest, request: Request, session: AsyncSession = Depends(session_dep)):
        items = [{"sku_id": i.sku_id, "quantity": i.quantity} for i in payload.items]
        result = await inventory_service.confirm(
            session, order_no=payload.order_no, items=items, event_id=payload.event_id)
        return success(result, trace_id=request.state.trace_id)

    return router