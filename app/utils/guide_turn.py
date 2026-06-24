"""Shared helpers for guide turn metadata."""

from __future__ import annotations

from typing import Any


def build_turn_extra(context: dict[str, Any]) -> dict[str, Any]:
    extra: dict[str, Any] = {}
    if context.get("turn_type"):
        extra["turn_type"] = context["turn_type"]
    if context.get("turn_reason"):
        extra["turn_reason"] = context["turn_reason"]
    return extra


def list_string_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return [str(value)] if str(value) else []
