"""Core unit tests for order-service (no external dependencies)."""

from app.services.order_service import _TRANSITIONS, calc_shipping_fee


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