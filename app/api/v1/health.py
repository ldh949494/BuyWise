import hmac

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.core.config import settings
from app.core.dependencies import get_readiness_service
from app.schemas.common import HealthResponse, ReadinessResponse
from app.services.readiness_service import ReadinessService


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="buywise-backend")


@router.get("/ready", response_model=ReadinessResponse)
def readiness_check(
    request: Request,
    readiness_service: ReadinessService = Depends(get_readiness_service),
) -> ReadinessResponse | JSONResponse:
    _require_readiness_token(request)
    report = readiness_service.validate_readiness(include_details=False)
    if report["status"] != "ready":
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=report)
    return ReadinessResponse.model_validate(report)


def _require_readiness_token(request: Request) -> None:
    if settings.app_env != "prod":
        return
    configured = settings.readiness_token.strip()
    token = _request_readiness_token(request)
    if not configured or token is None or not hmac.compare_digest(token, configured):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Readiness authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _request_readiness_token(request: Request) -> str | None:
    header_token = request.headers.get("x-readiness-token")
    if header_token:
        return header_token.strip()
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()
