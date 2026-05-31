from app.core.exceptions import AppError
from app.core.resilience import ProviderFailureReason, classify_provider_failure, provider_policy


class ProviderTimeoutError(Exception):
    pass


def test_provider_policy_uses_configured_timeout(monkeypatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "ai_provider_timeout_seconds", 12.5)

    policy = provider_policy("llm")

    assert policy.timeout_seconds == 12.5
    assert policy.degraded_reason == "llm_capacity_limited"


def test_classify_provider_failure_reasons() -> None:
    assert classify_provider_failure(
        AppError("capacity", status_code=503, code="capacity_limited")
    ) == ProviderFailureReason.CAPACITY
    assert classify_provider_failure(TimeoutError("timeout")) == ProviderFailureReason.TIMEOUT
    assert classify_provider_failure(ProviderTimeoutError("timeout")) == ProviderFailureReason.TIMEOUT
    assert classify_provider_failure(RuntimeError("provider is not configured")) == ProviderFailureReason.CONFIGURATION
    assert classify_provider_failure(RuntimeError("remote failed")) == ProviderFailureReason.PROVIDER
