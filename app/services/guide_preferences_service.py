"""Guide preference management and application service."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.guide_preferences_repo import GuidePreferencesRepository
from app.schemas.guide_preferences import (
    AppliedPreferenceConstraint,
    AppliedPreferences,
    BudgetRange,
    GuidePreferences,
    GuidePreferencesResponse,
    GuidePreferencesUpdate,
    preferences_json,
)


class GuidePreferencesService:
    CATEGORY_ALIASES = {
        "电脑": {"电脑", "主机", "笔记本"},
        "显示器": {"显示器", "屏幕"},
        "机械键盘": {"机械键盘", "键盘"},
        "鼠标": {"鼠标"},
        "蓝牙耳机": {"蓝牙耳机", "耳机"},
        "桌面配件": {"桌面配件", "台灯", "支架", "拓展坞", "插排"},
    }

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = GuidePreferencesRepository(db)

    def get_response(self, user_id: int) -> GuidePreferencesResponse:
        saved = self.repo.get_by_user_id(user_id)
        if saved is None:
            return GuidePreferencesResponse()
        preferences = self._from_model(saved)
        return GuidePreferencesResponse(**preferences.model_dump(mode="json"), has_saved_preferences=True)

    def update_preferences(self, user_id: int, update: GuidePreferencesUpdate) -> GuidePreferencesResponse:
        now = datetime.utcnow()
        saved = self.repo.update_preferences(
            user_id,
            budget_policy=update.budget_policy,
            presentation_style=update.presentation_style,
            preferences_json=preferences_json(update),
            now=now,
        )
        self.db.commit()
        preferences = self._from_model(saved)
        return GuidePreferencesResponse(**preferences.model_dump(mode="json"), has_saved_preferences=True)

    def delete(self, user_id: int) -> None:
        self.repo.delete_by_user_id(user_id)
        self.db.commit()

    def build_applied_preferences(
        self,
        need: Any,
        *,
        user_id: int | None,
        temporary_preferences: GuidePreferences | None,
        ignore_saved_preferences: bool,
    ) -> AppliedPreferences:
        saved = self._saved_preferences(user_id, ignore_saved_preferences)
        effective = self._merge_preferences(saved, temporary_preferences)
        applied = self._applied_summary(saved, effective, ignore_saved_preferences)
        if effective is None:
            return applied
        self._set_value(need, "budget_policy", effective.budget_policy)
        self._set_value(need, "budget_flex_rate", self._budget_flex_rate(effective.budget_policy))
        self._set_value(need, "presentation_style", effective.presentation_style)
        self._apply_budget(need, effective, applied)
        self._apply_tags(need, effective, applied)
        self._apply_owned_categories(need, effective, applied)
        return applied

    def _saved_preferences(self, user_id: int | None, ignore_saved_preferences: bool) -> GuidePreferences | None:
        if user_id is None or ignore_saved_preferences:
            return None
        saved = self.repo.get_by_user_id(user_id)
        if saved is None:
            return None
        return self._from_model(saved)

    def _merge_preferences(
        self,
        saved: GuidePreferences | None,
        temporary: GuidePreferences | None,
    ) -> GuidePreferences | None:
        if saved is None:
            return temporary
        if temporary is None:
            return saved
        saved_data = saved.model_dump(mode="json")
        temp_data = temporary.model_dump(mode="json")
        saved_data.update({key: value for key, value in temp_data.items() if value not in (None, [], {}, "")})
        return GuidePreferences.model_validate(saved_data)

    def _applied_summary(
        self,
        saved: GuidePreferences | None,
        effective: GuidePreferences | None,
        ignore_saved_preferences: bool,
    ) -> AppliedPreferences:
        return AppliedPreferences(
            used_saved_preferences=saved is not None and not ignore_saved_preferences,
            ignored_saved_preferences=ignore_saved_preferences,
            budget_policy=effective.budget_policy if effective else None,
            presentation_style=effective.presentation_style if effective else None,
        )

    def _apply_budget(self, need: Any, preferences: GuidePreferences, applied: AppliedPreferences) -> None:
        budget = self._budget_for_need(need, preferences)
        if budget is not None and self._get_value(need, "budget_max") is None and budget.max is not None:
            self._set_value(need, "budget_max", budget.max)
            applied.constraints.append(
                AppliedPreferenceConstraint(
                    type="budget",
                    key="budget_max",
                    label=f"常用预算 {int(budget.max)} 元以内",
                    effect="本次未提供预算，使用导购偏好的预算上限",
                )
            )
        if preferences.budget_policy == "slightly_flexible":
            applied.summary.append("允许小幅超预算")
        elif preferences.budget_policy == "strict":
            applied.summary.append("严格预算")
        elif preferences.budget_policy == "quality_first":
            applied.summary.append("品质优先")

    def _apply_tags(self, need: Any, preferences: GuidePreferences, applied: AppliedPreferences) -> None:
        current_preferences = self._string_list(self._get_value(need, "preferences"))
        current_avoid = self._string_list(self._get_value(need, "avoid"))
        merged_preferences = self._merge_string_lists(current_preferences, preferences.priority_tags)
        merged_avoid = self._merge_string_lists(current_avoid, preferences.excluded_tags + preferences.excluded_brands)
        self._set_value(need, "preferences", merged_preferences)
        self._set_value(need, "avoid", merged_avoid)
        applied.summary.extend(preferences.priority_tags[:3])
        for tag in preferences.excluded_tags[:3]:
            applied.constraints.append(
                AppliedPreferenceConstraint(type="excluded_tag", key=tag, label=f"排除 {tag}", effect="推荐排序会降低命中避雷项的商品")
            )
        for brand in preferences.excluded_brands[:3]:
            applied.constraints.append(
                AppliedPreferenceConstraint(type="excluded_brand", key=brand, label=f"排除 {brand}", effect="推荐排序会降低命中排除品牌的商品")
            )

    def _apply_owned_categories(self, need: Any, preferences: GuidePreferences, applied: AppliedPreferences) -> None:
        if not preferences.owned_categories:
            return
        existing = self._string_list(self._get_value(need, "avoid"))
        self._set_value(need, "avoid", self._merge_string_lists(existing, preferences.owned_categories))
        self._set_value(need, "owned_categories", preferences.owned_categories)
        for category in preferences.owned_categories[:3]:
            applied.summary.append(f"已有{category}")
            applied.constraints.append(
                AppliedPreferenceConstraint(
                    type="owned_category",
                    key=category,
                    label=f"已有{category}",
                    effect="整套方案不再把该品类作为必选项",
                )
            )

    def _budget_for_need(self, need: Any, preferences: GuidePreferences) -> BudgetRange | None:
        if self._get_value(need, "intent") in {"bundle_recommend", "场景化组合推荐"}:
            return preferences.bundle_budget_range
        category = str(self._get_value(need, "category") or "")
        if not category:
            return None
        for key, budget in preferences.single_item_budgets.items():
            aliases = self.CATEGORY_ALIASES.get(key, {key})
            if category in aliases or any(alias in category for alias in aliases):
                return budget
        return None

    def _budget_flex_rate(self, budget_policy: str) -> float:
        if budget_policy == "slightly_flexible":
            return 0.1
        if budget_policy == "quality_first":
            return 0.2
        return 0.0

    def _from_model(self, saved: Any) -> GuidePreferences:
        data = dict(saved.preferences_json or {})
        data["budget_policy"] = saved.budget_policy
        data["presentation_style"] = saved.presentation_style
        return GuidePreferences.model_validate(data)

    def _merge_string_lists(self, first: list[str], second: list[str]) -> list[str]:
        result = []
        seen = set()
        for value in first + second:
            clean = value.strip()
            if not clean or clean in seen:
                continue
            seen.add(clean)
            result.append(clean)
        return result

    def _string_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    def _get_value(self, source: Any, key: str) -> Any:
        if isinstance(source, dict):
            return source.get(key)
        return getattr(source, key, None)

    def _set_value(self, target: Any, key: str, value: Any) -> None:
        if isinstance(target, dict):
            target[key] = value
            return
        setattr(target, key, value)
