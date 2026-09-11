import asyncio

from app.services import cart_service
from common.redis import create_redis


async def main() -> None:
    redis = create_redis("redis://localhost:6380/15")
    owner = "u:smoke-cart"

    await redis.delete(f"cart:items:{owner}", f"cart:meta:{owner}", f"cart:seq:{owner}")

    r = await cart_service.add_item(redis, owner, 3001, 2, {"title": "T恤", "spec_text": "M/黑色", "image_url": "", "price_cents": 9900})
    print("add:", r)

    r = await cart_service.add_item(redis, owner, 3001, 3, {"title": "T恤", "price_cents": 9900})
    print("add-same-sku (累加):", r)

    r = await cart_service.add_item(redis, owner, 3002, 1, {"title": "杯子", "price_cents": 8900})
    print("add-other-sku:", r)

    cart = await cart_service.get_cart(redis, owner)
    print("get:", cart["summary"])

    item_id = cart["items"][0]["item_id"]
    r = await cart_service.update_quantity(redis, owner, item_id, 5)
    print("update-qty:", r)

    r = await cart_service.set_selected(redis, owner, None, True, select_all=True)
    print("select-all:", r)

    selected = await cart_service.get_selected_for_order(redis, owner)
    print("selected-for-order:", [(i["sku_id"], i["quantity"]) for i in selected])

    r = await cart_service.purge(redis, owner, [item_id])
    print("purge:", r)

    await redis.aclose()


asyncio.run(main())