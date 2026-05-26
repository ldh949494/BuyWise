"""Business metrics helpers."""

from __future__ import annotations

from prometheus_client import Counter, Histogram


CHAT_LATENCY_SECONDS = Histogram(
    "buywise_chat_latency_seconds",
    "End-to-end chat latency in seconds.",
    labelnames=("mode", "outcome"),
)
LLM_FAILURES_TOTAL = Counter(
    "buywise_llm_failures_total",
    "LLM failure count.",
    labelnames=("operation", "reason"),
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


def observe_chat_latency(mode: str, outcome: str, seconds: float) -> None:
    CHAT_LATENCY_SECONDS.labels(mode=mode, outcome=outcome).observe(seconds)


def count_llm_failure(operation: str, reason: str) -> None:
    LLM_FAILURES_TOTAL.labels(operation=operation, reason=reason).inc()


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
