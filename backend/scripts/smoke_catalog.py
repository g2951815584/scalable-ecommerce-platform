import asyncio
import time

from app.main import app
from httpx import ASGITransport, AsyncClient


async def main() -> None:
    suffix = int(time.time()) % 100000
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            hdr = {"X-Internal-Token": "change-me"}

            r = await c.post("/api/v1/admin/categories", headers={"X-User-Roles": "ADMIN"},
                             json={"name": "数码 3C", "slug": f"digital-{suffix}", "sort_order": 1})
            cat = (r.json().get("data") or {})
            print("category:", r.status_code, cat.get("id"))

            r = await c.post("/api/v1/admin/products", headers={"X-User-Roles": "ADMIN"},
                             json={"category_id": cat.get("id"), "title": "降噪耳机 Pro", "brand": "Acme",
                                   "skus": [{"sku_code": f"ACME-{suffix}", "spec_text": "颜色:黑色",
                                             "price_cents": 29900, "initial_stock": 5}]})
            prod = (r.json().get("data") or {})
            spu_id = prod.get("id")
            sku_id = (prod.get("skus") or [{}])[0].get("id")
            print("product:", r.status_code, "spu=", spu_id, "sku=", sku_id)

            await c.post(f"/api/v1/admin/products/{spu_id}/publish", headers={"X-User-Roles": "ADMIN"})

            r = await c.get(f"/api/v1/products/{spu_id}")
            detail = (r.json().get("data") or {})
            print("detail:", r.status_code, detail.get("title"), "available=", (detail.get("skus") or [{}])[0].get("available"))

            order_no = "SO_TEST_0001"
            r = await c.post("/internal/v1/inventory/reserve", headers=hdr,
                             json={"order_no": order_no, "items": [{"sku_id": sku_id, "quantity": 3}]})
            print("reserve:", r.status_code, (r.json().get("data") or {}).get("items"))

            r = await c.post("/internal/v1/inventory/reserve", headers=hdr,
                             json={"order_no": order_no, "items": [{"sku_id": sku_id, "quantity": 5}]})
            print("reserve-overstock:", r.status_code, r.json().get("code"))

            r = await c.post("/internal/v1/inventory/confirm", headers=hdr,
                             json={"order_no": order_no, "items": [{"sku_id": sku_id, "quantity": 3}]})
            print("confirm:", r.status_code, (r.json().get("data") or {}).get("confirmed"))

            r = await c.post("/internal/v1/inventory/batch-query", headers=hdr, json={"sku_ids": [sku_id]})
            print("batch-query:", (r.json().get("data") or {}).get("items"))


asyncio.run(main())