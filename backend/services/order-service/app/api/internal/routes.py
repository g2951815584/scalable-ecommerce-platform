"""Internal order routes for payment-service."""

from common.auth import require_internal
from common.response import success
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import session_dep
from app.services import order_service


def build_router() -> APIRouter:
    router = APIRouter(dependencies=[Depends(require_internal())])

    @router.get("/orders/{order_no}/amount")
    async def order_amount(order_no: str, request: Request, session: AsyncSession = Depends(session_dep)):
        data = await order_service.get_order(session, order_no)
        return success({
            "order_no": order_no, "user_id": "", "status": data["status"],
            "payable_amount_cents": data["amount"]["payable_amount_cents"],
            "paid_amount_cents": data["amount"]["paid_amount_cents"],
            "refunded_amount_cents": data["amount"]["refunded_amount_cents"],
            "currency": data["currency"],
            "allow_payment": data["status"] == "PENDING_PAYMENT",
        }, trace_id=request.state.trace_id)

    @router.get("/orders/{order_no}/status")
    async def order_status(order_no: str, request: Request, session: AsyncSession = Depends(session_dep)):
        data = await order_service.get_order(session, order_no)
        return success({"order_no": order_no, "status": data["status"], "status_text": data["status_text"]},
                       trace_id=request.state.trace_id)

    return router