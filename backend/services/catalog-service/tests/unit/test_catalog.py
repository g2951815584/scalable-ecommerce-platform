"""Core unit tests for catalog-service (no external dependencies)."""

from app.models.inventory import Inventory


def test_inventory_available_is_derived():
    inv = Inventory(id=1, sku_id=100, stock=10, reserved=3, sold=1)
    assert inv.available == 7


def test_sku_price_range_uses_min_max():
    from app.models.product import Spu

    spu = Spu(id=1, category_id=2, title="商品", status="ON_SALE",
              min_price_cents=1000, max_price_cents=3000)
    assert spu.min_price_cents == 1000
    assert spu.max_price_cents == 3000
    assert spu.status == "ON_SALE"


def test_reservation_explicit_status():
    from app.models.inventory import StockReservation

    r = StockReservation(id=1, order_no="SO1", sku_id=9, quantity=2, status="RESERVED")
    assert r.status == "RESERVED"
    assert r.quantity == 2


def test_snowflake_ids():
    from common.ids import new_id

    assert new_id() != new_id()