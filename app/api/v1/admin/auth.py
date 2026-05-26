"""Admin authentication endpoints."""

from fastapi import APIRouter, Depends

from app.core.dependencies import get_admin_auth_service
from app.schemas.admin import AdminLoginRequest, AdminTokenResponse
from app.services.admin_auth_service import AdminAuthService


router = APIRouter(prefix="/auth")


@router.post("/login", response_model=AdminTokenResponse)
def login_admin(
    credentials: AdminLoginRequest,
    service: AdminAuthService = Depends(get_admin_auth_service),
) -> AdminTokenResponse:
    user = service.get_authenticated_admin(credentials.username, credentials.password)
    access_token, expires_in = service.create_access_token(user)
    return AdminTokenResponse(access_token=access_token, expires_in=expires_in)
