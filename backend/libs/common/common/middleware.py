"""Request correlation middleware shared by every service."""

import logging
import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("ecommerce.request")


class TraceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        trace_id = request.headers.get("X-Trace-Id") or uuid4().hex
        request_id = request.headers.get("X-Request-Id") or uuid4().hex
        request.state.trace_id = trace_id
        request.state.request_id = request_id
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("request failed", extra={"trace_id": trace_id, "path": request.url.path})
            raise
        response.headers["X-Trace-Id"] = trace_id
        response.headers["X-Request-Id"] = request_id
        logger.info(
            "request completed",
            extra={
                "service": request.app.title,
                "trace_id": trace_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        )
        return response
