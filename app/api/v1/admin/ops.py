"""Admin closed beta operations endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.admin_auth import AdminPrincipal, require_admin
from app.core.database import get_db
from app.schemas.admin import AdminOpsSummary
from app.services.admin_ops_service import AdminOpsService

router = APIRouter(prefix="/ops")


@router.get("/summary", response_model=AdminOpsSummary)
def get_ops_summary(
    db: Session = Depends(get_db),
    principal: AdminPrincipal = Depends(require_admin),
) -> AdminOpsSummary:
    _ = principal
    return AdminOpsSummary.model_validate(AdminOpsService(db).get_summary())
