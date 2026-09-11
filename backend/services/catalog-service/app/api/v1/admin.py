"""Admin catalogue routes under /api/v1/admin."""

from common.auth import require_role
from common.response import success
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import session_dep
from app.schemas import CategoryCreate, ProductCreate
from app.services import catalog_service


def build_router() -> APIRouter:
    router = APIRouter(dependencies=[Depends(require_role("ADMIN", "PRODUCT_OPS"))])

    @router.post("/categories", status_code=201)
    async def create_category(payload: CategoryCreate, request: Request, session: AsyncSession = Depends(session_dep)):
        return success(await catalog_service.create_category(session, payload),
                       trace_id=request.state.trace_id)

    @router.post("/products", status_code=201)
    async def create_product(payload: ProductCreate, request: Request, session: AsyncSession = Depends(session_dep)):
        return success(await catalog_service.create_product(session, payload),
                       trace_id=request.state.trace_id)

    @router.post("/products/{product_id}/publish")
    async def publish(product_id: int, request: Request, session: AsyncSession = Depends(session_dep)):
        return success(await catalog_service.publish(session, product_id),
                       trace_id=request.state.trace_id)

    @router.post("/products/{product_id}/unpublish")
    async def unpublish(product_id: int, request: Request, session: AsyncSession = Depends(session_dep)):
        return success(await catalog_service.unpublish(session, product_id),
                       trace_id=request.state.trace_id)

    @router.put("/inventory/{sku_id}")
    async def adjust_inventory(sku_id: int, payload: dict, request: Request, session: AsyncSession = Depends(session_dep)):
        return success(await catalog_service.adjust_inventory(
            session, sku_id, payload.get("adjust_type", "SET"), int(payload.get("quantity", 0)),
            payload.get("reason", ""), operator_id=0),
            trace_id=request.state.trace_id)

    return router