import asyncio

from app.main import app
from app.services import notification_service
from app.services.renderer import render


async def main() -> None:
    # 渲染器单元验证
    assert render("订单 {{order_no}} 已创建", {"order_no": "SO1"}) == "订单 SO1 已创建"
    assert render("你好 {{nickname|default:顾客}}", {}) == "你好 顾客"
    print("renderer: OK")

    async with app.router.lifespan_context(app):
        sf = app.state.session_factory
        settings = app.state.settings

        r = await notification_service.dispatch_event(sf, {
            "event_id": "e-created-1", "event_type": "order.created",
            "payload": {"order_no": "SO1001", "user_id": "1024", "email": "buyer@example.com",
                        "total_amount_cents": 19900, "expires_at": "2026-09-10T09:00:00Z"}}, settings)
        print("order.created:", r["status"])

        r = await notification_service.dispatch_event(sf, {
            "event_id": "e-shipped-1", "event_type": "order.shipped",
            "payload": {"order_no": "SO1001", "user_id": "1024", "email": "buyer@example.com",
                        "carrier": "顺丰速运", "tracking_no": "SF1234567890"}}, settings)
        print("order.shipped:", r["status"])

        r = await notification_service.dispatch_event(sf, {
            "event_id": "e-stock-1", "event_type": "stock.low",
            "payload": {"spu_title": "降噪耳机", "spec_name": "黑色", "available": 3,
                        "threshold": 20, "sku_id": "2002"}}, settings)
        print("stock.low:", r["status"])

        # 幂等
        r = await notification_service.dispatch_event(sf, {
            "event_id": "e-created-1", "event_type": "order.created",
            "payload": {"order_no": "SO1001", "user_id": "1024", "email": "buyer@example.com",
                        "total_amount_cents": 19900, "expires_at": "2026-09-10T09:00:00Z"}}, settings)
        print("dup order.created:", r["status"])


asyncio.run(main())