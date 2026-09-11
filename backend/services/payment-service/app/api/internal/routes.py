"""Internal payment routes for order-service."""

from common.auth import require_internal
from common.response import success
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import session_dep
from app.services import payment_service


def build_router() -> APIRouter:
    router = APIRouter(dependencies=[Depends(require_internal())])

    @router.get("/payments/by-order/{order_no}")
    async def by_order(order_no: str, request: Request, session: AsyncSession = Depends(session_dep)):
        return success(await payment_service.by_order(session, order_no), trace_id=request.state.trace_id)

    return router