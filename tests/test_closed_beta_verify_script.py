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
