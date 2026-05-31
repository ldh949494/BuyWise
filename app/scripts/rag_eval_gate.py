"""Release gate for RAG evaluation quality thresholds."""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.scripts.evaluate_rag import evaluate_dataset


@dataclass(frozen=True)
class RagEvalThresholds:
    min_recall: float
    min_top1: float
    min_mrr: float
    max_fallback_rate: float
    max_empty_result_rate: float


async def evaluate_rag_gate(
    *,
    profile: str,
    retrieval: str,
    top_k: int,
    thresholds: RagEvalThresholds,
) -> dict[str, Any]:
    report = await evaluate_dataset(top_k=top_k, profile=profile, retrieval=retrieval)
    report = enrich_report(report)
    failures = check_thresholds(report, thresholds)
    report["thresholds"] = {
        "min_recall": thresholds.min_recall,
        "min_top1": thresholds.min_top1,
        "min_mrr": thresholds.min_mrr,
        "max_fallback_rate": thresholds.max_fallback_rate,
        "max_empty_result_rate": thresholds.max_empty_result_rate,
    }
    report["gate_passed"] = not failures
    report["gate_failures"] = failures
    return report


def enrich_report(report: dict[str, Any]) -> dict[str, Any]:
    metrics = dict(report["metrics"])
    cases = report.get("cases", [])
    metrics["fallback_rate"] = _rate(_uses_fallback(case) for case in cases)
    metrics["empty_result_rate"] = _rate(_is_empty_result(case) for case in cases)
    return {**report, "metrics": metrics}


def check_thresholds(report: dict[str, Any], thresholds: RagEvalThresholds) -> list[str]:
    metrics = report["metrics"]
    top_k = report["top_k"]
    checks = [
        (metrics[f"recall@{top_k}"] >= thresholds.min_recall, f"recall@{top_k} below {thresholds.min_recall}"),
        (metrics["top1_accuracy"] >= thresholds.min_top1, f"top1_accuracy below {thresholds.min_top1}"),
        (metrics[f"mrr@{top_k}"] >= thresholds.min_mrr, f"mrr@{top_k} below {thresholds.min_mrr}"),
        (metrics["fallback_rate"] <= thresholds.max_fallback_rate, "fallback_rate above threshold"),
        (metrics["empty_result_rate"] <= thresholds.max_empty_result_rate, "empty_result_rate above threshold"),
    ]
    return [message for passed, message in checks if not passed]


def format_gate_report(report: dict[str, Any]) -> str:
    metrics = report["metrics"]
    lines = [
        "RAG release gate report",
        f"profile: {report['profile']}",
        f"retrieval: {report.get('retrieval', 'fallback')}",
        f"cases: {report['case_count']}",
        f"top_k: {report['top_k']}",
    ]
    lines.extend(f"{name}: {value:.4f}" for name, value in metrics.items())
    lines.append(f"gate_passed: {str(report['gate_passed']).lower()}")
    for failure in report["gate_failures"]:
        lines.append(f"- {failure}")
    return "\n".join(lines)


def main() -> None:
    args = _parse_args()
    thresholds = RagEvalThresholds(
        min_recall=args.min_recall,
        min_top1=args.min_top1,
        min_mrr=args.min_mrr,
        max_fallback_rate=args.max_fallback_rate,
        max_empty_result_rate=args.max_empty_result_rate,
    )
    report = asyncio.run(
        evaluate_rag_gate(profile=args.profile, retrieval=args.retrieval, top_k=args.top_k, thresholds=thresholds)
    )
    report["retrieval"] = args.retrieval
    print(format_gate_report(report))
    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if not report["gate_passed"]:
        raise SystemExit(1)


def _uses_fallback(case: dict[str, Any]) -> bool:
    stage = (case.get("diagnostics") or {}).get("fallback_stage")
    return stage not in (None, "strict", "none")


def _is_empty_result(case: dict[str, Any]) -> bool:
    return not case.get("retrieved_product_ids")


def _rate(values: Any) -> float:
    values = list(values)
    if not values:
        return 0.0
    return round(sum(1 for value in values if value) / len(values), 4)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RAG eval with release quality thresholds.")
    parser.add_argument("--profile", choices=["android-contract", "demo", "beta-fixture"], default="android-contract")
    parser.add_argument("--retrieval", choices=["fallback", "vector"], default="fallback")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--min-recall", type=float, default=0.70)
    parser.add_argument("--min-top1", type=float, default=0.90)
    parser.add_argument("--min-mrr", type=float, default=0.70)
    parser.add_argument("--max-fallback-rate", type=float, default=0.20)
    parser.add_argument("--max-empty-result-rate", type=float, default=0.0)
    parser.add_argument("--output-json")
    return parser.parse_args()


if __name__ == "__main__":
    main()
