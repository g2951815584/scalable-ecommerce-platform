"""Cart routes under /api/v1/cart."""

from common.response import success
from fastapi import APIRouter, Request

from app.clients import catalog_client
from app.core.config import get_settings
from app.core.deps import get_redis, resolve_owner
from app.services import cart_service


def build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/cart")
    async def get_cart(request: Request):
        owner = resolve_owner()
        redis = get_redis(request)
        return success(await cart_service.get_cart(redis, owner), trace_id=request.state.trace_id)

    @router.get("/cart/count")
    async def cart_count(request: Request):
        owner = resolve_owner()
        redis = get_redis(request)
        data = await cart_service.get_cart(redis, owner)
        return success(data["summary"], trace_id=request.state.trace_id)

    @router.post("/cart/items", status_code=200)
    async def add_item(payload: dict, request: Request):
        owner = resolve_owner()
        redis = get_redis(request)
        sku_id = int(payload["sku_id"])
        quantity = int(payload["quantity"])
        # Fetch a snapshot from catalogue for validation/display.
        snapshot = {"title": f"商品{sku_id}", "spec_text": "", "image_url": "", "price_cents": 0}
        try:
            row = (await catalog_client.batch_query([sku_id], get_settings().internal_token)).get(sku_id)
            if row and row.get("is_sellable") is False:
                from common.errors import AppError
                raise AppError("CART-5003", "商品已下架或售罄", 409)
            if row:
                snapshot = {"title": f"商品{sku_id}", "spec_text": "", "image_url": "",
                            "price_cents": row.get("price_cents", 0)}
        except RuntimeError:
            from common.errors import AppError
            raise AppError("CART-7001", "商品信息暂时无法获取，请稍后重试", 502)
        result = await cart_service.add_item(redis, owner, sku_id, quantity, snapshot)
        return success(result, trace_id=request.state.trace_id)

    @router.put("/cart/items/{item_id}")
    async def update_quantity(item_id: str, payload: dict, request: Request):
        owner = resolve_owner()
        redis = get_redis(request)
        result = await cart_service.update_quantity(redis, owner, item_id, int(payload["quantity"]))
        return success(result, trace_id=request.state.trace_id)

    @router.delete("/cart/items/{item_id}", status_code=204)
    async def remove_item(item_id: str, request: Request):
        owner = resolve_owner()
        redis = get_redis(request)
        await cart_service.remove_items(redis, owner, [item_id])
        from fastapi import Response
        return Response(status_code=204)

    @router.post("/cart/items/batch-delete")
    async def batch_delete(payload: dict, request: Request):
        owner = resolve_owner()
        redis = get_redis(request)
        result = await cart_service.remove_items(redis, owner, payload.get("item_ids", []))
        return success(result, trace_id=request.state.trace_id)

    @router.post("/cart/items/select")
    async def select(payload: dict, request: Request):
        owner = resolve_owner()
        redis = get_redis(request)
        result = await cart_service.set_selected(
            redis, owner, payload.get("item_ids"), payload.get("selected", True),
            payload.get("select_all", False))
        return success(result, trace_id=request.state.trace_id)

    return router