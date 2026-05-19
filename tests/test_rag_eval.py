import pytest

from app.scripts.evaluate_rag import (
    evaluate_dataset,
    known_seed_product_ids,
    load_eval_cases,
)


def test_rag_eval_dataset_is_small_complete_and_bound_to_seed_products() -> None:
    cases = load_eval_cases()
    seed_ids = known_seed_product_ids()

    assert 20 <= len(cases) <= 50
    case_ids = [case.id for case in cases]
    assert len(case_ids) == len(set(case_ids))

    for case in cases:
        assert case.query
        assert case.structured_need["intent"]
        assert case.expected_product_ids
        assert case.ideal_top_id in case.expected_product_ids
        assert set(case.expected_product_ids).issubset(seed_ids)
        assert case.ranking_reason
        assert isinstance(case.failure_notes, list)
        assert case.tags


@pytest.mark.anyio
async def test_rag_eval_runner_reports_metrics_with_light_quality_gate() -> None:
    report = await evaluate_dataset(top_k=5)

    assert report["case_count"] == len(load_eval_cases())
    assert report["top_k"] == 5
    assert report["metrics"]["recall@5"] >= 0.70
    assert report["metrics"]["top1_accuracy"] >= 0.40
    assert "mrr@5" in report["metrics"]
    assert isinstance(report["failures"], list)
