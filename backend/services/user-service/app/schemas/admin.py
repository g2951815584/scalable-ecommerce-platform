"""Admin request contracts: roles and account management."""

from typing import Literal

from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    code: str = Field(pattern=r"^[A-Z][A-Z0-9_]{2,63}$")
    name: str = Field(min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=255)
    permission_codes: list[str] = Field(default_factory=list)
    sort_order: int = Field(default=0, ge=0, le=999)


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=255)
    is_enabled: bool | None = None
    sort_order: int | None = Field(default=None, ge=0, le=999)


class RolePermissionUpdate(BaseModel):
    permission_codes: list[str] = Field(default_factory=list)


class AssignRolesRequest(BaseModel):
    role_codes: list[str] = Field(min_length=1, max_length=10)
    reason: str | None = Field(default=None, max_length=200)


class SetStatusRequest(BaseModel):
    status: Literal["ACTIVE", "DISABLED"]
    reason: str | None = Field(default=None, max_length=200)


class RoleView(BaseModel):
    role_id: str
    code: str
    name: str
    description: str | None = None
    role_type: str
    is_enabled: bool
    sort_order: int
    permission_count: int = 0
    user_count: int = 0