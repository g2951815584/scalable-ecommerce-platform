"""User profile and account administration flows."""

from __future__ import annotations

from common.clock import utc_now
from common.errors import AppError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories import (
    assign_role,
    clear_roles,
    get_credential,
    get_profile,
    get_role_by_code,
    get_user_by_id,
    revoke_refresh_tokens_by_user,
)
from app.schemas.user import ProfilePatch
from app.services.auth_service import _audit, _role_codes, _user_payload


async def get_user(session: AsyncSession, user_id: int) -> dict:
    user = await get_user_by_id(session, user_id)
    if user is None:
        raise AppError("USER-4001", "用户不存在", 404)
    profile = await get_profile(session, user_id)
    roles = await _role_codes(session, user_id)
    payload = _user_payload(user, profile, roles)
    payload["oauth_bindings"] = []
    return payload


async def patch_profile(session: AsyncSession, user_id: int, patch: ProfilePatch) -> dict:
    user = await get_user_by_id(session, user_id)
    if user is None:
        raise AppError("USER-4001", "用户不存在", 404)
    profile = await get_profile(session, user_id)
    if profile is None:
        raise AppError("USER-4001", "用户不存在", 404)

    values = patch.model_dump(exclude_unset=True)
    for key, value in values.items():
        setattr(profile, key, value)
    await _audit(session, action="PROFILE_UPDATED", user_id=user_id, after_value=values)
    await session.commit()
    roles = await _role_codes(session, user_id)
    return _user_payload(user, profile, roles)


async def list_users(session: AsyncSession, *, page: int = 1, page_size: int = 20,
                     status: str | None = None, keyword: str | None = None) -> dict:
    stmt = select(User)
    count_stmt = select(func.count()).select_from(User)
    if status:
        stmt = stmt.where(User.status == status)
        count_stmt = count_stmt.where(User.status == status)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where((User.email.ilike(like)) | (User.phone.ilike(like)))
        count_stmt = count_stmt.where((User.email.ilike(like)) | (User.phone.ilike(like)))

    total = int((await session.execute(count_stmt)).scalar_one())
    users = list(
        (await session.execute(
            stmt.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        )).scalars().all()
    )
    items = []
    for user in users:
        profile = await get_profile(session, user.id)
        roles = await _role_codes(session, user.id)
        items.append(_user_payload(user, profile, roles))
    return {
        "items": items,
        "pagination": {"page": page, "page_size": page_size, "total": total,
                       "total_pages": max(1, (total + page_size - 1) // page_size)},
    }

async def assign_roles(session: AsyncSession, user_id: int, role_codes: list[str],
                       admin_id: int | None = None, reason: str | None = None) -> dict:
    user = await get_user_by_id(session, user_id)
    if user is None:
        raise AppError("USER-4001", "用户不存在", 404)

    role_ids = []
    for code in role_codes:
        role = await get_role_by_code(session, code)
        if role is None:
            raise AppError("USER-4002", f"角色不存在: {code}", 404)
        role_ids.append(role.id)

    await clear_roles(session, user_id)
    for role_id in role_ids:
        await assign_role(session, user_id, role_id, granted_by=admin_id)
    await _audit(session, action="ROLE_GRANTED", user_id=user_id, operator_id=admin_id,
                 operator_type="ADMIN", after_value={"roles": role_codes})
    await session.commit()
    return {"user_id": str(user_id), "roles": role_codes}


async def set_status(session: AsyncSession, user_id: int, status: str,
                     admin_id: int | None = None, reason: str | None = None) -> dict:
    user = await get_user_by_id(session, user_id)
    if user is None:
        raise AppError("USER-4001", "用户不存在", 404)
    if admin_id == user_id:
        raise AppError("USER-3006", "不能对本人账号执行该操作", 403)
    if user.status == status:
        raise AppError("USER-5015", "账号已处于目标状态", 409)

    before = user.status
    user.status = status
    if status == "DISABLED":
        await revoke_refresh_tokens_by_user(session, user_id, "ADMIN_DISABLED", utc_now())
    else:
        user.failed_login_count = 0
        user.locked_until = None
    await _audit(session, action="USER_DISABLED" if status == "DISABLED" else "USER_ENABLED",
                 user_id=user_id, operator_id=admin_id, operator_type="ADMIN",
                 before_value={"status": before}, after_value={"status": status, "reason": reason})
    await session.commit()
    return {"user_id": str(user_id), "status": status}


async def close_account(session: AsyncSession, user_id: int, reason: str | None = None) -> None:
    from sqlalchemy import update

    user = await get_user_by_id(session, user_id)
    if user is None or user.status == "DELETED":
        return
    user.status = "DELETED"
    user.deleted_at = utc_now()
    if user.email:
        user.email = f"deleted+{user_id}@deleted.invalid"
    if user.phone:
        user.phone = "+00000000000"
    user.failed_login_count = 0
    user.locked_until = None
    await revoke_refresh_tokens_by_user(session, user_id, "ACCOUNT_CLOSED", utc_now())
    from app.models.address import UserAddress

    await session.execute(update(UserAddress).where(UserAddress.user_id == user_id).values(deleted_at=utc_now()))
    await _audit(session, action="ACCOUNT_CLOSE_REQUESTED", user_id=user_id, after_value={"reason": reason})
    await session.commit()


async def change_password(session: AsyncSession, user_id: int, current_password, new_password) -> dict:
    from app.services.password import hash_password, verify_password

    credential = await get_credential(session, user_id)
    if credential and not verify_password(credential.password_hash, current_password or ""):
        raise AppError("USER-5010", "当前密码不正确", 409)
    if credential and verify_password(credential.password_hash, new_password):
        raise AppError("USER-5011", "新密码不能与当前密码相同", 409)
    if credential:
        credential.password_hash = hash_password(new_password)
        credential.password_updated_at = utc_now()
        await revoke_refresh_tokens_by_user(session, user_id, "PASSWORD_CHANGED", utc_now())
    await _audit(session, action="PASSWORD_CHANGED", user_id=user_id)
    await session.commit()
    return {"changed": True}


async def list_roles(session: AsyncSession) -> list[dict]:
    from app.models.rbac import Role

    roles = list((await session.execute(select(Role).order_by(Role.sort_order))).scalars().all())
    return [
        {"role_id": str(role.id), "code": role.code, "name": role.name,
         "description": role.description, "role_type": role.role_type,
         "is_enabled": role.is_enabled, "sort_order": role.sort_order,
         "permission_count": 0, "user_count": 0}
        for role in roles
    ]


async def list_permissions(session: AsyncSession) -> list[dict]:
    from app.models.rbac import Permission

    perms = list(
        (await session.execute(select(Permission).order_by(Permission.module, Permission.code))).scalars().all()
    )
    return [
        {"permission_id": str(p.id), "code": p.code, "name": p.name, "module": p.module,
         "description": p.description}
        for p in perms
    ]
