"""Core unit tests for notification-service."""

from app.services.renderer import render


def test_render_plain_variable():
    assert render("订单 {{order_no}} 已创建", {"order_no": "SO1"}) == "订单 SO1 已创建"


def test_render_default_when_missing():
    assert render("你好 {{nickname|default:顾客}}", {}) == "你好 顾客"
    assert render("你好 {{nickname|default:顾客}}", {"nickname": "Alice"}) == "你好 Alice"


def test_render_no_injection_reparse():
    # A variable containing `{{` is emitted literally, never re-parsed.
    assert render("{{a}}", {"a": "{{b}}"}) == "{{b}}"


def test_template_mapping_keys():
    from app.services.notification_service import _EVENT_TEMPLATE

    assert _EVENT_TEMPLATE["order.created"] == ("ORDER_CREATED_EMAIL", "EMAIL")
    assert _EVENT_TEMPLATE["stock.low"] == ("OPS_STOCK_LOW_EMAIL", "EMAIL")