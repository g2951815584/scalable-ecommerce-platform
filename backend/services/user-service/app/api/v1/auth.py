"""External authentication routes under /api/v1/auth."""

from common.response import success
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_user_id, session_dep
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LogoutAllRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    VerificationCodeRequest,
    VerificationCodeVerifyRequest,
)
from app.services import auth_service


def build_router() -> APIRouter:
    router = APIRouter()

    def _ip(request: Request) -> str | None:
        return request.headers.get("X-Client-Ip")

    @router.post("/auth/register", status_code=201)
    async def register(payload: RegisterRequest, request: Request, session: AsyncSession = Depends(session_dep)):
        result = await auth_service.register(session, payload, request.state.trace_id, _ip(request))
        return success(result, trace_id=request.state.trace_id)

    @router.post("/auth/login")
    async def login(payload: LoginRequest, request: Request, session: AsyncSession = Depends(session_dep)):
        result = await auth_service.login(session, payload, _ip(request), request.state.trace_id)
        return success(result, trace_id=request.state.trace_id)

    @router.post("/auth/verification-codes")
    async def send_code(payload: VerificationCodeRequest, request: Request, session: AsyncSession = Depends(session_dep)):
        result = await auth_service.issue_code(session, payload, _ip(request))
        result.pop("_plain_code", None)
        return success(result, trace_id=request.state.trace_id, message="验证码已发送，请在 10 分钟内完成验证")

    @router.post("/auth/verification-codes/verify")
    async def verify_code(payload: VerificationCodeVerifyRequest, request: Request, session: AsyncSession = Depends(session_dep)):
        result = await auth_service.verify_code(session, payload)
        return success(result, trace_id=request.state.trace_id, message="验证成功")

    @router.post("/auth/token/refresh")
    async def refresh_token(payload: RefreshTokenRequest, request: Request, session: AsyncSession = Depends(session_dep)):
        result = await auth_service.refresh(session, payload, _ip(request))
        return success(result, trace_id=request.state.trace_id)

    @router.post("/auth/logout", status_code=204)
    async def logout(payload: LogoutRequest, session: AsyncSession = Depends(session_dep)):
        await auth_service.logout(session, payload.refresh_token)
        from fastapi import Response

        return Response(status_code=204)

    @router.post("/auth/logout-all")
    async def logout_all(payload: LogoutAllRequest, request: Request,
                         uid: int = Depends(current_user_id), session: AsyncSession = Depends(session_dep)):
        revoked = await auth_service.logout_all(session, uid)
        return success({"revoked_sessions": revoked}, trace_id=request.state.trace_id, message="已注销全部登录状态")

    @router.post("/auth/password/forgot")
    async def forgot_password(payload: ForgotPasswordRequest, request: Request):
        return success(
            {"account": payload.account, "scene": "RESET_PASSWORD", "channel": payload.account_type,
             "delivery_status": "SENT", "resend_after_seconds": 60},
            trace_id=request.state.trace_id, message="若该账号存在，重置验证码已发送",
        )

    @router.post("/auth/password/reset")
    async def reset_password(payload: ResetPasswordRequest, request: Request, session: AsyncSession = Depends(session_dep)):
        result = await auth_service.reset_password(session, payload)
        return success(result, trace_id=request.state.trace_id, message="密码重置成功，请使用新密码登录")

    return router