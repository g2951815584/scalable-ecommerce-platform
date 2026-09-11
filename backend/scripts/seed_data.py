"""Seed script for a freshly composed stack.

Creates demo users (one admin, one buyer), a category tree and on-sale products
so the storefront has something to browse and the admin console can log in.
Run after ``docker compose up``::

    python backend/scripts/seed_data.py
"""

from __future__ import annotations

import time

import httpx

BASE = "http://localhost"


def _post(url: str, headers: dict | None = None, json: dict | None = None) -> dict:
    resp = httpx.post(url, headers=headers, json=json, timeout=15)
    resp.raise_for_status()
    return resp.json().get("data") or {}


def _put(url: str, headers: dict | None = None, json: dict | None = None) -> dict:
    resp = httpx.put(url, headers=headers, json=json, timeout=15)
    resp.raise_for_status()
    return resp.json().get("data") or {}


def _ensure_user(email: str, password: str, nickname: str) -> str:
    """Register a demo user, falling back to login when it already exists."""
    register = httpx.post(f"{BASE}:8001/api/v1/auth/register", timeout=15,
                          json={"email": email, "password": password, "nickname": nickname})
    if register.status_code == 409:
        login = httpx.post(f"{BASE}:8001/api/v1/auth/login", timeout=15,
                           json={"account": email, "password": password})
        login.raise_for_status()
        return login.json()["data"]["user"]["user_id"]
    register.raise_for_status()
    return register.json()["data"]["user_id"]


def main() -> None:
    ts = int(time.time()) % 100000
    admin_h = {"X-User-Roles": "ADMIN"}

    # 1. Admin account (register then grant ADMIN so the console login works).
    admin_id = _ensure_user("admin@example.com", "Admin123!", "系统管理员")
    _put(
        f"{BASE}:8001/api/v1/users/{admin_id}/roles",
        headers={**admin_h, "X-User-Id": admin_id},
        json={"role_codes": ["ADMIN"], "reason": "seed"},
    )
    print("[OK] admin account: admin@example.com / Admin123!")

    # 2. Buyer demo account.
    _ensure_user("buyer@example.com", "Buyer123!", "演示买家")
    print("[OK] buyer account: buyer@example.com / Buyer123!")

    # 3. Category tree (level-1 categories).
    categories = [("数码 3C", "digital"), ("服饰鞋包", "fashion"), ("家居生活", "home")]
    cat_ids: dict[str, str] = {}
    for name, slug in categories:
        cat = _post(f"{BASE}:8002/api/v1/admin/categories", headers=admin_h,
                    json={"name": name, "slug": f"{slug}-{ts}"})
        cat_ids[name] = cat["id"]

    # 4. Products (price in cents, initial stock) then publish each.
    products = [
        ("降噪无线耳机 Pro", "数码 3C", 29900, 50),
        ("便携蓝牙音箱", "数码 3C", 19900, 80),
        ("纯棉圆领 T 恤", "服饰鞋包", 9900, 200),
        ("轻量通勤双肩包", "服饰鞋包", 23900, 60),
        ("原木香氛蜡烛", "家居生活", 12900, 120),
    ]
    created, published = 0, 0
    for title, category, price, stock in products:
        prod = _post(f"{BASE}:8002/api/v1/admin/products", headers=admin_h, json={
            "category_id": cat_ids[category],
            "title": title,
            "skus": [{"sku_code": f"seeded-{ts}-{created}", "spec_text": "默认规格",
                      "price_cents": price, "initial_stock": stock}],
        })
        created += 1
        _post(f"{BASE}:8002/api/v1/admin/products/{prod['id']}/publish", headers=admin_h)
        published += 1

    print(f"[OK] categories: {len(cat_ids)}, products: {created} (published {published})")
    print("Seed complete. Admin console: /admin (admin@example.com), storefront: / (buyer@example.com)")


if __name__ == "__main__":
    main()