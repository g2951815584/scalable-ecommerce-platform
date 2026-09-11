"""Shipping address flows with ownership checks and optimistic locking."""

from __future__ import annotations

from common.clock import utc_now
from common.errors import AppError
from common.ids import next_id
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.address import UserAddress
from app.repositories import (
    add_address,
    clear_defaults,
    count_active,
    get_active_addresses,
    get_address,
    get_default_address,
    soft_delete_address,
)
from app.schemas.user import AddressCreate, AddressUpdate
from app.services.auth_service import _audit


def _payload(address: UserAddress) -> dict:
    return {
        "address_id": str(address.id),
        "user_id": str(address.user_id),
        "receiver_name": address.receiver_name,
        "receiver_phone": address.receiver_phone,
        "province": address.province,
        "city": address.city,
        "district": address.district,
        "detail_address": address.detail_address,
        "postal_code": address.postal_code,
        "region_code": address.region_code,
        "is_default": address.is_default,
        "version": address.version,
        "created_at": address.created_at.isoformat() if address.created_at else None,
        "updated_at": address.updated_at.isoformat() if address.updated_at else None,
    }


async def _require_owned(session: AsyncSession, user_id: int, address_id: int) -> UserAddress:
    address = await get_address(session, address_id)
    if address is None or address.user_id != user_id or address.deleted_at is not None:
        raise AppError("USER-3001", "收货地址无效，请重新选择", 403)
    return address


async def add_address_flow(session: AsyncSession, user_id: int, req: AddressCreate) -> dict:
    settings = get_settings()
    if await count_active(session, user_id) >= settings.address_max_count:
        raise AppError("USER-5007", f"收货地址数量已达上限（{settings.address_max_count} 个）", 409)

    is_default = req.is_default or await count_active(session, user_id) == 0
    if is_default:
        await clear_defaults(session, user_id)

    address = await add_address(
        session,
        UserAddress(
            id=next_id(), user_id=user_id, is_default=is_default, version=1,
            **req.model_dump(exclude={"is_default"}),
        ),
    )
    await _audit(session, action="ADDRESS_CREATED", user_id=user_id,
                 resource_type="ADDRESS", resource_id=str(address.id))
    await session.commit()
    return _payload(address)


async def list_addresses_flow(session: AsyncSession, user_id: int) -> dict:
    addresses = await get_active_addresses(session, user_id)
    settings = get_settings()
    return {"items": [_payload(a) for a in addresses], "total": len(addresses),
            "max_addresses": settings.address_max_count}


async def get_address_flow(session: AsyncSession, user_id: int, address_id: int) -> dict:
    return _payload(await _require_owned(session, user_id, address_id))


async def update_address_flow(session: AsyncSession, user_id: int, address_id: int, req: AddressUpdate) -> dict:
    address = await _require_owned(session, user_id, address_id)
    if req.version is not None and req.version != address.version:
        raise AppError("USER-6004", "地址已被修改，请刷新后重试", 429)

    values = req.model_dump(exclude_unset=True, exclude={"version"})
    make_default = values.pop("is_default", False)
    for key, value in values.items():
        setattr(address, key, value)
    if make_default and not address.is_default:
        await clear_defaults(session, user_id)
        address.is_default = True
    address.version += 1
    address.updated_at = utc_now()
    await _audit(session, action="ADDRESS_UPDATED", user_id=user_id,
                 resource_type="ADDRESS", resource_id=str(address_id))
    await session.commit()
    return _payload(address)


async def delete_address_flow(session: AsyncSession, user_id: int, address_id: int) -> None:
    address = await _require_owned(session, user_id, address_id)
    await soft_delete_address(session, address, utc_now())
    await _audit(session, action="ADDRESS_DELETED", user_id=user_id,
                 resource_type="ADDRESS", resource_id=str(address_id))
    await session.commit()


async def set_default_flow(session: AsyncSession, user_id: int, address_id: int) -> dict:
    address = await _require_owned(session, user_id, address_id)
    if not address.is_default:
        previous = await get_default_address(session, user_id)
        await clear_defaults(session, user_id)
        address.is_default = True
        address.version += 1
        await _audit(session, action="ADDRESS_SET_DEFAULT", user_id=user_id,
                     resource_type="ADDRESS", resource_id=str(address_id))
        await session.commit()
        return {**_payload(address), "previous_default_address_id": str(previous.id) if previous else None}
    return _payload(address)