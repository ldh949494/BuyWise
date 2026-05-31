from pathlib import Path


CLOSED_BETA_VERIFY = Path("scripts/closed_beta_verify.ps1")
RELEASE_CHECK = Path("scripts/release_check.ps1")


def test_closed_beta_verify_forwards_expected_active_products_to_readiness() -> None:
    text = CLOSED_BETA_VERIFY.read_text(encoding="utf-8")

    assert "[int]$ExpectedActiveProducts = 0" in text
    assert "& $python -m app.scripts.print_runtime_config_summary" in text
    assert '$readinessArgs = @("-m", "app.scripts.readiness_check")' in text
    assert '$readinessArgs += @("--expected-active-products", $ExpectedActiveProducts.ToString())' in text
    assert "& $python @readinessArgs" in text


def test_release_check_forwards_expected_active_products_to_closed_beta_verify() -> None:
    text = RELEASE_CHECK.read_text(encoding="utf-8")

    assert "[int]$ExpectedActiveProducts = 0" in text
    assert '$smokeArgs += @("-ExpectedActiveProducts", $ExpectedActiveProducts.ToString())' in text


def test_release_check_can_run_rag_eval_gate() -> None:
    text = RELEASE_CHECK.read_text(encoding="utf-8")

    assert "[switch]$RunRagEval" in text
    assert "[string]$RagEvalProfile = \"android-contract\"" in text
    assert '"app.scripts.rag_eval_gate"' in text
    assert '"--max-empty-result-rate"' in text
    assert 'Assert-LastExitCode "RAG evaluation gate"' in text


def test_release_check_can_run_openapi_contract_gate() -> None:
    text = RELEASE_CHECK.read_text(encoding="utf-8")

    assert "[switch]$CheckOpenApiContract" in text
    assert "& $python -m app.scripts.openapi_contract" in text
    assert 'Assert-LastExitCode "OpenAPI contract"' in text


def test_release_check_can_run_real_dependency_smoke() -> None:
    text = RELEASE_CHECK.read_text(encoding="utf-8")

    assert "[switch]$RunRealDependencySmoke" in text
    assert "[switch]$SmokeMySql" in text
    assert "[switch]$SmokeCos" in text
    assert '"app.scripts.real_dependency_smoke"' in text
    assert 'Assert-LastExitCode "real dependency smoke"' in text
