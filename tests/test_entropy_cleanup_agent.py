from pathlib import Path

import pytest

from scripts.entropy_cleanup_agent import ROOT, resolve_edit_path


def test_cleanup_agent_allows_documentation_and_app_paths() -> None:
    assert resolve_edit_path("app/services/example.py") == ROOT / "app" / "services" / "example.py"
    assert resolve_edit_path("docs/conventions/example.md") == ROOT / "docs" / "conventions" / "example.md"
    assert resolve_edit_path("README.md") == ROOT / "README.md"


def test_cleanup_agent_rejects_entropy_baseline_refresh() -> None:
    with pytest.raises(ValueError, match="must not refresh entropy baseline"):
        resolve_edit_path("docs/entropy/baseline.json")


def test_cleanup_agent_rejects_paths_outside_allowlist() -> None:
    with pytest.raises(ValueError, match="outside cleanup allowlist"):
        resolve_edit_path(".github/workflows/example.yml")


def test_cleanup_agent_rejects_absolute_paths() -> None:
    with pytest.raises(ValueError, match="Absolute path"):
        resolve_edit_path(str(Path.cwd() / "README.md"))
