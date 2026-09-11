"""Address data access."""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.address import UserAddress


async def get_address(session: AsyncSession, address_id: int) -> UserAddress | None:
    return await session.get(UserAddress, address_id)


async def get_active_addresses(session: AsyncSession, user_id: int) -> list[UserAddress]:
    stmt = (
        select(UserAddress)
        .where(UserAddress.user_id == user_id, UserAddress.deleted_at.is_(None))
        .order_by(UserAddress.is_default.desc(), UserAddress.created_at.desc())
    )
    return list((await session.execute(stmt)).scalars().all())


async def get_default_address(session: AsyncSession, user_id: int) -> UserAddress | None:
    stmt = select(UserAddress).where(
        UserAddress.user_id == user_id,
        UserAddress.is_default.is_(True),
        UserAddress.deleted_at.is_(None),
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def add_address(session: AsyncSession, address: UserAddress) -> UserAddress:
    session.add(address)
    return address


async def clear_defaults(session: AsyncSession, user_id: int) -> None:
    await session.execute(
        update(UserAddress)
        .where(UserAddress.user_id == user_id, UserAddress.deleted_at.is_(None))
        .values(is_default=False)
    )


async def soft_delete_address(session: AsyncSession, address: UserAddress, deleted_at) -> None:
    address.deleted_at = deleted_at


async def count_active(session: AsyncSession, user_id: int) -> int:
    stmt = select(func.count()).select_from(UserAddress).where(
        UserAddress.user_id == user_id, UserAddress.deleted_at.is_(None)
    )
    return int((await session.execute(stmt)).scalar_one())