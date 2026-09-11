"""Public catalogue routes under /api/v1/products and /api/v1/categories."""

from common.response import success
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import session_dep
from app.services import catalog_service


def build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/categories/tree")
    async def category_tree(request: Request, session: AsyncSession = Depends(session_dep)):
        return success(await catalog_service.category_tree(session), trace_id=request.state.trace_id)

    @router.get("/products")
    async def list_products(request: Request, session: AsyncSession = Depends(session_dep),
                            category_id: str | None = None, page: int = 1, page_size: int = 20,
                            keyword: str | None = None):
        cid = int(category_id) if category_id else None
        return success(await catalog_service.list_products(
            session, category_id=cid, page=page, page_size=page_size, keyword=keyword),
            trace_id=request.state.trace_id)

    @router.get("/products/search")
    async def search(request: Request, session: AsyncSession = Depends(session_dep),
                     keyword: str = "", page: int = 1, page_size: int = 20):
        if not keyword:
            return success({"items": [], "pagination": {"page": page, "page_size": page_size, "total": 0, "total_pages": 0}},
                           trace_id=request.state.trace_id)
        return success(await catalog_service.list_products(
            session, page=page, page_size=page_size, keyword=keyword),
            trace_id=request.state.trace_id)

    @router.get("/products/{product_id}")
    async def product_detail(product_id: int, request: Request, session: AsyncSession = Depends(session_dep)):
        return success(await catalog_service.get_product_detail(session, product_id),
                       trace_id=request.state.trace_id)

    return router