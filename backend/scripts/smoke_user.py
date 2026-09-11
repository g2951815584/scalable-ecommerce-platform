import asyncio
import time

from app.main import app
from httpx import ASGITransport, AsyncClient


async def main() -> None:
    email = f"alice-{int(time.time())}@example.com"
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.post(
                "/api/v1/auth/register",
                json={"email": email, "password": "Str0ngPass!2026", "nickname": "Alice"},
            )
            b = r.json()
            print("register:", r.status_code, b.get("code"), "user_id=", (b.get("data") or {}).get("user_id"))

            r2 = await c.post(
                "/api/v1/auth/login",
                json={"account": email, "password": "Str0ngPass!2026"},
            )
            b2 = r2.json()
            data2 = b2.get("data") or {}
            print("login:", r2.status_code, b2.get("code"), "has_token=", bool(data2.get("access_token")))

            uid = data2.get("user", {}).get("user_id")
            r3 = await c.get("/api/v1/users/me", headers={"X-User-Id": str(uid)})
            print("me:", r3.status_code, r3.json().get("code"), (r3.json().get("data") or {}).get("nickname"))

            r4 = await c.post(
                "/api/v1/users/me/addresses",
                headers={"X-User-Id": str(uid)},
                json={"receiver_name": "张三", "receiver_phone": "+8613800138000",
                      "province": "广东省", "city": "深圳市", "district": "南山区",
                      "detail_address": "科技园南路 1 号 A 座 1801", "is_default": True},
            )
            print("address:", r4.status_code, r4.json().get("code"), (r4.json().get("data") or {}).get("address_id"))


asyncio.run(main())