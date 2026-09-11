"""Authentication request contracts."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class RegisterRequest(BaseModel):
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=20)
    password: str = Field(min_length=8, max_length=64)
    nickname: str | None = Field(default=None, min_length=1, max_length=64)
    verification_code: str | None = Field(default=None, min_length=6, max_length=6)
    registered_from: Literal["WEB", "IOS", "ANDROID"] = "WEB"

    @model_validator(mode="after")
    def account_required(self) -> "RegisterRequest":
        if not self.email and not self.phone:
            raise ValueError("email 或 phone 至少填写一个")
        password = self.password
        if any(char.isspace() for char in password):
            raise ValueError("密码不能包含空白字符")
        if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
            raise ValueError("密码需同时包含字母和数字")
        return self


class LoginRequest(BaseModel):
    account: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=128)
    client_type: Literal["WEB", "ADMIN_CONSOLE"] = "WEB"


class VerificationCodeRequest(BaseModel):
    account: str = Field(min_length=1, max_length=254)
    account_type: Literal["EMAIL", "PHONE"]
    scene: Literal[
        "REGISTER", "LOGIN", "RESET_PASSWORD", "BIND_EMAIL", "BIND_PHONE", "CLOSE_ACCOUNT"
    ]


class VerificationCodeVerifyRequest(BaseModel):
    account: str = Field(min_length=1, max_length=254)
    scene: str
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=512)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=512)


class LogoutAllRequest(BaseModel):
    keep_current: bool = False


class ForgotPasswordRequest(BaseModel):
    account: str = Field(min_length=1, max_length=254)
    account_type: Literal["EMAIL", "PHONE"]


class ResetPasswordRequest(BaseModel):
    account: str = Field(min_length=1, max_length=254)
    verification_code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    new_password: str = Field(min_length=8, max_length=64)
    logout_all: bool = True


class ChangePasswordRequest(BaseModel):
    current_password: str | None = Field(default=None, max_length=128)
    new_password: str = Field(min_length=8, max_length=64)
    logout_other_sessions: bool = True


class CloseAccountRequest(BaseModel):
    verification_ticket: str | None = None
    verification_code: str | None = None
    reason: str | None = Field(default=None, max_length=200)