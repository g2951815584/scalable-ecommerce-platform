"""Catalogue reads/writes: category tree, product aggregate and listing."""

from __future__ import annotations

from common.clock import utc_now
from common.errors import AppError
from common.ids import next_id
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import Inventory
from app.models.misc import ProductChangeLog
from app.models.product import Category, Sku, Spu
from app.schemas import CategoryCreate, ProductCreate


def _category_payload(c: Category) -> dict:
    return {"id": str(c.id), "name": c.name, "slug": c.slug, "depth": c.depth,
            "icon_url": c.icon_url, "product_count": c.product_count, "children": []}


async def category_tree(session: AsyncSession) -> dict:
    cats = list((await session.execute(
        select(Category).where(Category.is_enabled.is_(True), Category.deleted_at.is_(None))
        .order_by(Category.depth, Category.sort_order)
    )).scalars().all())

    nodes: dict[int, dict] = {c.id: _category_payload(c) for c in cats}
    roots = []
    for c in cats:
        payload = nodes[c.id]
        if c.parent_id and c.parent_id in nodes:
            nodes[c.parent_id]["children"].append(payload)
        else:
            roots.append(payload)
    return {"items": roots, "total": len(roots), "max_depth": 3}


async def create_category(session: AsyncSession, req: CategoryCreate) -> dict:
    parent = None
    depth = 1
    path = ""
    if req.parent_id:
        parent = await session.get(Category, int(req.parent_id))
        if parent is None or parent.deleted_at is not None:
            raise AppError("CAT-4005", "分类不存在", 404)
        depth = parent.depth + 1
        if depth > 3:
            raise AppError("CAT-5014", "分类最多支持 3 级", 409)
        path = parent.path

    category = Category(id=next_id(), parent_id=parent.id if parent else None, name=req.name,
                        slug=req.slug, path=path, depth=depth,
                        level_name=f"LEVEL_{depth}", sort_order=req.sort_order)
    session.add(category)
    await session.flush()
    category.path = f"{path}{category.id}/"
    await session.commit()
    return {"id": str(category.id), "path": category.path, "depth": category.depth}


async def create_product(session: AsyncSession, req: ProductCreate, operator_id: int = 0) -> dict:
    spu = Spu(id=next_id(), category_id=int(req.category_id), title=req.title,
              subtitle=req.subtitle, brand=req.brand, description=req.description,
              main_image_url=req.main_image_url, status="DRAFT")
    session.add(spu)

    sku_payloads = []
    for s in req.skus:
        sku = Sku(id=next_id(), spu_id=spu.id, sku_code=s.sku_code, spec_text=s.spec_text,
                  price_cents=s.price_cents, original_price_cents=s.original_price_cents,
                  image_url=s.image_url, status="ENABLED")
        session.add(sku)
        session.add(Inventory(id=next_id(), sku_id=sku.id, stock=s.initial_stock,
                              low_stock_threshold=s.low_stock_threshold))
        sku_payloads.append({"id": str(sku.id), "sku_code": s.sku_code})

    session.add(ProductChangeLog(id=next_id(), entity_type="SPU", entity_id=spu.id,
                                 spu_id=spu.id, action="CREATE", changed_fields=[],
                                 operator_id=operator_id))
    await session.flush()
    await _recalc_price_range(session, spu.id)
    await session.commit()
    return {"id": str(spu.id), "status": "DRAFT", "skus": sku_payloads}


async def _get_spu(session: AsyncSession, spu_id: int) -> Spu:
    spu = await session.get(Spu, spu_id)
    if spu is None or spu.deleted_at is not None:
        raise AppError("CAT-4001", "商品不存在", 404)
    return spu


async def _recalc_price_range(session: AsyncSession, spu_id: int) -> None:
    from sqlalchemy import func as sqlfunc

    row = (await session.execute(
        select(sqlfunc.min(Sku.price_cents), sqlfunc.max(Sku.price_cents))
        .where(Sku.spu_id == spu_id, Sku.status == "ENABLED", Sku.deleted_at.is_(None))
    )).one()
    spu = await session.get(Spu, spu_id)
    spu.min_price_cents, spu.max_price_cents = row[0], row[1]


async def get_product_detail(session: AsyncSession, spu_id: int) -> dict:
    spu = await _get_spu(session, spu_id)
    if spu.status != "ON_SALE":
        raise AppError("CAT-4002", "商品已下架", 404)

    skus = list((await session.execute(
        select(Sku).where(Sku.spu_id == spu_id, Sku.deleted_at.is_(None), Sku.status == "ENABLED")
        .order_by(Sku.sort_order)
    )).scalars().all())

    sku_payloads = []
    for sku in skus:
        inventory = (await session.execute(
            select(Inventory).where(Inventory.sku_id == sku.id)
        )).scalar_one_or_none()
        available = (inventory.stock - inventory.reserved) if inventory else 0
        sku_payloads.append({
            "id": str(sku.id), "sku_code": sku.sku_code, "spec_text": sku.spec_text,
            "price_cents": sku.price_cents, "original_price_cents": sku.original_price_cents,
            "currency": sku.currency, "image_url": sku.image_url, "status": sku.status,
            "available": available, "is_sellable": available > 0,
        })

    return {
        "id": str(spu.id), "title": spu.title, "subtitle": spu.subtitle, "brand": spu.brand,
        "category_id": str(spu.category_id), "status": spu.status,
        "description": spu.description, "main_image_url": spu.main_image_url,
        "price": {"min_price_cents": spu.min_price_cents, "max_price_cents": spu.max_price_cents,
                  "currency": spu.currency},
        "skus": sku_payloads,
        "rating_avg": spu.rating_avg, "review_count": spu.review_count,
        "sales_count": spu.sales_count,
        "published_at": spu.published_at.isoformat() if spu.published_at else None,
    }


async def list_products(session: AsyncSession, *, category_id: int | None = None,
                        page: int = 1, page_size: int = 20, keyword: str | None = None) -> dict:
    from sqlalchemy import func as sqlfunc

    stmt = select(Spu).where(Spu.status == "ON_SALE", Spu.deleted_at.is_(None))
    if category_id is not None:
        stmt = stmt.where(Spu.category_id.in_(await _subtree_ids(session, category_id)))
    if keyword:
        stmt = stmt.where(Spu.title.ilike(f"%{keyword}%"))

    total = int((await session.execute(
        select(sqlfunc.count()).select_from(Spu).where(*stmt.whereclause)
    )).scalar_one())

    spus = list((await session.execute(
        stmt.order_by(Spu.published_at.desc(), Spu.id.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )).scalars().all())

    items = [{
        "id": str(s.id), "title": s.title, "subtitle": s.subtitle, "brand": s.brand,
        "main_image_url": s.main_image_url, "category_id": str(s.category_id),
        "min_price_cents": s.min_price_cents, "max_price_cents": s.max_price_cents,
        "currency": s.currency, "sales_count": s.sales_count,
        "rating_avg": s.rating_avg, "review_count": s.review_count,
        "published_at": s.published_at.isoformat() if s.published_at else None,
    } for s in spus]

    return {"items": items, "pagination": {"page": page, "page_size": page_size,
                                          "total": total,
                                          "total_pages": max(1, (total + page_size - 1) // page_size)}}


async def _subtree_ids(session: AsyncSession, category_id: int) -> list[int]:
    category = await session.get(Category, category_id)
    if category is None:
        return [category_id]
    rows = list((await session.execute(
        select(Category.id).where(Category.path.like(f"{category.path}%"),
                                  Category.deleted_at.is_(None))
    )).scalars().all())
    return rows or [category_id]


async def publish(session: AsyncSession, spu_id: int) -> dict:
    spu = await _get_spu(session, spu_id)
    spu.status = "ON_SALE"
    if spu.published_at is None:
        spu.published_at = utc_now()
    await _recalc_price_range(session, spu_id)
    await session.commit()
    return {"id": str(spu_id), "status": "ON_SALE",
            "published_at": spu.published_at.isoformat()}


async def unpublish(session: AsyncSession, spu_id: int) -> dict:
    spu = await _get_spu(session, spu_id)
    spu.status = "OFF_SALE"
    spu.off_sale_at = utc_now()
    await session.commit()
    return {"id": str(spu_id), "status": "OFF_SALE"}


async def adjust_inventory(session: AsyncSession, sku_id: int, adjust_type: str,
                           quantity: int, reason: str, operator_id: int = 0) -> dict:
    if not reason:
        raise AppError("CAT-1001", "调整原因必填", 400)
    inventory = (await session.execute(
        select(Inventory).where(Inventory.sku_id == sku_id)
    )).scalar_one_or_none()
    if inventory is None:
        raise AppError("CAT-4006", "商品规格不存在", 404)

    if adjust_type == "SET":
        if quantity < inventory.reserved:
            raise AppError("CAT-5006", "调整后库存低于已预占数量，无法调整", 409)
        inventory.stock = quantity
    elif adjust_type == "INCREASE":
        inventory.stock += quantity
    else:  # DECREASE
        if inventory.stock - quantity < inventory.reserved:
            raise AppError("CAT-5006", "调整后库存低于已预占数量，无法调整", 409)
        inventory.stock -= quantity
    inventory.version += 1
    from app.models.inventory import InventoryTransaction

    session.add(InventoryTransaction(
        id=next_id(), sku_id=sku_id, txn_type="ADJUST", quantity=quantity if adjust_type != "DECREASE" else -quantity,
        stock_after=inventory.stock, reserved_after=inventory.reserved,
        available_after=inventory.stock - inventory.reserved, sold_after=inventory.sold,
        reason=reason, operator_id=operator_id, operator_type="ADMIN", ref_type="MANUAL"))
    await session.commit()
    return {"sku_id": str(sku_id), "stock": inventory.stock, "reserved": inventory.reserved,
            "available": inventory.stock - inventory.reserved, "sold": inventory.sold,
            "low_stock_threshold": inventory.low_stock_threshold}