"""Business metrics helpers."""

from __future__ import annotations

from prometheus_client import Counter, Histogram


CHAT_LATENCY_SECONDS = Histogram(
    "buywise_chat_latency_seconds",
    "End-to-end chat latency in seconds.",
    labelnames=("mode", "outcome"),
)
CHAT_STREAM_FIRST_PRODUCTS_LATENCY_SECONDS = Histogram(
    "buywise_chat_stream_first_products_latency_seconds",
    "Latency until the first chat stream products event is emitted.",
    labelnames=("path",),
)
CHAT_STREAM_DONE_LATENCY_SECONDS = Histogram(
    "buywise_chat_stream_done_latency_seconds",
    "Latency until the chat stream done event is emitted.",
    labelnames=("path",),
)
LLM_FAILURES_TOTAL = Counter(
    "buywise_llm_failures_total",
    "LLM failure count.",
    labelnames=("operation", "reason"),
)
PROVIDER_FAILURES_TOTAL = Counter(
    "buywise_provider_failures_total",
    "External provider failure count.",
    labelnames=("provider", "operation", "reason"),
)
RAG_FALLBACK_TOTAL = Counter(
    "buywise_rag_fallback_total",
    "RAG fallback count.",
    labelnames=("entrypoint", "stage"),
)
RAG_EMPTY_RESULTS_TOTAL = Counter(
    "buywise_rag_empty_results_total",
    "RAG empty result count.",
    labelnames=("entrypoint", "source"),
)
UPLOAD_FAILURES_TOTAL = Counter(
    "buywise_upload_failures_total",
    "Upload failure count.",
    labelnames=("reason",),
)
ORDER_CREATED_TOTAL = Counter(
    "buywise_order_created_total",
    "Order created count.",
    labelnames=("source",),
)
FEEDBACK_PROMPTED_TOTAL = Counter(
    "buywise_feedback_prompted_total",
    "Feedback prompted count.",
    labelnames=("source",),
)
FEEDBACK_SUBMIT_SUCCESS_TOTAL = Counter(
    "buywise_feedback_submit_success_total",
    "Feedback submit success count.",
    labelnames=("source",),
)
FEEDBACK_SUBMIT_FAILURES_TOTAL = Counter(
    "buywise_feedback_submit_failures_total",
    "Feedback submit failure count.",
    labelnames=("reason",),
)
AGENT_ACTION_TOTAL = Counter(
    "buywise_agent_action_total",
    "Agent action count.",
    labelnames=("action", "status"),
)
AGENT_SAFETY_BLOCK_TOTAL = Counter(
    "buywise_agent_safety_block_total",
    "Agent safety block count.",
    labelnames=("stage", "reason"),
)
CHAT_SESSION_FORBIDDEN_TOTAL = Counter(
    "buywise_chat_session_forbidden_total",
    "Chat session authorization failure count.",
    labelnames=("reason",),
)
CHAT_RATE_LIMITED_TOTAL = Counter(
    "buywise_chat_rate_limited_total",
    "Chat rate limit count.",
    labelnames=("scope",),
)


def observe_chat_latency(mode: str, outcome: str, seconds: float) -> None:
    CHAT_LATENCY_SECONDS.labels(mode=mode, outcome=outcome).observe(seconds)


def observe_chat_stream_first_products_latency(path: str, seconds: float) -> None:
    CHAT_STREAM_FIRST_PRODUCTS_LATENCY_SECONDS.labels(path=path).observe(seconds)


def observe_chat_stream_done_latency(path: str, seconds: float) -> None:
    CHAT_STREAM_DONE_LATENCY_SECONDS.labels(path=path).observe(seconds)


def count_llm_failure(operation: str, reason: str) -> None:
    LLM_FAILURES_TOTAL.labels(operation=operation, reason=reason).inc()


def count_provider_failure(provider: str, operation: str, reason: str) -> None:
    PROVIDER_FAILURES_TOTAL.labels(provider=provider, operation=operation, reason=reason).inc()


def count_rag_fallback(entrypoint: str, stage: str) -> None:
    RAG_FALLBACK_TOTAL.labels(entrypoint=entrypoint, stage=stage).inc()


def count_rag_empty_results(entrypoint: str, source: str) -> None:
    RAG_EMPTY_RESULTS_TOTAL.labels(entrypoint=entrypoint, source=source).inc()


def count_upload_failure(reason: str) -> None:
    UPLOAD_FAILURES_TOTAL.labels(reason=reason).inc()


def count_order_created(source: str) -> None:
    ORDER_CREATED_TOTAL.labels(source=source).inc()


def count_feedback_prompted(source: str, amount: int = 1) -> None:
    FEEDBACK_PROMPTED_TOTAL.labels(source=source).inc(amount)


def count_feedback_submit_success(source: str) -> None:
    FEEDBACK_SUBMIT_SUCCESS_TOTAL.labels(source=source).inc()


def count_feedback_submit_failure(reason: str) -> None:
    FEEDBACK_SUBMIT_FAILURES_TOTAL.labels(reason=reason).inc()


def count_agent_action(action: str, status: str) -> None:
    AGENT_ACTION_TOTAL.labels(action=action, status=status).inc()


def count_agent_safety_block(stage: str, reason: str) -> None:
    AGENT_SAFETY_BLOCK_TOTAL.labels(stage=stage, reason=reason).inc()


def count_chat_session_forbidden(reason: str) -> None:
    CHAT_SESSION_FORBIDDEN_TOTAL.labels(reason=reason).inc()


def count_chat_rate_limited(scope: str) -> None:
    CHAT_RATE_LIMITED_TOTAL.labels(scope=scope).inc()
