"""Order service: state machine, checkout saga and amount calculation."""

from __future__ import annotations

import hashlib
import json
from datetime import timedelta

from common.clock import utc_now
from common.errors import AppError
from common.ids import next_id
from common.outbox import make_outbox_event
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients import catalog_client
from app.core.config import get_settings
from app.models.order import Order, OrderItem, OrderShippingSnapshot, OrderStatusLog

_STATUS_TEXT = {
    "PENDING_PAYMENT": "待支付", "CLOSING": "已关闭", "PAID": "待发货",
    "SHIPPED": "待收货", "RECEIVED": "已收货", "COMPLETED": "已完成",
    "CANCELLED": "已取消", "CLOSED": "已关闭", "REFUNDING": "退款中", "REFUNDED": "已退款",
}

_TRANSITIONS = {
    "PAYMENT_SUCCEEDED": ({"PENDING_PAYMENT", "CLOSING"}, "PAID"),
    "BUYER_CANCEL": ({"PENDING_PAYMENT"}, "CANCELLED"),
    "TIMEOUT_CLOSE": ({"PENDING_PAYMENT"}, "CLOSING"),
    "CLOSE_RELEASED": ({"CLOSING"}, "CLOSED"),
    "SHIP": ({"PAID"}, "SHIPPED"),
    "BUYER_CONFIRM": ({"SHIPPED"}, "RECEIVED"),
    "AUTO_COMPLETE": ({"RECEIVED"}, "COMPLETED"),
    "REFUND_APPROVED": ({"PAID", "SHIPPED", "RECEIVED", "COMPLETED"}, "REFUNDING"),
    "REFUND_SUCCEEDED": ({"REFUNDING"}, "REFUNDED"),
}


def _order_no() -> str:
    return f"SO{utc_now().strftime('%Y%m%d')}{next_id() % 1000000:06d}"


def calc_shipping_fee(goods_amount_cents: int) -> int:
    s = get_settings()
    if goods_amount_cents >= s.free_shipping_threshold_cents:
        return 0
    return s.shipping_base_fee_cents


async def transition(session: AsyncSession, order_no: str, action: str,
                     operator_type: str = "SYSTEM", operator_id: int | None = None,
                     reason: str | None = None, extra: dict | None = None) -> Order | None:
    if action not in _TRANSITIONS:
        raise AppError("ORD-8003", "非法状态流转", 500)
    from_statuses, to_status = _TRANSITIONS[action]

    row = (await session.execute(
        select(Order).where(Order.order_no == order_no).with_for_update()
    )).scalar_one_or_none()
    if row is None or row.status not in from_statuses:
        return None

    sets = {"status": to_status, "version": Order.version + 1}
    if extra:
        sets.update(extra)
    await session.execute(
        update(Order).where(Order.order_no == order_no, Order.status == row.status,
                            Order.version == row.version).values(**sets)
    )
    session.add(OrderStatusLog(
        id=next_id(), order_no=order_no, from_status=row.status, to_status=to_status,
        action=action, operator_type=operator_type, operator_id=operator_id, reason=reason))
    row.status = to_status
    return row


async def _log(session: AsyncSession, order_no: str, action: str,
               status: str, reason: str | None = None) -> None:
    session.add(OrderStatusLog(
        id=next_id(), order_no=order_no, from_status=status, to_status=status,
        action=action, operator_type="SYSTEM", reason=reason))


async def create_order(session: AsyncSession, *, user_id: int, items: list[dict],
                       address: dict | None = None, idempotency_key: str | None = None,
                       source: str = "WEB") -> dict:
    settings = get_settings()
    goods = sum(int(i["unit_price_cents"]) * int(i["quantity"]) for i in items)
    shipping = calc_shipping_fee(goods)
    payable = goods + shipping

    order_no = _order_no()

    # Saga step 1: reserve inventory before persisting the order. The catalogue
    # reserve is atomic (all-or-nothing); any failure raises ORD-5001/ORD-7002
    # here and needs no order-side compensation because nothing was reserved.
    await catalog_client.reserve_stock(order_no, items, settings.internal_token)

    order = Order(
        id=next_id(), order_no=order_no, user_id=user_id, status="PENDING_PAYMENT",
        goods_amount_cents=goods, shipping_fee_cents=shipping, payable_amount_cents=payable,
        item_kind_count=len(items),
        total_quantity=sum(int(i["quantity"]) for i in items),
        idempotency_key=idempotency_key,
        idempotency_fingerprint=hashlib.sha256(
            json.dumps(items, sort_keys=True).encode()).hexdigest() if idempotency_key else None,
        price_breakdown={"pricing_version": "v1"},
        source=source,
        expires_at=utc_now() + timedelta(minutes=settings.payment_timeout_minutes),
    )

    try:
        session.add(order)
        await session.flush()

        for idx, item in enumerate(items, start=1):
            qty = int(item["quantity"])
            price = int(item["unit_price_cents"])
            session.add(OrderItem(
                id=next_id(), order_id=order.id, order_no=order_no, user_id=user_id, item_no=idx,
                spu_id=int(item.get("spu_id", 0)), sku_id=int(item["sku_id"]),
                spu_title=item.get("title", ""), sku_spec_text=item.get("spec_name", ""),
                sku_image_url=item.get("image_url"), unit_price_cents=price, quantity=qty,
                item_amount_cents=price * qty))

        if address:
            session.add(OrderShippingSnapshot(
                id=next_id(), order_no=order_no, user_id=user_id,
                address_id=int(address.get("address_id", 0) or 0),
                receiver_name=address.get("receiver_name", ""),
                receiver_phone=address.get("receiver_phone", ""),
                province=address.get("province", ""), city=address.get("city", ""),
                district=address.get("district", ""),
                detail_address=address.get("detail_address", ""),
                postal_code=address.get("postal_code"),
                address_text=address.get("address_text", "")))

        session.add(OrderStatusLog(
            id=next_id(), order_no=order_no, from_status=None, to_status="PENDING_PAYMENT",
            action="CREATE", operator_type="SYSTEM"))
        session.add(make_outbox_event(
            event_type="order.created", aggregate_type="ORDER", aggregate_id=order_no,
            payload={"order_no": order_no, "user_id": str(user_id), "total_amount_cents": payable,
                     "currency": "CNY", "expires_at": order.expires_at.isoformat(),
                     "items": [{"sku_id": str(item["sku_id"]), "quantity": int(item["quantity"])}
                               for item in items]}))

        await session.commit()
    except Exception:
        # Saga compensation: release the reservation we took above.
        await session.rollback()
        await catalog_client.release_stock(order_no, settings.internal_token)
        raise AppError("ORD-8001", "下单失败，请稍后重试", 500)

    return {
        "order_no": order_no, "status": "PENDING_PAYMENT", "status_text": "待支付",
        "payable_amount_cents": payable, "currency": "CNY",
        "expires_at": order.expires_at.isoformat(),
    }


async def get_order(session: AsyncSession, order_no: str) -> dict:
    order = (await session.execute(select(Order).where(Order.order_no == order_no))).scalar_one_or_none()
    if order is None:
        raise AppError("ORD-4001", "订单不存在", 404)
    items = list((await session.execute(
        select(OrderItem).where(OrderItem.order_no == order_no).order_by(OrderItem.item_no)
    )).scalars().all())
    return {
        "order_no": order.order_no, "status": order.status, "status_text": _STATUS_TEXT.get(order.status, order.status),
        "currency": order.currency, "created_at": order.created_at.isoformat(),
        "expires_at": order.expires_at.isoformat(), "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        "amount": {"goods_amount_cents": order.goods_amount_cents, "shipping_fee_cents": order.shipping_fee_cents,
                   "discount_amount_cents": order.discount_amount_cents,
                   "adjust_amount_cents": order.adjust_amount_cents,
                   "payable_amount_cents": order.payable_amount_cents,
                   "paid_amount_cents": order.paid_amount_cents,
                   "refunded_amount_cents": order.refunded_amount_cents},
        "items": [{"item_no": i.item_no, "spu_id": str(i.spu_id), "sku_id": str(i.sku_id),
                   "spu_title": i.spu_title, "sku_spec_text": i.sku_spec_text,
                   "unit_price_cents": i.unit_price_cents, "quantity": i.quantity,
                   "item_amount_cents": i.item_amount_cents} for i in items],
    }


async def list_orders(session: AsyncSession, user_id: int, status: str | None = None,
                      page: int = 1, page_size: int = 20) -> dict:
    from sqlalchemy import func as sqlfunc

    stmt = select(Order).where(Order.user_id == user_id)
    if status:
        stmt = stmt.where(Order.status == status)
    else:
        stmt = stmt.where(Order.status != "CLOSING")
    total = int((await session.execute(
        select(sqlfunc.count()).select_from(Order).where(*stmt.whereclause))).scalar_one())
    orders = list((await session.execute(
        stmt.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )).scalars().all())
    items = [{"order_no": o.order_no, "status": o.status, "status_text": _STATUS_TEXT.get(o.status, o.status),
              "payable_amount_cents": o.payable_amount_cents, "currency": o.currency,
              "item_kind_count": o.item_kind_count, "total_quantity": o.total_quantity,
              "created_at": o.created_at.isoformat(), "expires_at": o.expires_at.isoformat()} for o in orders]
    return {"items": items, "pagination": {"page": page, "page_size": page_size, "total": total,
                                          "total_pages": max(1, (total + page_size - 1) // page_size)}}


async def cancel(session: AsyncSession, order_no: str, user_id: int, reason: str) -> dict:
    order = await transition(session, order_no, "BUYER_CANCEL", operator_type="BUYER",
                             operator_id=user_id, reason=reason,
                             extra={"cancelled_at": utc_now(), "cancel_reason": reason})
    if order is None:
        raise AppError("ORD-5006", "当前订单状态不允许取消", 409)

    # Release the reserved stock via the outbox (catalog-service consumes it).
    order_items = list((await session.execute(
        select(OrderItem).where(OrderItem.order_no == order_no))).scalars().all())
    session.add(make_outbox_event(
        event_type="order.cancelled", aggregate_type="ORDER", aggregate_id=order_no,
        payload={"order_no": order_no, "user_id": str(order.user_id), "reason": "BUYER_CANCEL",
                 "final_status": "CANCELLED",
                 "items": [{"sku_id": str(i.sku_id), "quantity": i.quantity} for i in order_items]}))

    await session.commit()
    return {"order_no": order_no, "status": "CANCELLED", "status_text": "已取消"}


async def confirm_receipt(session: AsyncSession, order_no: str, user_id: int) -> dict:
    order = await transition(session, order_no, "BUYER_CONFIRM", operator_type="BUYER",
                             operator_id=user_id, extra={"received_at": utc_now()})
    if order is None:
        raise AppError("ORD-5007", "订单尚未发货，无法确认收货", 409)
    await session.commit()
    return {"order_no": order_no, "status": "RECEIVED"}


async def ship(session: AsyncSession, order_no: str, carrier: str, tracking_no: str) -> dict:
    now = utc_now()
    order = await transition(session, order_no, "SHIP", operator_type="ADMIN",
                             extra={"shipped_at": now, "stock_deduct_status": "DEDUCTED"})
    if order is None:
        raise AppError("ORD-5006", "当前订单状态不允许发货", 409)
    session.add(make_outbox_event(
        event_type="order.shipped", aggregate_type="ORDER", aggregate_id=order_no,
        payload={"order_no": order_no, "user_id": str(order.user_id), "carrier": carrier,
                 "tracking_no": tracking_no, "shipped_at": now.isoformat()}))
    await session.commit()
    return {"order_no": order_no, "status": "SHIPPED"}


async def handle_payment_succeeded(session: AsyncSession, payment_no: str, order_no: str,
                                   amount_cents: int, paid_at: str) -> None:
    order = (await session.execute(
        select(Order).where(Order.order_no == order_no))).scalar_one_or_none()
    if order is None:
        return
    if order.status in ("CANCELLED", "CLOSED", "REFUNDED"):
        return  # payment-after-close: handled by anomaly/refund flow (simplified)
    updated = await transition(session, order_no, "PAYMENT_SUCCEEDED", operator_type="EVENT",
                               extra={"paid_at": utc_now(), "paid_amount_cents": amount_cents,
                                      "stock_deduct_status": "DEDUCTED"})
    if updated is None and order.status == "PAID":
        return  # duplicate payment event
    order_items = list((await session.execute(
        select(OrderItem).where(OrderItem.order_no == order_no))).scalars().all())
    session.add(make_outbox_event(
        event_type="order.paid", aggregate_type="ORDER", aggregate_id=order_no,
        payload={"order_no": order_no, "user_id": str(order.user_id),
                 "payment_no": payment_no, "paid_amount_cents": amount_cents,
                 "currency": "CNY", "paid_at": paid_at,
                 "items": [{"sku_id": str(i.sku_id), "quantity": i.quantity} for i in order_items]}))
    await session.commit()