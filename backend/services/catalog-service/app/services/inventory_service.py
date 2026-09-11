"""Three-phase inventory service: reserve, confirm, release.

Correctness lives in the database: conditional ``UPDATE ... WHERE stock - reserved
>= qty`` guards against overselling and the ``(order_no, sku_id)`` unique
constraint makes reserve idempotent.  Redis is an optimisation seam, never the
source of truth.
"""

from __future__ import annotations

from datetime import timedelta

from common.clock import utc_now
from common.errors import AppError
from common.ids import next_id
from common.response import ErrorDetail
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.inventory import Inventory, InventoryTransaction, StockReservation
from app.models.product import Sku, Spu


async def _get_inventory(session: AsyncSession, sku_id: int) -> Inventory | None:
    return (await session.execute(
        select(Inventory).where(Inventory.sku_id == sku_id)
    )).scalar_one_or_none()


async def _add_txn(session: AsyncSession, *, sku_id: int, txn_type: str, quantity: int,
                   inv: Inventory, reason: str | None = None, ref_type: str | None = None,
                   ref_no: str | None = None, event_id: str | None = None) -> None:
    session.add(
        InventoryTransaction(
            id=next_id(), sku_id=sku_id, txn_type=txn_type, quantity=quantity,
            stock_after=inv.stock, reserved_after=inv.reserved,
            available_after=inv.stock - inv.reserved, sold_after=inv.sold,
            reason=reason, ref_type=ref_type, ref_no=ref_no, event_id=event_id,
        )
    )


async def _find_reservation(session: AsyncSession, order_no: str, sku_id: int) -> StockReservation | None:
    return (await session.execute(
        select(StockReservation).where(
            StockReservation.order_no == order_no, StockReservation.sku_id == sku_id)
    )).scalar_one_or_none()


async def reserve(session: AsyncSession, *, order_no: str, items: list[dict], expires_at=None) -> dict:
    settings = get_settings()
    expiry = expires_at or (utc_now() + timedelta(seconds=settings.order_reserve_ttl_seconds))
    result_items = []

    for item in sorted(items, key=lambda i: int(i["sku_id"])):
        sku_id = int(item["sku_id"])
        quantity = int(item["quantity"])

        existing = await _find_reservation(session, order_no, sku_id)
        if existing is not None:
            result_items.append({"sku_id": str(sku_id), "quantity": existing.quantity,
                                 "status": existing.status})
            continue

        inv = await _get_inventory(session, sku_id)
        if inv is None:
            raise AppError("CAT-4006", "商品规格不存在", 404)

        rows = (await session.execute(
            update(Inventory)
            .where(Inventory.sku_id == sku_id, Inventory.stock - Inventory.reserved >= quantity)
            .values(reserved=Inventory.reserved + quantity, version=Inventory.version + 1)
        )).rowcount
        if rows == 0:
            available = inv.stock - inv.reserved
            raise AppError(
                "CAT-5002", "库存不足，无法下单", 409,
                details=[ErrorDetail(field=f"items[{sku_id}].sku_id",
                                     reason=f"可售库存不足，当前可售 {available} 件，需 {quantity} 件")],
            )

        await session.refresh(inv)
        session.add(StockReservation(
            id=next_id(), order_no=order_no, sku_id=sku_id, quantity=quantity,
            status="RESERVED", expires_at=expiry,
        ))
        await _add_txn(session, sku_id=sku_id, txn_type="RESERVE", quantity=quantity,
                       inv=inv, ref_type="ORDER", ref_no=order_no)
        result_items.append({"sku_id": str(sku_id), "quantity": quantity,
                             "reserved_after": inv.reserved,
                             "available_after": inv.stock - inv.reserved})

    await session.commit()
    return {"order_no": order_no, "items": result_items, "idempotent_replay": False}


async def confirm(session: AsyncSession, *, order_no: str, items: list[dict], event_id: str | None = None) -> dict:
    result_items = []
    for item in items:
        sku_id = int(item["sku_id"])
        quantity = int(item["quantity"])
        rows = (await session.execute(
            update(StockReservation)
            .where(StockReservation.order_no == order_no,
                   StockReservation.sku_id == sku_id,
                   StockReservation.status == "RESERVED")
            .values(status="CONFIRMED", confirmed_at=utc_now())
        )).rowcount

        if rows == 0:
            existing = await _find_reservation(session, order_no, sku_id)
            if existing is None:
                raise AppError("CAT-4008", "订单库存信息不存在", 404)
            if existing.status == "CONFIRMED":
                result_items.append({"sku_id": str(sku_id), "quantity": quantity, "status": "CONFIRMED"})
                continue
            raise AppError("CAT-5013", "支付成功但库存已释放，请人工处理", 409)

        inv = await _get_inventory(session, sku_id)
        await session.execute(
            update(Inventory)
            .where(Inventory.sku_id == sku_id)
            .values(reserved=Inventory.reserved - quantity, sold=Inventory.sold + quantity,
                    version=Inventory.version + 1)
        )
        await session.refresh(inv)
        await _add_txn(session, sku_id=sku_id, txn_type="CONFIRM", quantity=quantity,
                       inv=inv, ref_type="ORDER", ref_no=order_no, event_id=event_id)
        result_items.append({"sku_id": str(sku_id), "quantity": quantity, "status": "CONFIRMED",
                             "reserved_after": inv.reserved, "sold_after": inv.sold,
                             "available_after": inv.stock - inv.reserved})

    await session.commit()
    return {"order_no": order_no, "confirmed": result_items, "idempotent_replay": False}


async def release(session: AsyncSession, *, order_no: str, items: list[dict] | None = None,
                  reason: str | None = None, expired: bool = False) -> dict:
    target_status = "EXPIRED" if expired else "RELEASED"

    if items is None:
        rows = list((await session.execute(
            select(StockReservation).where(StockReservation.order_no == order_no,
                                           StockReservation.status == "RESERVED")
        )).scalars().all())
        items = [{"sku_id": str(r.sku_id), "quantity": r.quantity} for r in rows]

    result_items = []
    for item in items:
        sku_id = int(item["sku_id"])
        quantity = int(item["quantity"])
        rows = (await session.execute(
            update(StockReservation)
            .where(StockReservation.order_no == order_no,
                   StockReservation.sku_id == sku_id,
                   StockReservation.status == "RESERVED")
            .values(status=target_status, released_at=utc_now(), release_reason=reason)
        )).rowcount
        if rows == 0:
            existing = await _find_reservation(session, order_no, sku_id)
            if existing is None or existing.status in ("RELEASED", "EXPIRED"):
                continue
            raise AppError("CAT-5012", "订单已支付，无法释放库存", 409)

        inv = await _get_inventory(session, sku_id)
        await session.execute(
            update(Inventory)
            .where(Inventory.sku_id == sku_id)
            .values(reserved=Inventory.reserved - quantity, version=Inventory.version + 1)
        )
        await session.refresh(inv)
        await _add_txn(session, sku_id=sku_id, txn_type="RELEASE", quantity=-quantity,
                       inv=inv, reason=reason or "RELEASE", ref_type="ORDER", ref_no=order_no)
        result_items.append({"sku_id": str(sku_id), "quantity": quantity, "status": target_status,
                             "reserved_after": inv.reserved,
                             "available_after": inv.stock - inv.reserved})

    await session.commit()
    return {"order_no": order_no, "released": result_items, "skipped": [], "idempotent_replay": False}


async def batch_query(session: AsyncSession, sku_ids: list[int]) -> dict:
    items = []
    for sku_id in sku_ids:
        inv = await _get_inventory(session, sku_id)
        sku = await session.get(Sku, sku_id)
        if inv is None or sku is None:
            items.append({"sku_id": str(sku_id), "available": 0, "is_sellable": False})
            continue
        spu = await session.get(Spu, sku.spu_id)
        is_sellable = (spu is not None and spu.status == "ON_SALE" and sku.status == "ENABLED"
                       and inv.stock - inv.reserved > 0)
        items.append({
            "sku_id": str(sku_id), "available": inv.stock - inv.reserved,
            "price_cents": sku.price_cents, "currency": sku.currency,
            "spu_status": spu.status if spu else None, "sku_status": sku.status,
            "is_sellable": is_sellable,
        })
    return {"items": items, "queried_at": utc_now().isoformat()}