"""Notification routes under /api/v1."""

from common.auth import require_role
from common.response import success
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import session_dep
from app.services import notification_service


def build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/admin/notification-records", dependencies=[Depends(require_role("ADMIN"))])
    async def list_records(request: Request, session: AsyncSession = Depends(session_dep),
                           page: int = 1, page_size: int = 20):
        return success(await notification_service.list_records(session, page, page_size),
                       trace_id=request.state.trace_id)

    @router.post("/notifications/verification-code")
    async def verification_code(payload: dict, request: Request):
        """Synchronous verification-code send (mock). Code is discarded after rendering."""
        from common.clock import utc_now

        return success({
            "record_no": f"NT{utc_now().strftime('%Y%m%d')}00000001",
            "channel": payload.get("channel", "SMS"), "provider": "TWILIO",
            "status": "SENT", "degraded": False,
            "expires_at": utc_now().isoformat(),
        }, trace_id=request.state.trace_id, message="验证码已发送")

    return router