"""Structured logging helpers."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from app.core.request_context import get_request_id


REDACTED_VALUE = "[redacted]"
SENSITIVE_FIELD_PARTS = ("password", "token", "secret", "api_key", "authorization")
_LOG_RECORD_FIELDS = set(logging.makeLogRecord({}).__dict__)


def sanitize_log_value(key: str, value: Any) -> Any:
    if _is_sensitive_key(key):
        return REDACTED_VALUE
    if isinstance(value, dict):
        return {str(item_key): sanitize_log_value(str(item_key), item_value) for item_key, item_value in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [sanitize_log_value(key, item) for item in value]
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return str(value)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
            "request_id": get_request_id(),
        }
        for key, value in record.__dict__.items():
            if key not in _LOG_RECORD_FIELDS and key not in payload:
                payload[key] = sanitize_log_value(key, value)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower()
    return any(part in normalized for part in SENSITIVE_FIELD_PARTS)
