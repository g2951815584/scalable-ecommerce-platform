import asyncio

from app.main import app
from app.services import payment_service
from common.clock import utc_now


async def main() -> None:
    async with app.router.lifespan_context(app):
        sf = app.state.session_factory

        async with sf() as s:
            p = await payment_service.create_payment(
                s, order_no="SO_TEST_PAY", user_id=1024, channel="STRIPE", amount_cents=19900)
            payment_no = p["payment_no"]
            print("create:", p["status"], "payment_no=", payment_no)

        async with sf() as s:
            r = await payment_service.settle_paid(
                s, payment_no=payment_no, third_party_payment_id="pi_123", paid_at=utc_now())
            print("settle:", r["status"], "replay=", r["idempotent_replay"])

        # 重复回调幂等
        async with sf() as s:
            r = await payment_service.settle_paid(
                s, payment_no=payment_no, third_party_payment_id="pi_123", paid_at=utc_now())
            print("settle-dup:", r["status"], "replay=", r["idempotent_replay"])

        async with sf() as s:
            d = await payment_service.get_payment(s, payment_no)
            print("get:", d["status"], "refundable=", d["refundable_amount_cents"])

        async with sf() as s:
            r = await payment_service.create_refund(
                s, payment_no=payment_no, order_no="SO_TEST_PAY", user_id=1024,
                channel="STRIPE", amount_cents=5000, reason="部分退款", idempotency_key="rk1")
            print("refund:", r["refund_type"], r["amount_cents"])

        # 超额退款应被拒
        async with sf() as s:
            try:
                await payment_service.create_refund(
                    s, payment_no=payment_no, order_no="SO_TEST_PAY", user_id=1024,
                    channel="STRIPE", amount_cents=15000, reason="超额", idempotency_key="rk2")
                print("refund-over: 未拦截(错)")
            except Exception as e:
                print("refund-over rejected:", getattr(e, "code", type(e).__name__))

        async with sf() as s:
            d = await payment_service.by_order(s, "SO_TEST_PAY")
            print("by-order:", d["has_succeeded_payment"], "net=", d["net_paid_cents"])


asyncio.run(main())