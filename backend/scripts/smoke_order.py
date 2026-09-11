import asyncio

from app.main import app
from app.services import order_service


async def main() -> None:
    async with app.router.lifespan_context(app):
        session_factory = app.state.session_factory

        # 1. 创建订单
        async with session_factory() as session:
            created = await order_service.create_order(
                session, user_id=1024,
                items=[{"sku_id": "3001", "quantity": 2, "unit_price_cents": 9900,
                        "title": "纯棉T恤", "spec_name": "黑色/M"}],
                address={"receiver_name": "张三", "receiver_phone": "+8613800138000",
                         "province": "广东", "city": "深圳", "district": "南山",
                         "detail_address": "科技园1号", "address_text": "广东深圳南山科技园1号"})
            order_no = created["order_no"]
            print("create:", created["status"], "payable=", created["payable_amount_cents"])

        # 2. 详情
        async with session_factory() as session:
            detail = await order_service.get_order(session, order_no)
            print("detail:", detail["status_text"], "items=", len(detail["items"]))

        # 3. 取消
        async with session_factory() as session:
            await order_service.cancel(session, order_no, 1024, "不想买了")
            print("cancel done")

        # 4. 再创建 + 支付 + 发货 + 收货
        async with session_factory() as session:
            created2 = await order_service.create_order(
                session, user_id=1024,
                items=[{"sku_id": "3002", "quantity": 1, "unit_price_cents": 8900,
                        "title": "马克杯", "spec_name": "雾白"}])
            order2 = created2["order_no"]

        async with session_factory() as session:
            await order_service.handle_payment_succeeded(session, "PA1", order2, 8900, "2026-09-10T08:35:00Z")
            print("paid done")

        async with session_factory() as session:
            d = await order_service.get_order(session, order2)
            print("after-pay status:", d["status"])

        async with session_factory() as session:
            await order_service.ship(session, order2, "SF", "SF1234567890")
            await order_service.confirm_receipt(session, order2, 1024)
            d = await order_service.get_order(session, order2)
            print("after-ship+confirm status:", d["status"])


asyncio.run(main())