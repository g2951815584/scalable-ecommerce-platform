"""Core unit tests for order-service (no external dependencies)."""

import asyncio

import pytest
from app.services import order_service
from app.services.order_service import _TRANSITIONS, calc_shipping_fee
from common.errors import AppError


def test_shipping_fee_free_threshold():
    # 免邮阈值 9900 分（99 元）
    assert calc_shipping_fee(9900) == 0
    assert calc_shipping_fee(10000) == 0
    assert calc_shipping_fee(9899) == 800  # 基础运费 8 元


def test_transition_matrix_keys():
    assert _TRANSITIONS["PAYMENT_SUCCEEDED"][1] == "PAID"
    assert _TRANSITIONS["BUYER_CANCEL"][1] == "CANCELLED"
    assert _TRANSITIONS["SHIP"][1] == "SHIPPED"
    assert _TRANSITIONS["BUYER_CONFIRM"][1] == "RECEIVED"
    assert _TRANSITIONS["REFUND_SUCCEEDED"][1] == "REFUNDED"


def test_status_constants():
    from app.models.order import FINAL_STATUSES, ORDER_STATUSES

    assert "COMPLETED" in FINAL_STATUSES
    assert len(ORDER_STATUSES) == 10


class _FakeSession:
    """Minimal stand-in for AsyncSession used only by create_order's saga path."""

    def __init__(self, fail_commit: bool = False):
        self.fail_commit = fail_commit
        self.committed = False
        self.rolled_back = False

    def add(self, obj) -> None:
        return None

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        if self.fail_commit:
            raise RuntimeError("database down")
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True


_ITEMS = [{"sku_id": "3001", "quantity": 2, "unit_price_cents": 9900,
           "title": "纯棉T恤", "spec_name": "黑色", "image_url": ""}]


def test_create_order_raises_when_reserve_fails(monkeypatch):
    async def fail_reserve(order_no, items, token):
        raise AppError("ORD-5001", "库存不足", 409)

    monkeypatch.setattr(order_service.catalog_client, "reserve_stock", fail_reserve)

    with pytest.raises(AppError) as exc:
        asyncio.run(order_service.create_order(_FakeSession(), user_id=1, items=_ITEMS))
    assert exc.value.code == "ORD-5001"


def test_create_order_releases_on_commit_failure(monkeypatch):
    released: list[str] = []

    async def ok_reserve(order_no, items, token):
        return {"order_no": order_no}

    async def record_release(order_no, token):
        released.append(order_no)

    monkeypatch.setattr(order_service.catalog_client, "reserve_stock", ok_reserve)
    monkeypatch.setattr(order_service.catalog_client, "release_stock", record_release)
    session = _FakeSession(fail_commit=True)

    with pytest.raises(AppError) as exc:
        asyncio.run(order_service.create_order(session, user_id=1, items=_ITEMS))
    assert exc.value.code == "ORD-8001"
    assert len(released) == 1
    assert session.rolled_back is True