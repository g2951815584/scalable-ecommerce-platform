"""Internal cart routes for order-service."""

from common.auth import require_internal
from common.response import success
from fastapi import APIRouter, Depends, Request

from app.core.deps import get_redis
from app.services import cart_service


def build_router() -> APIRouter:
    router = APIRouter(dependencies=[Depends(require_internal())])

    @router.get("/cart/{user_id}/selected-items")
    async def selected_items(user_id: int, request: Request):
        redis = get_redis(request)
        items = await cart_service.get_selected_for_order(redis, f"u:{user_id}")
        return success({
            "cart_id": "0", "cart_version": "0", "stale": False,
            "items": items, "excluded_items": [],
            "summary": {"item_count": len(items), "total_quantity": sum(i["quantity"] for i in items),
                        "goods_amount_cents": sum(i["unit_price_cents"] * i["quantity"] for i in items)},
            "currency": "CNY",
        }, trace_id=request.state.trace_id)

    @router.post("/cart/{user_id}/purge")
    async def purge(user_id: int, payload: dict, request: Request):
        redis = get_redis(request)
        result = await cart_service.purge(redis, f"u:{user_id}", payload.get("item_ids", []))
        return success({**result, "order_no": payload.get("order_no", "")}, trace_id=request.state.trace_id)

    return router