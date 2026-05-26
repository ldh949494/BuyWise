from pathlib import Path


SCRIPT = Path("scripts/start_demo.ps1")


def test_start_demo_checks_native_command_failures_before_backend_start() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    assert "function Assert-LastExitCode" in text
    assert '& $python -m app.scripts.migrate_database\nAssert-LastExitCode "database migration"' in text
    assert '& $python -m app.scripts.seed_products --profile demo\nAssert-LastExitCode "demo seed data"' in text
    assert '& $python -m app.scripts.build_vector_index\n    Assert-LastExitCode "vector index build"' in text


def test_start_demo_preflights_embedding_configuration_before_index_build() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    assert '[Environment]::GetEnvironmentVariable($Name)' in text
    assert '$embeddingProvider = Get-DemoEnvValue $envValues "EMBEDDING_PROVIDER"' in text
    assert '$embeddingBaseUrl = Get-DemoEnvValue $envValues "EMBEDDING_BASE_URL"' in text
    assert '$embeddingApiKey = Get-DemoEnvValue $envValues "EMBEDDING_API_KEY"' in text
    assert 'Non-mock EMBEDDING_PROVIDER requires EMBEDDING_BASE_URL and EMBEDDING_API_KEY when building the demo vector index.' in text
    assert 'Use -SkipIndex to start without rebuilding the index.' in text
