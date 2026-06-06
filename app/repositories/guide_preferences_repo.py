"""Repository for user guide preferences."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user_guide_preferences import UserGuidePreferences


class GuidePreferencesRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_user_id(self, user_id: int) -> UserGuidePreferences | None:
        statement = select(UserGuidePreferences).where(UserGuidePreferences.user_id == user_id)
        return self.db.scalar(statement)

    def update_preferences(
        self,
        user_id: int,
        *,
        budget_policy: str,
        presentation_style: str,
        preferences_json: dict[str, Any],
        now: datetime,
    ) -> UserGuidePreferences:
        preferences = self.get_by_user_id(user_id)
        if preferences is None:
            preferences = UserGuidePreferences(user_id=user_id, created_at=now)
        preferences.budget_policy = budget_policy
        preferences.presentation_style = presentation_style
        preferences.preferences_json = preferences_json
        preferences.updated_at = now
        self.db.add(preferences)
        self.db.flush()
        return preferences

    def delete_by_user_id(self, user_id: int) -> bool:
        preferences = self.get_by_user_id(user_id)
        if preferences is None:
            return False
        self.db.delete(preferences)
        self.db.flush()
        return True
