"""Refresh token and verification code data access."""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token import RefreshToken, VerificationCode


async def add_refresh_token(session: AsyncSession, token: RefreshToken) -> RefreshToken:
    session.add(token)
    return token


async def find_refresh_token_by_hash(
    session: AsyncSession, token_hash: str
) -> RefreshToken | None:
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    return (await session.execute(stmt)).scalar_one_or_none()


async def revoke_refresh_tokens_by_user(
    session: AsyncSession, user_id: int, reason: str, revoked_at
) -> int:
    from sqlalchemy import delete as _unused  # noqa: F401

    result = await session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.status == "ACTIVE")
        .values(status="REVOKED", revoke_reason=reason, revoked_at=revoked_at)
    )
    return result.rowcount


async def revoke_family(
    session: AsyncSession, family_id, reason: str, revoked_at
) -> int:
    result = await session.execute(
        update(RefreshToken)
        .where(RefreshToken.token_family_id == family_id, RefreshToken.status == "ACTIVE")
        .values(status="REVOKED", revoke_reason=reason, revoked_at=revoked_at)
    )
    return result.rowcount


async def add_verification_code(
    session: AsyncSession, code: VerificationCode
) -> VerificationCode:
    session.add(code)
    return code


async def find_latest_code(
    session: AsyncSession, account: str, scene: str
) -> VerificationCode | None:
    stmt = (
        select(VerificationCode)
        .where(VerificationCode.account == account, VerificationCode.scene == scene)
        .order_by(VerificationCode.created_at.desc())
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()