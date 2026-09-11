"""Pydantic request contracts for user-service."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class ProfilePatch(BaseModel):
    nickname: str | None = Field(default=None, min_length=1, max_length=64)
    avatar_url: str | None = Field(default=None, max_length=512)
    gender: Literal["MALE", "FEMALE", "OTHER", "UNKNOWN"] | None = None
    birthday: date | None = None
    bio: str | None = Field(default=None, max_length=200)
    locale: Literal["zh-CN", "en-US"] | None = None


class AddressCreate(BaseModel):
    receiver_name: str = Field(min_length=1, max_length=64)
    receiver_phone: str = Field(min_length=3, max_length=20)
    province: str = Field(min_length=1, max_length=64)
    city: str = Field(min_length=1, max_length=64)
    district: str = Field(min_length=1, max_length=64)
    detail_address: str = Field(min_length=1, max_length=255)
    postal_code: str | None = Field(default=None, max_length=12)
    region_code: str | None = Field(default=None, max_length=12)
    is_default: bool = False


class AddressUpdate(BaseModel):
    receiver_name: str | None = Field(default=None, min_length=1, max_length=64)
    receiver_phone: str | None = Field(default=None, min_length=3, max_length=20)
    province: str | None = Field(default=None, min_length=1, max_length=64)
    city: str | None = Field(default=None, min_length=1, max_length=64)
    district: str | None = Field(default=None, min_length=1, max_length=64)
    detail_address: str | None = Field(default=None, min_length=1, max_length=255)
    postal_code: str | None = Field(default=None, max_length=12)
    region_code: str | None = Field(default=None, max_length=12)
    is_default: bool | None = None
    version: int | None = Field(default=None, ge=1)


class BatchUsersRequest(BaseModel):
    user_ids: list[str] = Field(min_length=1, max_length=100)
    fields: list[str] | None = None
