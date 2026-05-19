"""Evaluate RAG retrieval quality against a small shopping-needs dataset."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai.rag_pipeline import RAGPipeline
from app.core.database import Base
from app.scripts.seed_products import (
    ANDROID_CONTRACT_PRODUCTS,
    seed_android_contract_products,
)
from app.schemas.chat import StructuredNeed

DEFAULT_DATASET_PATH = Path(__file__).resolve().parents[2] / "data" / "rag_eval" / "shopping_needs.jsonl"


class EmptyProductStore:
    """Deterministic baseline store that exercises database fallback retrieval."""

    def search(self, query: str, top_k: int = 10) -> list[dict[str, Any]]:
        return []


@dataclass(frozen=True)
class RagEvalCase:
    id: str
    query: str
    structured_need: dict[str, Any]
    expected_product_ids: list[int]
    ideal_top_id: int
    ranking_reason: str
    failure_notes: list[str]
    tags: list[str]


def load_eval_cases(dataset_path: str | Path = DEFAULT_DATASET_PATH) -> list[RagEvalCase]:
    path = Path(dataset_path)
    cases = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            data = json.loads(line)
            cases.append(_build_case(data, line_number))
    return cases


async def evaluate_cases(
    cases: list[RagEvalCase],
    *,
    top_k: int = 5,
    db: Session | None = None,
    pipeline: RAGPipeline | None = None,
) -> dict[str, Any]:
    owns_db = db is None
    if db is None:
        session_factory = _make_session_factory()
        db = session_factory()
        seed_android_contract_products(db)

    pipeline = pipeline or RAGPipeline(product_store=EmptyProductStore())
    try:
        rows = []
        for case in cases:
            results = await pipeline.search_products(_structured_need(case), db, top_k=top_k)
            retrieved_ids = [product.id for product in results]
            rows.append(_score_case(case, retrieved_ids))
        return _summarize(rows, top_k)
    finally:
        if owns_db:
            db.close()


async def evaluate_dataset(
    dataset_path: str | Path = DEFAULT_DATASET_PATH,
    *,
    top_k: int = 5,
) -> dict[str, Any]:
    return await evaluate_cases(load_eval_cases(dataset_path), top_k=top_k)


def known_seed_product_ids() -> set[int]:
    return {int(product["id"]) for product in ANDROID_CONTRACT_PRODUCTS}


def main() -> None:
    args = _parse_args()
    import asyncio

    report = asyncio.run(evaluate_dataset(args.dataset, top_k=args.top_k))
    print(_format_report(report))
    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _build_case(data: dict[str, Any], line_number: int) -> RagEvalCase:
    required = [
        "id",
        "query",
        "structured_need",
        "expected_product_ids",
        "ideal_top_id",
        "ranking_reason",
        "failure_notes",
        "tags",
    ]
    missing = [field for field in required if field not in data]
    if missing:
        raise ValueError(f"RAG eval case line {line_number} is missing fields: {missing}")
    return RagEvalCase(
        id=str(data["id"]),
        query=str(data["query"]),
        structured_need=dict(data["structured_need"]),
        expected_product_ids=[int(product_id) for product_id in data["expected_product_ids"]],
        ideal_top_id=int(data["ideal_top_id"]),
        ranking_reason=str(data["ranking_reason"]),
        failure_notes=[str(note) for note in data["failure_notes"]],
        tags=[str(tag) for tag in data["tags"]],
    )


def _make_session_factory():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _structured_need(case: RagEvalCase) -> StructuredNeed:
    return StructuredNeed(**case.structured_need)


def _score_case(case: RagEvalCase, retrieved_ids: list[int]) -> dict[str, Any]:
    expected = set(case.expected_product_ids)
    hits = [product_id for product_id in retrieved_ids if product_id in expected]
    top_id = retrieved_ids[0] if retrieved_ids else None
    reciprocal_rank = _reciprocal_rank(retrieved_ids, expected)
    return {
        "id": case.id,
        "query": case.query,
        "expected_product_ids": case.expected_product_ids,
        "ideal_top_id": case.ideal_top_id,
        "retrieved_product_ids": retrieved_ids,
        "recall": len(set(hits)) / len(expected) if expected else 0.0,
        "top1_match": top_id == case.ideal_top_id,
        "mrr": reciprocal_rank,
        "ranking_reason": case.ranking_reason,
        "failure_notes": case.failure_notes,
    }


def _reciprocal_rank(retrieved_ids: list[int], expected: set[int]) -> float:
    for index, product_id in enumerate(retrieved_ids, start=1):
        if product_id in expected:
            return 1 / index
    return 0.0


def _summarize(rows: list[dict[str, Any]], top_k: int) -> dict[str, Any]:
    total = len(rows)
    failures = [
        row
        for row in rows
        if row["recall"] < 1.0 or not row["top1_match"]
    ]
    return {
        "case_count": total,
        "top_k": top_k,
        "metrics": {
            f"recall@{top_k}": _average(row["recall"] for row in rows),
            "top1_accuracy": _average(1.0 if row["top1_match"] else 0.0 for row in rows),
            f"mrr@{top_k}": _average(row["mrr"] for row in rows),
        },
        "failures": failures,
        "cases": rows,
    }


def _average(values: Any) -> float:
    values = list(values)
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


def _format_report(report: dict[str, Any]) -> str:
    metrics = report["metrics"]
    lines = [
        "RAG evaluation report",
        f"cases: {report['case_count']}",
        f"top_k: {report['top_k']}",
    ]
    lines.extend(f"{name}: {value:.4f}" for name, value in metrics.items())
    lines.append(f"failures: {len(report['failures'])}")
    for failure in report["failures"][:10]:
        lines.append(
            "- "
            f"{failure['id']}: expected={failure['expected_product_ids']} "
            f"retrieved={failure['retrieved_product_ids']} "
            f"top1={failure['top1_match']}"
        )
    return "\n".join(lines)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate BuyWise RAG retrieval quality.")
    parser.add_argument(
        "--dataset",
        default=str(DEFAULT_DATASET_PATH),
        help="Path to the JSONL RAG evaluation dataset.",
    )
    parser.add_argument("--top-k", type=int, default=5, help="Number of products to retrieve per case.")
    parser.add_argument("--output-json", help="Optional path for a JSON report.")
    return parser.parse_args()


if __name__ == "__main__":
    main()
