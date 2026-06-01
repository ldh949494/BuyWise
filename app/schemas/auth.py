"""Ordinary user authentication schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.common import BaseSchema


class OtpRequest(BaseSchema):
    phone: str = Field(min_length=1, max_length=32)


class OtpRequestResponse(BaseSchema):
    phone_masked: str
    debug_otp: str | None = None


class OtpVerifyRequest(BaseSchema):
    phone: str = Field(min_length=1, max_length=32)
    code: str = Field(min_length=4, max_length=12)
    device_id: str | None = Field(default=None, max_length=128)
    device_name: str | None = Field(default=None, max_length=128)


class RefreshRequest(BaseSchema):
    refresh_token: str = Field(min_length=16)


class LogoutRequest(BaseSchema):
    refresh_token: str = Field(min_length=16)


class UserProfileResponse(BaseSchema):
    id: int
    phone_masked: str
    display_name: str | None = None
    avatar_url: str | None = None
    account_type: str = "user"
    created_at: datetime


class UserAuthTokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"
    user: UserProfileResponse


class RefreshResponse(BaseSchema):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"
