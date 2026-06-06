"""Guide preferences API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.providers import AppError, Principal, require_principal
from app.schemas.guide_preferences import GuidePreferencesResponse, GuidePreferencesUpdate
from app.services.guide_preferences_service import GuidePreferencesService

router = APIRouter(prefix="/guide/preferences")


@router.get("", response_model=GuidePreferencesResponse)
def get_guide_preferences(
    principal: Principal = Depends(require_principal(())),
    db: Session = Depends(get_db),
) -> GuidePreferencesResponse:
    return GuidePreferencesService(db).get_response(_user_id(principal))


@router.put("", response_model=GuidePreferencesResponse)
def save_guide_preferences(
    payload: GuidePreferencesUpdate,
    principal: Principal = Depends(require_principal(())),
    db: Session = Depends(get_db),
) -> GuidePreferencesResponse:
    return GuidePreferencesService(db).update_preferences(_user_id(principal), payload)


@router.delete("", status_code=204)
def delete_guide_preferences(
    principal: Principal = Depends(require_principal(())),
    db: Session = Depends(get_db),
) -> None:
    GuidePreferencesService(db).delete(_user_id(principal))


def _user_id(principal: Principal) -> int:
    if principal.auth_type != "user" or not principal.subject.startswith("user:"):
        raise AppError("User authentication required.", status_code=403, code="forbidden")
    try:
        return int(principal.subject.split(":", 1)[1])
    except ValueError as exc:
        raise AppError("Invalid user authentication.", status_code=401, code="unauthorized") from exc
