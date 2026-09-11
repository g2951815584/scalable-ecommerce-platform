"""Payment routes under /api/v1/payments."""

from common.response import success
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_user_id, session_dep
from app.services import payment_service


def build_router() -> APIRouter:
    router = APIRouter()

    @router.post("/payments", status_code=201)
    async def create_payment(payload: dict, request: Request, uid: int = Depends(current_user_id),
                             session: AsyncSession = Depends(session_dep)):
        result = await payment_service.create_payment(
            session, order_no=payload["order_no"], user_id=uid,
            channel=payload.get("channel", "STRIPE"),
            amount_cents=int(payload.get("amount_cents", 0)),
            idempotency_key=request.headers.get("Idempotency-Key"))
        return success(result, trace_id=request.state.trace_id)

    @router.get("/payments/{payment_no}")
    async def get_payment(payment_no: str, request: Request, session: AsyncSession = Depends(session_dep)):
        return success(await payment_service.get_payment(session, payment_no), trace_id=request.state.trace_id)

    @router.post("/payments/{payment_no}/refunds", status_code=201)
    async def create_refund(payment_no: str, payload: dict, request: Request,
                            uid: int = Depends(current_user_id), session: AsyncSession = Depends(session_dep)):
        payment = await payment_service.get_payment(session, payment_no)
        result = await payment_service.create_refund(
            session, payment_no=payment_no, order_no=payment["order_no"], user_id=uid,
            channel=payment["channel"], amount_cents=int(payload["amount_cents"]),
            reason=payload.get("reason", "退款"), idempotency_key=request.headers.get("Idempotency-Key", ""))
        return success(result, trace_id=request.state.trace_id)

    @router.post("/payments/{channel}/webhook")
    async def webhook(channel: str, payload: dict, request: Request, session: AsyncSession = Depends(session_dep)):
        from common.clock import utc_now

        payment_no = payload.get("payment_no") or payload.get("metadata", {}).get("payment_no")
        third_party_id = payload.get("third_party_payment_id") or payload.get("id", "")
        result = await payment_service.settle_paid(
            session, payment_no=payment_no, third_party_payment_id=third_party_id, paid_at=utc_now())
        return success(result, trace_id=request.state.trace_id)

    return router