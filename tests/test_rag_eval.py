import pytest

from app.scripts.evaluate_rag import (
    dataset_path_for_profile,
    evaluate_dataset,
    known_seed_product_ids,
    load_eval_cases,
)


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
