from pathlib import Path


SCRIPT = Path("scripts/release_prepare.ps1")


def test_release_prepare_defaults_to_migration_only() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    assert '[string]$SeedProfile = ""' in text
    assert '[string]$ImportCsv = ""' in text
    assert "[switch]$RequireRealCatalog" in text
    assert "[switch]$BuildIndex" in text
    assert "[switch]$CheckIndex" in text
    assert "& $python -m app.scripts.migrate_database" in text


def test_release_prepare_requires_explicit_catalog_and_index_actions() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    assert 'if ($SeedProfile -and $ImportCsv)' in text
    assert 'if ($RequireRealCatalog -and -not $ImportCsv)' in text
    assert "app.scripts.seed_products --profile $SeedProfile" in text
    assert '"app.scripts.import_products", "--csv", $ImportCsv' in text
    assert '"--require-real-assets"' in text
    assert "app.scripts.build_vector_index --mode $IndexMode" in text
    assert "app.scripts.check_vector_index" in text
