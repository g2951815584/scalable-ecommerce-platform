"""Typed application errors and FastAPI handlers."""


from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .response import ErrorDetail, failure


class AppError(Exception):
    """An expected domain error crossing an HTTP seam."""

    def __init__(self, code: str, message: str, status_code: int = 400, details: list[ErrorDetail] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        body = failure(exc.code, exc.message, details=exc.details, trace_id=getattr(request.state, "trace_id", None))
        return JSONResponse(status_code=exc.status_code, content=body.model_dump(mode="json"))

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            ErrorDetail(field=".".join(str(part) for part in error.get("loc", [])), reason=error.get("msg", "invalid"))
            for error in exc.errors()
        ]
        body = failure(
            "COMMON-1001",
            "请求参数校验失败",
            details=details,
            trace_id=getattr(request.state, "trace_id", None),
        )
        return JSONResponse(status_code=400, content=body.model_dump(mode="json"))

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        # Do not include exception details in the client response; structured
        # logging/telemetry can attach the traceback in a real deployment.
        body = failure("COMMON-8001", "服务内部错误", trace_id=getattr(request.state, "trace_id", None))
        return JSONResponse(status_code=500, content=body.model_dump(mode="json"))
