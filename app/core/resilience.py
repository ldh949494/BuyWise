"""Shared resilience policy for external providers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from app.core.config import settings
from app.core.providers import AppError


class ProviderFailureReason(StrEnum):
    CAPACITY = "capacity"
    TIMEOUT = "timeout"
    CONFIGURATION = "configuration_error"
    PROVIDER = "provider_error"


@dataclass(frozen=True)
class ResiliencePolicy:
    operation: str
    timeout_seconds: float

    @property
    def degraded_reason(self) -> str:
        return f"{self.operation}_capacity_limited"


def provider_policy(operation: str) -> ResiliencePolicy:
    return ResiliencePolicy(operation=operation, timeout_seconds=settings.ai_provider_timeout_seconds)


def classify_provider_failure(exc: Exception) -> ProviderFailureReason:
    if isinstance(exc, AppError) and exc.code == "capacity_limited":
        return ProviderFailureReason.CAPACITY
    if isinstance(exc, TimeoutError):
        return ProviderFailureReason.TIMEOUT
    if isinstance(exc, (RuntimeError, ValueError, AppError)) and "configured" in str(exc).lower():
        return ProviderFailureReason.CONFIGURATION
    if _exception_name_contains(exc, "timeout"):
        return ProviderFailureReason.TIMEOUT
    return ProviderFailureReason.PROVIDER


def _exception_name_contains(exc: Exception, text: str) -> bool:
    names: list[str] = []
    current: Any = type(exc)
    while current is not None:
        names.append(current.__name__.lower())
        current = current.__base__
    return any(text in name for name in names)
