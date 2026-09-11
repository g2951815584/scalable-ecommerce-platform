"""Pydantic request/response contracts."""

from .admin import (
    AssignRolesRequest,
    RoleCreate,
    RolePermissionUpdate,
    RoleUpdate,
    RoleView,
    SetStatusRequest,
)
from .auth import (
    ChangePasswordRequest,
    CloseAccountRequest,
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
from .user import AddressCreate, AddressUpdate, BatchUsersRequest, ProfilePatch

__all__ = [
    "AddressCreate",
    "AddressUpdate",
    "AssignRolesRequest",
    "BatchUsersRequest",
    "ChangePasswordRequest",
    "CloseAccountRequest",
    "ForgotPasswordRequest",
    "LoginRequest",
    "LogoutAllRequest",
    "LogoutRequest",
    "ProfilePatch",
    "RefreshTokenRequest",
    "RegisterRequest",
    "ResetPasswordRequest",
    "RoleCreate",
    "RolePermissionUpdate",
    "RoleUpdate",
    "RoleView",
    "SetStatusRequest",
    "VerificationCodeRequest",
    "VerificationCodeVerifyRequest",
]
