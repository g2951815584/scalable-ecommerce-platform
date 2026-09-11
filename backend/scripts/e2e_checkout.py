"""End-to-end checkout smoke test.

Run against a fully composed stack (services reachable on localhost:8001-8006;
see ``docker compose up``).  Validates the three-phase inventory saga end to
end: reserve on order placement, oversell protection, confirm on payment, and
release on cancellation.

Usage::

    python backend/scripts/e2e_checkout.py
"""

from __future__ import annotations

import time

import httpx

BASE = "http://localhost"
ADMIN = {"X-User-Roles": "ADMIN"}


def _get(url: str, headers: dict | None = None) -> dict:
    resp = httpx.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]


def _post(url: str, headers: dict | None = None, json: dict | None = None) -> httpx.Response:
    return httpx.post(url, headers=headers, json=json, timeout=10)


def _wait_until(predicate, timeout: float = 12.0, interval: float = 0.5) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False


def main() -> None:
    ts = int(time.time()) % 100000
    address = {
        "receiver_name": "张三",
        "receiver_phone": "+8613800138000",
        "province": "广东",
        "city": "深圳",
        "district": "南山",
        "detail_address": "科技园1号",
        "address_text": "广东深圳南山科技园1号",
    }

    # 1. Seed a category and an on-sale product with 5 units.
    cat = _post(
        f"{BASE}:8002/api/v1/admin/categories",
        headers=ADMIN,
        json={"name": "数码", "slug": f"digital-{ts}"},
    ).json()["data"]
    prod = _post(
        f"{BASE}:8002/api/v1/admin/products",
        headers=ADMIN,
        json={
            "category_id": cat["id"],
            "title": "降噪耳机 Pro",
            "skus": [{"sku_code": f"SKU-{ts}", "spec_text": "黑色", "price_cents": 29900, "initial_stock": 5}],
        },
    ).json()["data"]
    spu, sku = prod["id"], prod["skus"][0]["id"]
    _post(f"{BASE}:8002/api/v1/admin/products/{spu}/publish", headers=ADMIN)

    # 2. Register a buyer.
    buyer = _post(
        f"{BASE}:8001/api/v1/auth/register",
        json={"email": f"buyer-{ts}@example.com", "password": "Str0ngPass!2026"},
    ).json()["data"]
    buyer_h = {"X-User-Id": buyer["user_id"]}

    def available() -> int:
        return _get(f"{BASE}:8002/api/v1/products/{spu}")["skus"][0]["available"]

    initial = available()
    assert initial == 5, f"expected initial stock 5, got {initial}"

    # 3. Place an order for 3 -> reserved, available drops to 2 (synchronous).
    order_resp = _post(
        f"{BASE}:8004/api/v1/orders",
        headers={**buyer_h, "Idempotency-Key": f"e2e-{ts}-1"},
        json={
            "items": [{"sku_id": sku, "quantity": 3, "unit_price_cents": 29900,
                       "title": "降噪耳机 Pro", "spec_name": "黑色", "image_url": ""}],
            "address": address,
        },
    )
    assert order_resp.status_code == 201, order_resp.text
    order_no = order_resp.json()["data"]["order_no"]
    assert available() == 2, f"expected 2 available after reserve, got {available()}"
    print(f"[OK] reserve: available {initial} -> {available()}")

    # 4. Oversell protection: order 3 more while only 2 are available.
    over = _post(
        f"{BASE}:8004/api/v1/orders",
        headers={**buyer_h, "Idempotency-Key": f"e2e-{ts}-2"},
        json={
            "items": [{"sku_id": sku, "quantity": 3, "unit_price_cents": 29900,
                       "title": "降噪耳机 Pro", "spec_name": "黑色", "image_url": ""}],
            "address": address,
        },
    )
    assert over.status_code == 409 and over.json()["code"] == "ORD-5001", over.text
    print("[OK] oversell blocked: ORD-5001")

    # 5. Cancel the first order -> reserved released (async via order.cancelled).
    _post(f"{BASE}:8004/api/v1/orders/{order_no}/cancel", headers=buyer_h, json={"reason": "e2e"})
    released = _wait_until(lambda: available() == 5)
    assert released, f"expected available to return to 5, got {available()}"
    print("[OK] cancel release: available back to 5")

    # 6. Pay then confirm: reserve moves to sold, available returns to stock.
    order2_resp = _post(
        f"{BASE}:8004/api/v1/orders",
        headers={**buyer_h, "Idempotency-Key": f"e2e-{ts}-3"},
        json={
            "items": [{"sku_id": sku, "quantity": 2, "unit_price_cents": 29900,
                       "title": "降噪耳机 Pro", "spec_name": "黑色", "image_url": ""}],
            "address": address,
        },
    )
    order2 = order2_resp.json()["data"]["order_no"]
    assert available() == 3, f"expected 3 available after second reserve, got {available()}"

    pay = _post(
        f"{BASE}:8005/api/v1/payments",
        headers=buyer_h,
        json={"order_no": order2, "channel": "STRIPE", "amount_cents": 59800},
    ).json()["data"]
    _post(f"{BASE}:8005/api/v1/payments/stripe/webhook", json={
        "payment_no": pay["payment_no"], "third_party_payment_id": f"mock-{ts}",
    })

    paid = _wait_until(lambda: _get(f"{BASE}:8004/api/v1/orders/{order2}")["status"] == "PAID")
    confirmed = _wait_until(lambda: available() == 5)
    assert paid, "order did not reach PAID"
    assert confirmed, f"expected 5 available after confirm, got {available()}"
    print("[OK] pay -> confirm: order PAID, available back to 5 (sold=2)")

    print(f"\nE2E PASSED (order={order2})")


if __name__ == "__main__":
    main()