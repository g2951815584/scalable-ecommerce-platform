"""Authentication flows: register, login, token rotation and password recovery."""

from __future__ import annotations

import hmac
import logging
from datetime import timedelta

from common.clock import utc_now
from common.errors import AppError
from common.ids import next_id
from common.outbox import make_outbox_event
from common.response import ErrorDetail

from app.core.config import get_settings
from app.models.oauth import UserAuditLog
from app.models.token import RefreshToken, VerificationCode
from app.models.user import User, UserCredential, UserProfile
from app.repositories import (
    add_refresh_token,
    add_user,
    add_verification_code,
    assign_role,
    find_latest_code,
    find_refresh_token_by_hash,
    get_credential,
    get_profile,
    get_role_by_code,
    get_user_by_account,
    get_user_by_email,
    get_user_by_id,
    get_user_by_phone,
    list_role_codes,
    revoke_family,
    revoke_refresh_tokens_by_user,
    update_credential_hash,
)
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    VerificationCodeRequest,
    VerificationCodeVerifyRequest,
)
from app.services.password import hash_password, verify_password
from app.services.token_service import (
    generate_refresh_token,
    hash_refresh_token,
    hash_verification_code,
    new_token_family_id,
    sign_access_token,
)

logger = logging.getLogger("user-service.auth")

_DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$ZHVtbXlzYWx0$ZHVtbXlkdW1teWR1bW15ZHVtbXlkdW1teWR1bW15"


async def _issue_pair(session, user, *, client_ip=None):
    settings = get_settings()
    roles = await list_role_codes(session, user.id) or ["BUYER"]
    access_token = sign_access_token(user.id, roles)
    raw_refresh = generate_refresh_token()
    row = RefreshToken(
        id=next_id(),
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh),
        token_family_id=new_token_family_id(),
        parent_token_id=None,
        status="ACTIVE",
        issued_at=utc_now(),
        expires_at=utc_now() + timedelta(seconds=settings.refresh_token_ttl_seconds),
        client_ip=client_ip,
    )
    await add_refresh_token(session, row)
    return {
        "access_token": access_token,
        "refresh_token": raw_refresh,
        "token_type": "Bearer",
        "expires_in": settings.access_token_ttl_seconds,
        "refresh_expires_in": settings.refresh_token_ttl_seconds,
    }


def _nickname(account: str) -> str:
    if "@" in account:
        local, domain = account.split("@", 1)
        return f"{local[:1]}***@{domain}"
    return f"{account[:3]}****"


async def _role_codes(session, user_id: int) -> list[str]:
    return await list_role_codes(session, user_id) or ["BUYER"]


async def register(session, req: RegisterRequest, trace_id: str, client_ip=None) -> dict:
    email = req.email.lower() if req.email else None
    if email and await get_user_by_email(session, email):
        raise AppError("USER-5001", "该邮箱已被注册", 409)
    if req.phone and await get_user_by_phone(session, req.phone):
        raise AppError("USER-5002", "该手机号已被注册", 409)

    user_id = next_id()
    user = User(
        id=user_id,
        email=email,
        phone=req.phone,
        status="ACTIVE",
        is_email_verified=bool(req.verification_code and email),
        is_phone_verified=bool(req.verification_code and req.phone),
        registered_from=req.registered_from,
    )
    credential = UserCredential(
        id=next_id(),
        user_id=user_id,
        password_hash=hash_password(req.password),
        password_updated_at=utc_now(),
    )
    profile = UserProfile(
        id=next_id(),
        user_id=user_id,
        nickname=req.nickname or _nickname(email or req.phone or "用户"),
    )
    await add_user(session, user, credential, profile)

    buyer = await get_role_by_code(session, "BUYER")
    if buyer is not None:
        await assign_role(session, user_id, buyer.id, granted_by=None)

    await _audit(session, action="REGISTER", user_id=user_id, trace_id=trace_id, client_ip=client_ip)
    event = make_outbox_event(
        event_type="user.registered",
        aggregate_type="USER",
        aggregate_id=str(user_id),
        payload={
            "user_id": str(user_id),
            "account": email or req.phone,
            "email": email,
            "phone": req.phone,
            "nickname": profile.nickname,
        },
        trace_id=trace_id,
    )
    session.add(event)

    tokens = await _issue_pair(session, user, client_ip=client_ip)
    await session.commit()
    return _user_payload(user, profile, await _role_codes(session, user_id), tokens)


async def login(session, req: LoginRequest, client_ip=None, trace_id: str = "") -> dict:
    settings = get_settings()
    user = await get_user_by_account(session, req.account)

    if user is None:
        verify_password(_DUMMY_HASH, req.password)
        raise AppError("USER-2001", "账号或密码错误", 401)

    if user.status == "DELETED":
        raise AppError("USER-2004", "账号已注销", 401)
    if user.status == "DISABLED":
        raise AppError("USER-2003", "账号已被禁用", 401)
    if user.locked_until and user.locked_until > utc_now():
        raise AppError("USER-2002", "账号已被锁定", 401,
                       details=[ErrorDetail(field="locked_until", reason=user.locked_until.isoformat())])

    credential = await get_credential(session, user.id)
    ok = credential is not None and verify_password(credential.password_hash, req.password)

    if not ok:
        user.failed_login_count += 1
        if user.failed_login_count >= settings.login_max_failures:
            user.locked_until = utc_now() + timedelta(minutes=settings.login_lock_minutes)
        await _audit(session, action="LOGIN_FAILED", user_id=user.id, trace_id=trace_id, client_ip=client_ip)
        await session.commit()
        raise AppError("USER-2001", "账号或密码错误", 401)

    if req.client_type == "ADMIN_CONSOLE":
        roles = await _role_codes(session, user.id)
        if roles == ["BUYER"]:
            raise AppError("COMMON-3001", "无权限登录管理后台", 403)

    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = utc_now()
    user.last_login_ip = client_ip
    await _audit(session, action="LOGIN", user_id=user.id, trace_id=trace_id, client_ip=client_ip)
    tokens = await _issue_pair(session, user, client_ip=client_ip)
    await session.commit()
    profile = await get_profile(session, user.id)
    roles = await _role_codes(session, user.id)
    return {**tokens, "user": _user_payload(user, profile, roles)}


async def refresh(session, req: RefreshTokenRequest, client_ip=None) -> dict:
    digest = hash_refresh_token(req.refresh_token)
    row = await find_refresh_token_by_hash(session, digest)
    if row is None:
        raise AppError("USER-2005", "刷新令牌无效或已过期", 401)

    if row.status == "USED":
        await revoke_family(session, row.token_family_id, "REPLAY_DETECTED", utc_now())
        await revoke_refresh_tokens_by_user(session, row.user_id, "REPLAY_DETECTED", utc_now())
        await _audit(session, action="REFRESH_REPLAY_DETECTED", user_id=row.user_id, client_ip=client_ip)
        await session.commit()
        raise AppError("USER-2006", "登录状态异常，出于安全已注销全部会话，请重新登录", 401)

    if row.status != "ACTIVE" or row.expires_at <= utc_now():
        raise AppError("USER-2005", "刷新令牌无效或已过期", 401)

    user = await get_user_by_id(session, row.user_id)
    if user is None or user.status in ("DISABLED", "DELETED"):
        await revoke_family(session, row.token_family_id, "ACCOUNT_CLOSED", utc_now())
        await session.commit()
        raise AppError("USER-2003" if user else "USER-2004", "账号不可用", 401)

    settings = get_settings()
    row.status = "USED"
    row.used_at = utc_now()
    row.revoke_reason = "ROTATED"

    raw_refresh = generate_refresh_token()
    new_row = RefreshToken(
        id=next_id(),
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh),
        token_family_id=row.token_family_id,
        parent_token_id=row.id,
        status="ACTIVE",
        issued_at=utc_now(),
        expires_at=utc_now() + timedelta(seconds=settings.refresh_token_ttl_seconds),
        client_ip=client_ip,
    )
    await add_refresh_token(session, new_row)
    roles = await _role_codes(session, user.id)
    access_token = sign_access_token(user.id, roles)
    await session.commit()
    return {
        "access_token": access_token,
        "refresh_token": raw_refresh,
        "token_type": "Bearer",
        "expires_in": settings.access_token_ttl_seconds,
        "refresh_expires_in": settings.refresh_token_ttl_seconds,
    }


async def logout(session, raw_refresh: str) -> None:
    row = await find_refresh_token_by_hash(session, hash_refresh_token(raw_refresh))
    if row is None or row.status != "ACTIVE":
        return
    row.status = "REVOKED"
    row.revoke_reason = "LOGOUT"
    row.revoked_at = utc_now()
    await session.commit()


async def logout_all(session, user_id: int) -> int:
    revoked = await revoke_refresh_tokens_by_user(session, user_id, "LOGOUT_ALL", utc_now())
    await session.commit()
    return revoked


async def change_password(session, user_id: int, current_password: str | None, new_password: str) -> dict:
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


async def issue_code(session, req: VerificationCodeRequest, client_ip=None) -> dict:
    import secrets

    settings = get_settings()
    plain = f"{secrets.randbelow(10 ** settings.verify_code_length):0{settings.verify_code_length}d}"
    ttl = (
        settings.verify_code_email_ttl_seconds
        if req.account_type == "EMAIL"
        else settings.verify_code_sms_ttl_seconds
    )
    code = VerificationCode(
        id=next_id(),
        account=req.account,
        account_type=req.account_type,
        scene=req.scene,
        code_hash=hash_verification_code(plain, req.account, req.scene),
        channel="EMAIL" if req.account_type == "EMAIL" else "SMS",
        max_attempts=settings.verify_code_max_attempts,
        sender_ip=client_ip,
        expires_at=utc_now() + timedelta(seconds=ttl),
    )
    await add_verification_code(session, code)
    await session.commit()
    return {
        "account": req.account,
        "scene": req.scene,
        "channel": code.channel,
        "delivery_status": "SENT",
        "expires_at": code.expires_at.isoformat(),
        "resend_after_seconds": settings.verify_code_send_interval_seconds,
        "_plain_code": plain,
    }
async def verify_code(session, req: VerificationCodeVerifyRequest) -> dict:
    row = await find_latest_code(session, req.account, req.scene)
    if row is None or row.status != "PENDING":
        raise AppError("USER-4005", "验证码不存在或已失效", 404)
    if row.expires_at <= utc_now():
        row.status = "EXPIRED"
        await session.commit()
        raise AppError("USER-5004", "验证码已过期，请重新获取", 409)

    row.attempt_count += 1
    if row.attempt_count > row.max_attempts:
        row.status = "LOCKED"
        await session.commit()
        raise AppError("USER-5005", "验证码错误次数过多，请重新获取", 409)

    expected = hash_verification_code(req.code, req.account, req.scene)
    if not hmac.compare_digest(row.code_hash, expected):
        left = max(0, row.max_attempts - row.attempt_count)
        await session.commit()
        raise AppError("USER-5003", "验证码错误", 409,
                       details=[ErrorDetail(field="code", reason=f"还可尝试 {left} 次")])

    row.status = "USED"
    row.verified_at = utc_now()
    await session.commit()
    return {"verified": True, "account": req.account, "scene": req.scene, "verification_ticket": f"vt_{row.id}"}


async def reset_password(session, req: ResetPasswordRequest) -> dict:
    user = await get_user_by_account(session, req.account)
    if user is None:
        raise AppError("USER-4001", "账号不存在", 404)
    await verify_code(
        session,
        VerificationCodeVerifyRequest(account=req.account, scene="RESET_PASSWORD", code=req.verification_code),
    )
    credential = await get_credential(session, user.id)
    if credential and verify_password(credential.password_hash, req.new_password):
        raise AppError("USER-5011", "新密码不能与当前密码相同", 409)
    await update_credential_hash(session, user.id, hash_password(req.new_password))
    if req.logout_all:
        await revoke_refresh_tokens_by_user(session, user.id, "PASSWORD_CHANGED", utc_now())
    await _audit(session, action="PASSWORD_RESET", user_id=user.id)
    await session.commit()
    return {"reset": True}


async def _audit(session, *, action, user_id=None, operator_id=None, operator_type="USER",
                 trace_id=None, client_ip=None, resource_type=None, resource_id=None,
                 after_value=None, before_value=None) -> None:
    session.add(
        UserAuditLog(
            id=next_id(),
            user_id=user_id,
            operator_id=operator_id,
            operator_type=operator_type,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            before_value=before_value,
            after_value=after_value,
            client_ip=client_ip,
            trace_id=(trace_id or "")[:64] or None,
        )
    )


def _user_payload(user, profile, roles, tokens=None) -> dict:
    payload = {
        "user_id": str(user.id),
        "email": user.email,
        "phone": user.phone,
        "nickname": profile.nickname if profile else (user.email or user.phone or ""),
        "status": user.status,
        "is_email_verified": user.is_email_verified,
        "is_phone_verified": user.is_phone_verified,
        "can_place_order": user.can_place_order,
        "roles": roles,
        "avatar_url": profile.avatar_url if profile else None,
        "gender": profile.gender if profile else "UNKNOWN",
        "birthday": profile.birthday.isoformat() if profile and profile.birthday else None,
        "bio": profile.bio if profile else None,
        "locale": profile.locale if profile else "zh-CN",
        "registered_at": user.created_at.isoformat() if user.created_at else None,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "has_password": True,
    }
    if tokens:
        payload.update(tokens)
    return payload