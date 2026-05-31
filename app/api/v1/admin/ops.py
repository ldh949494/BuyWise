"""Admin closed beta operations endpoints."""

from fastapi import APIRouter, Depends

from app.core.admin_auth import AdminPrincipal, require_admin
from app.core.dependencies import get_admin_ops_service
from app.schemas.admin import AdminOpsSummary
from app.services.admin_ops_service import AdminOpsService

router = APIRouter(prefix="/ops")


@router.get("/summary", response_model=AdminOpsSummary)
def get_ops_summary(
    service: AdminOpsService = Depends(get_admin_ops_service),
    principal: AdminPrincipal = Depends(require_admin),
) -> AdminOpsSummary:
    _ = principal
    return AdminOpsSummary.model_validate(service.get_summary())
