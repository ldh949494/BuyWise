"""Telemetry provider implementation."""

from __future__ import annotations

from typing import Literal

from fastapi import FastAPI

try:
    from prometheus_fastapi_instrumentator import Instrumentator
except ImportError:  # pragma: no cover - dependency is installed in normal runtime.
    Instrumentator = None

ProviderName = Literal["auth", "telemetry", "logging", "errors", "middleware"]


class TelemetryProvider:
    name: ProviderName = "telemetry"

    def instrument(self, app: FastAPI) -> None:
        if Instrumentator is not None:
            Instrumentator().instrument(app).expose(app)
