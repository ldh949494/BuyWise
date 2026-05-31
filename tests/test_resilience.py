import pytest

from app.core.exceptions import AppError
from app.core.resilience import (
    ProviderFailureReason,
    ResiliencePolicy,
    classify_provider_failure,
    provider_policy,
    reset_resilience_state,
    run_provider_call,
    run_provider_call_async,
)


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


def test_run_provider_call_retries_provider_failures_and_records_metrics(monkeypatch) -> None:
    reset_resilience_state()
    failures = []
    attempts = []

    monkeypatch.setattr(
        "app.core.resilience.count_provider_failure",
        lambda provider, operation, reason: failures.append((provider, operation, reason)),
    )

    def flaky_call():
        attempts.append("called")
        if len(attempts) == 1:
            raise RuntimeError("temporary remote failure")
        return "ok"

    result = run_provider_call(
        ResiliencePolicy(
            provider="cos",
            operation="upload_fileobj",
            timeout_seconds=1,
            max_attempts=2,
            retry_backoff_seconds=0,
        ),
        flaky_call,
    )

    assert result == "ok"
    assert attempts == ["called", "called"]
    assert failures == [("cos", "upload_fileobj", "provider_error")]


def test_run_provider_call_opens_circuit_after_repeated_provider_failures(monkeypatch) -> None:
    reset_resilience_state()
    monkeypatch.setattr("app.core.resilience.count_provider_failure", lambda provider, operation, reason: None)
    policy = ResiliencePolicy(
        provider="chroma",
        operation="query",
        timeout_seconds=1,
        max_attempts=1,
        circuit_failure_threshold=1,
        circuit_reset_seconds=60,
    )

    with pytest.raises(RuntimeError):
        run_provider_call(policy, lambda: (_ for _ in ()).throw(RuntimeError("remote failed")))

    with pytest.raises(AppError) as exc_info:
        run_provider_call(policy, lambda: "not-called")

    assert exc_info.value.code == "provider_circuit_open"


@pytest.mark.anyio
async def test_run_provider_call_async_does_not_retry_capacity_failures(monkeypatch) -> None:
    reset_resilience_state()
    failures = []
    calls = []
    monkeypatch.setattr(
        "app.core.resilience.count_provider_failure",
        lambda provider, operation, reason: failures.append((provider, operation, reason)),
    )

    async def capacity_call():
        calls.append("called")
        raise AppError("capacity", status_code=503, code="capacity_limited")

    with pytest.raises(AppError):
        await run_provider_call_async(
            ResiliencePolicy(
                provider="llm",
                operation="chat",
                timeout_seconds=1,
                max_attempts=3,
                retry_backoff_seconds=0,
            ),
            capacity_call,
        )

    assert calls == ["called"]
    assert failures == [("llm", "chat", "capacity")]
