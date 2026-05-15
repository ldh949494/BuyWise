"""Unified providers for cross-cutting concerns."""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from logging.config import dictConfig
from typing import Any, Literal, Protocol, TypeAlias, cast

from fastapi import FastAPI

try:
    from prometheus_fastapi_instrumentator import Instrumentator
except ImportError:  # pragma: no cover - dependency is installed in normal runtime.
    Instrumentator = None


ProviderName: TypeAlias = Literal["auth", "telemetry", "logging", "errors"]


class Provider(Protocol):
    name: ProviderName


@dataclass(frozen=True)
class Principal:
    subject: str
    scopes: tuple[str, ...] = ()


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


class LoggingProvider:
    name: ProviderName = "logging"

    def configure(self) -> None:
        dictConfig(
            {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "json": {
                        "()": JsonFormatter,
                    },
                },
                "handlers": {
                    "default": {
                        "class": "logging.StreamHandler",
                        "stream": sys.stdout,
                        "formatter": "json",
                    },
                },
                "root": {
                    "handlers": ["default"],
                    "level": "INFO",
                },
                "loggers": {
                    "uvicorn": {
                        "handlers": ["default"],
                        "level": "INFO",
                        "propagate": False,
                    },
                    "uvicorn.error": {
                        "handlers": ["default"],
                        "level": "INFO",
                        "propagate": False,
                    },
                    "uvicorn.access": {
                        "handlers": ["default"],
                        "level": "INFO",
                        "propagate": False,
                    },
                },
            }
        )

    def get_logger(self, name: str) -> logging.Logger:
        return logging.getLogger(name)


class TelemetryProvider:
    name: ProviderName = "telemetry"

    def instrument(self, app: FastAPI) -> None:
        if Instrumentator is not None:
            Instrumentator().instrument(app).expose(app)


class ErrorProvider:
    name: ProviderName = "errors"

    def register_exception_handlers(self, app: FastAPI) -> None:
        _ = app


class AuthProvider:
    name: ProviderName = "auth"

    def get_current_principal(self) -> Principal | None:
        return None


_PROVIDERS: dict[ProviderName, Provider] = {
    "auth": AuthProvider(),
    "telemetry": TelemetryProvider(),
    "logging": LoggingProvider(),
    "errors": ErrorProvider(),
}


def get_provider(name: ProviderName) -> Any:
    return _PROVIDERS[name]


def get_logging_provider() -> LoggingProvider:
    return cast(LoggingProvider, get_provider("logging"))


def get_telemetry_provider() -> TelemetryProvider:
    return cast(TelemetryProvider, get_provider("telemetry"))


def get_error_provider() -> ErrorProvider:
    return cast(ErrorProvider, get_provider("errors"))


def get_auth_provider() -> AuthProvider:
    return cast(AuthProvider, get_provider("auth"))
