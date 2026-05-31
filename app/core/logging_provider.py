"""Logging provider implementation."""

from __future__ import annotations

import logging
import sys
from logging.config import dictConfig
from typing import Any, Literal

from app.core.config import settings
from app.core.logging_utils import JsonFormatter

ProviderName = Literal["auth", "telemetry", "logging", "errors", "middleware"]


class LoggingProvider:
    name: ProviderName = "logging"

    def configure(self, level: str | None = None) -> None:
        log_level = (level or settings.log_level).upper()
        dictConfig(self._config(log_level))

    def get_logger(self, name: str) -> logging.Logger:
        return logging.getLogger(name)

    def _config(self, log_level: str) -> dict[str, Any]:
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"json": {"()": JsonFormatter}},
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "stream": sys.stdout,
                    "formatter": "json",
                },
            },
            "root": {"handlers": ["default"], "level": log_level},
            "loggers": {
                name: {"handlers": ["default"], "level": log_level, "propagate": False}
                for name in ["uvicorn", "uvicorn.error", "uvicorn.access"]
            },
        }
