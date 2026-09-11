"""Uniform response envelope mandated by the detailed design."""

from datetime import UTC, datetime
from typing import Generic, TypeVar
from uuid import uuid4

from pydantic import BaseModel, Field

T = TypeVar("T")


def utc_now() -> datetime:
    return datetime.now(UTC)


class ErrorDetail(BaseModel):
    field: str | None = None
    reason: str


class ApiResponse(BaseModel, Generic[T]):
    code: str = "OK"
    message: str = "success"
    data: T | None = None
    details: list[ErrorDetail] | None = None
    trace_id: str = Field(default_factory=lambda: uuid4().hex)
    timestamp: datetime = Field(default_factory=utc_now)


def success(data: T | None = None, *, trace_id: str | None = None, message: str = "success") -> ApiResponse[T]:
    return ApiResponse(code="OK", message=message, data=data, trace_id=trace_id or uuid4().hex)


def failure(
    code: str,
    message: str,
    *,
    details: list[ErrorDetail] | None = None,
    trace_id: str | None = None,
) -> ApiResponse[None]:
    return ApiResponse(
        code=code,
        message=message,
        data=None,
        details=details,
        trace_id=trace_id or uuid4().hex,
    )


class Pagination(BaseModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class CursorPage(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = None
    has_more: bool = False
