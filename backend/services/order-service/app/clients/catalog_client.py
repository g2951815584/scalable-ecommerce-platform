"""HTTP client for catalog-service inventory reserve/release.

The downstream reserve is a single atomic transaction (all-or-nothing): when it
fails with 409 the catalogue has already rolled back, so the caller only needs
to compensate when the *order* insert afterwards fails.  Transport errors and
5xx are surfaced as ``ORD-7002`` (service unavailable) rather than leaking a
raw 500.
"""

import logging

import httpx
from common.errors import AppError
from common.response import ErrorDetail

from app.core.config import get_settings

logger = logging.getLogger("order-service.catalog-client")


def _read_details(body: dict) -> list[ErrorDetail]:
    details = body.get("details") or []
    result = []
    for item in details:
        if isinstance(item, dict) and item.get("reason"):
            result.append(ErrorDetail(field=item.get("field"), reason=item["reason"]))
    return result or [ErrorDetail(field="items", reason="部分商品库存不足")]


async def reserve_stock(order_no: str, items: list[dict], internal_token: str) -> dict:
    settings = get_settings()
    payload = {
        "order_no": order_no,
        "items": [{"sku_id": str(i["sku_id"]), "quantity": int(i["quantity"])} for i in items],
    }
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(
                f"{settings.catalog_service_url}/internal/v1/inventory/reserve",
                headers={"X-Internal-Token": internal_token},
                json=payload,
            )
    except httpx.HTTPError as exc:
        logger.warning("inventory reserve transport error: %s", exc)
        raise AppError("ORD-7002", "商品服务暂不可用，请稍后重试", 502) from exc

    if resp.status_code == 409:
        body = resp.json()
        raise AppError(
            "ORD-5001",
            body.get("message") or "部分商品库存不足，请调整数量后重试",
            409,
            details=_read_details(body),
        )
    if resp.status_code >= 500:
        raise AppError("ORD-7002", "商品服务暂不可用，请稍后重试", 502)
    if resp.status_code >= 400:
        raise AppError("ORD-7002", "商品服务校验失败，请稍后重试", 502)

    return resp.json().get("data") or {}


async def release_stock(order_no: str, internal_token: str) -> None:
    """Idempotent compensation: release every reserved item for ``order_no``."""
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            await client.post(
                f"{settings.catalog_service_url}/internal/v1/inventory/release",
                headers={"X-Internal-Token": internal_token},
                json={"order_no": order_no, "reason": "ORDER_ROLLBACK"},
            )
    except Exception as exc:
        logger.warning("inventory release compensation failed for %s: %s", order_no, exc)