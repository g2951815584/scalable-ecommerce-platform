"""Payment service: initiate, callback settlement, refund and ledger."""

from __future__ import annotations

from datetime import timedelta

from common.clock import utc_now
from common.errors import AppError
from common.ids import next_id
from common.outbox import make_outbox_event
from common.response import ErrorDetail
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Payment, PaymentTransaction, Refund


def _payment_no() -> str:
    return f"PA{utc_now().strftime('%Y%m%d')}{next_id() % 10000000000:010d}"


def _refund_no() -> str:
    return f"RF{utc_now().strftime('%Y%m%d')}{next_id() % 10000000000:010d}"


def _txn_no() -> str:
    return f"TX{utc_now().strftime('%Y%m%d')}{next_id() % 10000000000:010d}"


async def _get_payment_by_no(session: AsyncSession, payment_no: str) -> Payment | None:
    return (await session.execute(
        select(Payment).where(Payment.payment_no == payment_no))).scalar_one_or_none()


async def _get_payment_by_order_channel(session: AsyncSession, order_no: str, channel: str) -> Payment | None:
    return (await session.execute(
        select(Payment).where(Payment.order_no == order_no, Payment.channel == channel,
                              Payment.status.in_(["PENDING", "PROCESSING"]))
    )).scalar_one_or_none()


async def _add_txn(session: AsyncSession, *, transaction_type: str, payment_no: str,
                   order_no: str, user_id: int, channel: str, direction: str,
                   amount_cents: int, third_party_id: str | None = None,
                   refund_no: str | None = None) -> None:
    session.add(PaymentTransaction(
        id=next_id(), transaction_no=_txn_no(), transaction_type=transaction_type,
        payment_no=payment_no, refund_no=refund_no, order_no=order_no, user_id=user_id,
        channel=channel, direction=direction, amount_cents=amount_cents,
        third_party_transaction_id=third_party_id, transaction_at=utc_now()))


async def create_payment(session: AsyncSession, *, order_no: str, user_id: int, channel: str,
                         amount_cents: int, currency: str = "CNY",
                         idempotency_key: str | None = None, expires_at=None) -> dict:
    existing = await _get_payment_by_order_channel(session, order_no, channel)
    if existing is not None:
        return {"payment_no": existing.payment_no, "status": existing.status,
                "idempotent_replay": True, "amount_cents": existing.amount_cents}

    payment = Payment(
        id=next_id(), payment_no=_payment_no(), order_no=order_no, user_id=user_id,
        channel=channel, status="PENDING", amount_cents=amount_cents, currency=currency,
        idempotency_key=idempotency_key or f"pay:{order_no}:{channel}",
        expires_at=expires_at or (utc_now() + timedelta(minutes=35)),
    )
    session.add(payment)
    await session.commit()
    return {"payment_no": payment.payment_no, "status": "PENDING",
            "amount_cents": payment.amount_cents, "currency": currency,
            "idempotent_replay": False}


async def settle_paid(session: AsyncSession, *, payment_no: str, third_party_payment_id: str,
                      paid_at, event_id: str | None = None) -> dict:
    payment = await _get_payment_by_no(session, payment_no)
    if payment is None:
        raise AppError("PAY-4002", "支付单不存在", 404)
    if payment.status == "SUCCEEDED":
        return {"payment_no": payment_no, "status": "SUCCEEDED", "idempotent_replay": True}

    rows = (await session.execute(
        update(Payment)
        .where(Payment.payment_no == payment_no, Payment.status.in_(["PENDING", "PROCESSING"]),
               Payment.version == payment.version)
        .values(status="SUCCEEDED", third_party_payment_id=third_party_payment_id,
                paid_at=paid_at, version=Payment.version + 1)
    )).rowcount
    if rows == 0:
        return {"payment_no": payment_no, "status": payment.status, "idempotent_replay": True}

    payment.status = "SUCCEEDED"
    await _add_txn(session, transaction_type="PAYMENT", payment_no=payment_no,
                   order_no=payment.order_no, user_id=payment.user_id, channel=payment.channel,
                   direction="IN", amount_cents=payment.amount_cents,
                   third_party_id=third_party_payment_id)
    session.add(make_outbox_event(
        event_type="payment.succeeded", aggregate_type="PAYMENT", aggregate_id=payment_no,
        payload={"payment_no": payment_no, "order_no": payment.order_no,
                 "user_id": str(payment.user_id), "amount_cents": payment.amount_cents,
                 "currency": payment.currency, "channel": payment.channel,
                 "third_party_payment_id": third_party_payment_id,
                 "paid_at": paid_at.isoformat() if hasattr(paid_at, "isoformat") else str(paid_at)}))
    await session.commit()
    return {"payment_no": payment_no, "status": "SUCCEEDED", "idempotent_replay": False}


async def create_refund(session: AsyncSession, *, payment_no: str, order_no: str, user_id: int,
                        channel: str, amount_cents: int, reason: str,
                        idempotency_key: str) -> dict:
    payment = await _get_payment_by_no(session, payment_no)
    if payment is None or payment.status != "SUCCEEDED":
        raise AppError("PAY-5002", "该支付单当前状态不支持退款", 409)

    reserved = (await session.execute(
        update(Payment)
        .where(Payment.payment_no == payment_no,
               Payment.refunded_amount_cents + amount_cents <= Payment.amount_cents)
        .values(refunded_amount_cents=Payment.refunded_amount_cents + amount_cents,
                version=Payment.version + 1)
    )).rowcount
    if reserved == 0:
        refundable = payment.amount_cents - payment.refunded_amount_cents
        raise AppError("PAY-5007", "退款金额超过可退金额", 409,
                       details=[ErrorDetail(field="amount_cents", reason=f"当前可退金额 {refundable} 分")])

    refund_type = "FULL" if amount_cents == payment.amount_cents else "PARTIAL"
    refund = Refund(
        id=next_id(), refund_no=_refund_no(), payment_no=payment_no, order_no=order_no,
        user_id=user_id, channel=channel, refund_type=refund_type, amount_cents=amount_cents,
        currency=payment.currency, payment_amount_cents=payment.amount_cents,
        status="SUCCEEDED", reason=reason, idempotency_key=idempotency_key, refunded_at=utc_now())
    session.add(refund)
    await _add_txn(session, transaction_type="REFUND", payment_no=payment_no, refund_no=refund.refund_no,
                   order_no=order_no, user_id=user_id, channel=channel, direction="OUT",
                   amount_cents=amount_cents)

    await session.refresh(payment)
    session.add(make_outbox_event(
        event_type="payment.refunded", aggregate_type="PAYMENT", aggregate_id=payment_no,
        payload={"refund_no": refund.refund_no, "payment_no": payment_no, "order_no": order_no,
                 "user_id": str(user_id), "amount_cents": amount_cents, "currency": payment.currency,
                 "channel": channel, "refund_type": refund_type,
                 "payment_total_amount_cents": payment.amount_cents,
                 "total_refunded_amount_cents": payment.refunded_amount_cents,
                 "refunded_at": utc_now().isoformat()}))
    await session.commit()
    return {"refund_no": refund.refund_no, "payment_no": payment_no, "order_no": order_no,
            "refund_type": refund_type, "amount_cents": amount_cents, "status": "SUCCEEDED"}


async def get_payment(session: AsyncSession, payment_no: str) -> dict:
    payment = await _get_payment_by_no(session, payment_no)
    if payment is None:
        raise AppError("PAY-4002", "支付单不存在", 404)
    return {
        "payment_no": payment.payment_no, "order_no": payment.order_no,
        "user_id": str(payment.user_id), "channel": payment.channel,
        "status": payment.status, "amount_cents": payment.amount_cents,
        "currency": payment.currency, "refunded_amount_cents": payment.refunded_amount_cents,
        "refundable_amount_cents": payment.amount_cents - payment.refunded_amount_cents,
        "third_party_payment_id": payment.third_party_payment_id,
        "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
    }


async def by_order(session: AsyncSession, order_no: str) -> dict:
    payments = list((await session.execute(
        select(Payment).where(Payment.order_no == order_no).order_by(Payment.created_at.desc())
    )).scalars().all())
    succeeded = [p for p in payments if p.status == "SUCCEEDED"]
    total_paid = sum(p.amount_cents for p in succeeded)
    total_refunded = sum(p.refunded_amount_cents for p in succeeded)
    latest = payments[0] if payments else None
    return {
        "order_no": order_no,
        "has_succeeded_payment": bool(succeeded),
        "total_paid_cents": total_paid,
        "total_refunded_cents": total_refunded,
        "net_paid_cents": total_paid - total_refunded,
        "currency": "CNY",
        "latest_payment": {
            "payment_no": latest.payment_no, "channel": latest.channel, "status": latest.status,
            "amount_cents": latest.amount_cents,
            "paid_at": latest.paid_at.isoformat() if latest.paid_at else None,
        } if latest else None,
    }