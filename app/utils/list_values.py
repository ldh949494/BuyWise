"""List normalization helpers."""

from __future__ import annotations

import json
from typing import Any


def dedupe_strings(values: list[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)
    return result


def coerce_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parsed = parse_json_or_none(value)
        if isinstance(parsed, list):
            return [str(item) for item in parsed if item]
        return [part.strip() for part in value.split(",") if part.strip()]
    if isinstance(value, list):
        return [str(item) for item in value if item]
    return [str(value)]


def parse_json_or_none(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None
