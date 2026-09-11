"""Cart core: Redis-hash primary storage with catalogue validation."""

from __future__ import annotations

import json
import time

from common.errors import AppError

from app.core.config import get_settings


def _items_key(owner: str) -> str:
    return f"cart:items:{owner}"


def _meta_key(owner: str) -> str:
    return f"cart:meta:{owner}"


async def _all_items(redis, owner: str) -> dict[str, dict]:
    raw = await redis.hgetall(_items_key(owner))
    return {k: json.loads(v) for k, v in raw.items()}


async def _recalc_meta(redis, owner: str, items: dict[str, dict]) -> None:
    total_qty = sum(i["quantity"] for i in items.values())
    selected = [i for i in items.values() if i.get("is_selected", True)]
    meta = {
        "ic": len(items),
        "iq": total_qty,
        "sc": len(selected),
        "sq": sum(i["quantity"] for i in selected),
        "sa": sum(i["price"] * i["quantity"] for i in selected),
        "seq": await redis.incr(f"cart:seq:{owner}"),
    }
    await redis.hset(_meta_key(owner), mapping=meta)
    ttl = get_settings().redis_ttl_seconds
    await redis.expire(_items_key(owner), ttl)


async def add_item(redis, owner: str, sku_id: int, quantity: int, snapshot: dict) -> dict:
    settings = get_settings()
    items = await _all_items(redis, owner)
    if len(items) >= settings.max_items_per_cart and str(sku_id) not in {i["sku_id"] for i in items.values()}:
        raise AppError("CART-5002", "购物车已满", 409)

    existing_id = next((iid for iid, i in items.items() if i["sku_id"] == sku_id), None)
    if existing_id:
        item = items[existing_id]
        item["quantity"] = min(item["quantity"] + quantity, settings.max_item_quantity)
        item_id = existing_id
    else:
        item = {
            "sku_id": sku_id, "quantity": min(quantity, settings.max_item_quantity),
            "is_selected": True, "title": snapshot.get("title", ""),
            "spec": snapshot.get("spec_text", ""), "image": snapshot.get("image_url", ""),
            "price": snapshot.get("price_cents", 0), "added_at": int(time.time()),
        }
        item_id = str(int(time.time() * 1000) % 10000000000000)
        item["item_id"] = item_id
        items[item_id] = item

    await redis.hset(_items_key(owner), item_id, json.dumps(item))
    await _recalc_meta(redis, owner, items)
    return {"item_id": item_id, "quantity": item["quantity"], "is_selected": item["is_selected"]}


async def get_cart(redis, owner: str) -> dict:
    items = await _all_items(redis, owner)
    meta = await redis.hgetall(_meta_key(owner))
    return {
        "items": [{"item_id": iid, **item} for iid, item in sorted(
            items.items(), key=lambda kv: kv[1].get("added_at", 0))],
        "summary": {
            "item_count": int(meta.get("ic", 0) or 0),
            "total_quantity": int(meta.get("iq", 0) or 0),
            "selected_item_count": int(meta.get("sc", 0) or 0),
            "selected_quantity": int(meta.get("sq", 0) or 0),
            "selected_amount_cents": int(meta.get("sa", 0) or 0),
        },
    }


async def update_quantity(redis, owner: str, item_id: str, quantity: int) -> dict:
    items = await _all_items(redis, owner)
    if item_id not in items:
        raise AppError("CART-4002", "该商品已不在购物车中", 404)
    if quantity == 0:
        await redis.hdel(_items_key(owner), item_id)
        items.pop(item_id)
        await _recalc_meta(redis, owner, items)
        return {"item_id": item_id, "quantity": 0, "removed": True}
    if quantity > get_settings().max_item_quantity:
        raise AppError("CART-5001", f"该商品最多可购买 {get_settings().max_item_quantity} 件", 409)
    items[item_id]["quantity"] = quantity
    await redis.hset(_items_key(owner), item_id, json.dumps(items[item_id]))
    await _recalc_meta(redis, owner, items)
    return {"item_id": item_id, "quantity": quantity, "removed": False}


async def remove_items(redis, owner: str, item_ids: list[str]) -> dict:
    items = await _all_items(redis, owner)
    removed, not_found = [], []
    for iid in item_ids:
        if iid in items:
            await redis.hdel(_items_key(owner), iid)
            items.pop(iid)
            removed.append(iid)
        else:
            not_found.append(iid)
    await _recalc_meta(redis, owner, items)
    return {"purged_count": len(removed), "not_found_ids": not_found}


async def set_selected(redis, owner: str, item_ids: list[str] | None, selected: bool, select_all: bool) -> dict:
    items = await _all_items(redis, owner)
    targets = list(items) if select_all else (item_ids or [])
    for iid in targets:
        if iid in items:
            items[iid]["is_selected"] = selected
            await redis.hset(_items_key(owner), iid, json.dumps(items[iid]))
    await _recalc_meta(redis, owner, items)
    meta = await redis.hgetall(_meta_key(owner))
    return {
        "selected_item_count": int(meta.get("sc", 0) or 0),
        "selected_quantity": int(meta.get("sq", 0) or 0),
        "selected_amount_cents": int(meta.get("sa", 0) or 0),
    }


async def get_selected_for_order(redis, owner: str) -> list[dict]:
    items = await _all_items(redis, owner)
    return [
        {"item_id": iid, "sku_id": item["sku_id"], "quantity": item["quantity"],
         "unit_price_cents": item["price"], "title": item["title"],
         "spec_name": item["spec"], "image_url": item["image"]}
        for iid, item in items.items() if item.get("is_selected", True)
    ]


async def purge(redis, owner: str, item_ids: list[str]) -> dict:
    return await remove_items(redis, owner, item_ids)