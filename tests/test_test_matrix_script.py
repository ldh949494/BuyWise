from pathlib import Path


PYTEST_INI = Path("pytest.ini")
TEST_MATRIX = Path("scripts/test_matrix.ps1")


def test_pytest_markers_define_test_tiers() -> None:
    text = PYTEST_INI.read_text(encoding="utf-8")

    assert "unit:" in text
    assert "integration:" in text
    assert "release:" in text


def test_test_matrix_runs_unit_integration_and_release_tiers() -> None:
    text = TEST_MATRIX.read_text(encoding="utf-8")

    assert '[ValidateSet("unit", "integration", "release")]' in text
    assert 'Invoke-PytestTier "not integration and not release"' in text
    assert 'Invoke-PytestTier "integration and not release"' in text
    assert '".\\scripts\\release_check.ps1"' in text
    assert '$releaseArgs += "-CheckOpenApiContract"' in text
    assert '$releaseArgs += "-RunRagEval"' in text
    assert '$releaseArgs += "-RunRealDependencySmoke"' in text
    assert '$releaseArgs += "-SmokeMySql"' in text
    assert '$releaseArgs += "-SmokeCos"' in text
