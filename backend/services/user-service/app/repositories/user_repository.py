"""User, credential, profile and role data access."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rbac import Role, UserRole
from app.models.user import User, UserCredential, UserProfile


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def get_user_by_account(session: AsyncSession, account: str) -> User | None:
    stmt = select(User).where((User.email == account) | (User.phone == account))
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_user_by_phone(session: AsyncSession, phone: str) -> User | None:
    stmt = select(User).where(User.phone == phone)
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_credential(session: AsyncSession, user_id: int) -> UserCredential | None:
    stmt = select(UserCredential).where(UserCredential.user_id == user_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_profile(session: AsyncSession, user_id: int) -> UserProfile | None:
    stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def add_user(
    session: AsyncSession, user: User, credential: UserCredential, profile: UserProfile
) -> None:
    session.add(user)
    session.add(credential)
    session.add(profile)


async def update_credential_hash(
    session: AsyncSession, user_id: int, password_hash: str
) -> None:
    credential = await get_credential(session, user_id)
    if credential is not None:
        credential.password_hash = password_hash


async def get_role_by_code(session: AsyncSession, code: str) -> Role | None:
    stmt = select(Role).where(Role.code == code)
    return (await session.execute(stmt)).scalar_one_or_none()


async def list_role_codes(session: AsyncSession, user_id: int) -> list[str]:
    stmt = (
        select(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id, Role.is_enabled.is_(True))
        .order_by(Role.sort_order)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return list(rows)


async def assign_role(
    session: AsyncSession, user_id: int, role_id: int, granted_by: int | None = None
) -> None:
    from common.clock import utc_now
    from common.ids import next_id

    session.add(
        UserRole(id=next_id(), user_id=user_id, role_id=role_id, granted_by=granted_by, granted_at=utc_now())
    )


async def clear_roles(session: AsyncSession, user_id: int) -> None:
    await session.execute(delete(UserRole).where(UserRole.user_id == user_id))
