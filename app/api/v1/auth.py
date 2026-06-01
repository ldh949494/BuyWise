"""Ordinary user authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.providers import AppError, Principal, require_principal
from app.schemas.auth import (
    LogoutRequest,
    OtpRequest,
    OtpRequestResponse,
    OtpVerifyRequest,
    RefreshRequest,
    RefreshResponse,
    UserAuthTokenResponse,
    UserProfileResponse,
)
from app.services.user_auth_service import UserAuthService, build_masked_phone

router = APIRouter(prefix="/auth")


def get_user_auth_service(db: Session = Depends(get_db)) -> UserAuthService:
    return UserAuthService(db)


@router.post("/otp/request", response_model=OtpRequestResponse)
def request_otp(
    payload: OtpRequest,
    request: Request,
    service: UserAuthService = Depends(get_user_auth_service),
) -> OtpRequestResponse:
    result = service.create_login_otp(payload.phone, request.client.host if request.client else None)
    return OtpRequestResponse(phone_masked=build_masked_phone(result.phone_e164), debug_otp=result.debug_otp)


@router.post("/otp/verify", response_model=UserAuthTokenResponse)
def verify_otp(
    payload: OtpVerifyRequest,
    service: UserAuthService = Depends(get_user_auth_service),
) -> UserAuthTokenResponse:
    user, tokens = service.validate_login_otp(
        payload.phone,
        payload.code,
        device_id=payload.device_id,
        device_name=payload.device_name,
    )
    return UserAuthTokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
        token_type=tokens.token_type,
        user=_profile_response(user),
    )


@router.post("/refresh", response_model=RefreshResponse)
def refresh(
    payload: RefreshRequest,
    service: UserAuthService = Depends(get_user_auth_service),
) -> RefreshResponse:
    tokens = service.create_refreshed_tokens(payload.refresh_token)
    return RefreshResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
        token_type=tokens.token_type,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: LogoutRequest,
    service: UserAuthService = Depends(get_user_auth_service),
) -> None:
    service.update_logout(payload.refresh_token)


@router.get("/me", response_model=UserProfileResponse)
def me(
    principal: Principal = Depends(require_principal(())),
    service: UserAuthService = Depends(get_user_auth_service),
) -> UserProfileResponse:
    if principal.auth_type != "user":
        raise AppError("User authentication required.", status_code=403, code="forbidden")
    user = service.get_user_by_subject(principal.subject)
    if user is None:
        raise AppError("User not found.", status_code=401, code="unauthorized")
    return _profile_response(user)


def _profile_response(user) -> UserProfileResponse:
    return UserProfileResponse(
        id=user.id,
        phone_masked=build_masked_phone(user.phone_e164),
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
    )
