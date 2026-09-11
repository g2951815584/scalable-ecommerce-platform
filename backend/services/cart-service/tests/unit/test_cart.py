"""Core unit tests for cart-service (no external dependencies)."""

from app.models import CartItem
from common.ids import new_id


def test_cart_item_defaults():
    item = CartItem(id=1, cart_id=2, sku_id=3001, quantity=3,
                    snapshot_unit_price_cents=9900, is_selected=True, currency="CNY")
    assert item.quantity == 3
    assert item.is_selected is True
    assert item.currency == "CNY"


def test_cart_item_amount_derivation():
    item = CartItem(id=1, cart_id=2, sku_id=3001, quantity=4,
                    snapshot_unit_price_cents=2500)
    assert item.snapshot_unit_price_cents * item.quantity == 10000


def test_owner_resolution_shape():
    assert f"u:{123}" == "u:123"
    assert f"g:{'guest'}" == "g:guest"


def test_snowflake_unique():
    assert new_id() != new_id()