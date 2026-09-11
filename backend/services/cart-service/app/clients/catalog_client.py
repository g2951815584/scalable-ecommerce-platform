"""HTTP client for catalog-service batch query."""

from __future__ import annotations

import httpx

from app.core.config import get_settings


async def batch_query(sku_ids: list[int], internal_token: str) -> dict[int, dict]:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=3.0) as client:
        try:
            resp = await client.post(
                f"{settings.catalog_service_url}/internal/v1/inventory/batch-query",
                headers={"X-Internal-Token": internal_token},
                json={"sku_ids": [str(s) for s in sku_ids]},
            )
            resp.raise_for_status()
            body = resp.json()
            items = (body.get("data") or {}).get("items") or []
            return {int(i["sku_id"]): i for i in items}
        except Exception as exc:
            raise RuntimeError(f"catalog batch query failed: {exc}") from exc