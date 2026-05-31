import pytest

from app.scripts.evaluate_rag import (
    dataset_path_for_profile,
    evaluate_dataset,
    known_seed_product_ids,
    load_eval_cases,
)
from app.scripts.rag_eval_gate import RagEvalThresholds, check_thresholds, enrich_report, evaluate_rag_gate


def test_rag_eval_dataset_is_small_complete_and_bound_to_seed_products() -> None:
    cases = load_eval_cases(dataset_path_for_profile("android-contract"))
    seed_ids = known_seed_product_ids("android-contract")

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
    report = await evaluate_dataset(top_k=5, profile="android-contract")

    assert report["profile"] == "android-contract"
    assert report["case_count"] == len(load_eval_cases(dataset_path_for_profile("android-contract")))
    assert report["top_k"] == 5
    assert report["metrics"]["recall@5"] >= 0.70
    assert report["metrics"]["top1_accuracy"] >= 0.90
    assert "mrr@5" in report["metrics"]
    assert isinstance(report["failures"], list)


def test_demo_rag_eval_dataset_is_bound_to_demo_products() -> None:
    cases = load_eval_cases(dataset_path_for_profile("demo"))
    seed_ids = known_seed_product_ids("demo")

    assert 5 <= len(cases) <= 50
    for case in cases:
        assert "demo" in case.tags
        assert set(case.expected_product_ids).issubset(seed_ids)
        assert case.ideal_top_id in case.expected_product_ids


@pytest.mark.anyio
async def test_demo_rag_eval_runner_reports_profile_metrics() -> None:
    report = await evaluate_dataset(top_k=5, profile="demo")

    assert report["profile"] == "demo"
    assert report["case_count"] == len(load_eval_cases(dataset_path_for_profile("demo")))
    assert report["metrics"]["recall@5"] >= 0.70
    assert report["metrics"]["top1_accuracy"] >= 0.90
    assert "mrr@5" in report["metrics"]


def test_beta_fixture_rag_eval_dataset_is_bound_to_fixture_products() -> None:
    cases = load_eval_cases(dataset_path_for_profile("beta-fixture"))
    seed_ids = known_seed_product_ids("beta-fixture")

    assert 5 <= len(cases) <= 50
    for case in cases:
        assert "beta" in case.tags
        assert set(case.expected_product_ids).issubset(seed_ids)
        assert case.ideal_top_id in case.expected_product_ids


@pytest.mark.anyio
async def test_beta_fixture_vector_eval_reports_case_diagnostics() -> None:
    report = await evaluate_dataset(top_k=5, profile="beta-fixture", retrieval="vector")

    assert report["profile"] == "beta-fixture"
    assert report["case_count"] == len(load_eval_cases(dataset_path_for_profile("beta-fixture")))
    assert "mrr@5" in report["metrics"]
    assert "diagnostics" in report["cases"][0]
    assert "retrieved_ids" in report["cases"][0]["diagnostics"]
    assert "final_ids" in report["cases"][0]["diagnostics"]


def test_rag_eval_gate_adds_operational_rates_and_threshold_failures() -> None:
    report = enrich_report(
        {
            "case_count": 2,
            "top_k": 5,
            "profile": "demo",
            "metrics": {"recall@5": 0.5, "top1_accuracy": 0.5, "mrr@5": 0.5},
            "cases": [
                {"retrieved_product_ids": [1], "diagnostics": {"fallback_stage": "strict"}},
                {"retrieved_product_ids": [], "diagnostics": {"fallback_stage": "fallback_budget"}},
            ],
        }
    )

    failures = check_thresholds(
        report,
        RagEvalThresholds(
            min_recall=0.7,
            min_top1=0.9,
            min_mrr=0.7,
            max_fallback_rate=0.2,
            max_empty_result_rate=0.0,
        ),
    )

    assert report["metrics"]["fallback_rate"] == 0.5
    assert report["metrics"]["empty_result_rate"] == 0.5
    assert len(failures) == 5


@pytest.mark.anyio
async def test_rag_eval_gate_passes_demo_thresholds() -> None:
    report = await evaluate_rag_gate(
        profile="demo",
        retrieval="fallback",
        top_k=5,
        thresholds=RagEvalThresholds(
            min_recall=0.7,
            min_top1=0.9,
            min_mrr=0.7,
            max_fallback_rate=0.2,
            max_empty_result_rate=0.0,
        ),
    )

    assert report["gate_passed"] is True
    assert "fallback_rate" in report["metrics"]
    assert "empty_result_rate" in report["metrics"]
