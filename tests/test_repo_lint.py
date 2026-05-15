from pathlib import Path

from scripts.validate_repo_lint import Diagnostic, ROOT


def test_lint_diagnostic_includes_error_and_fix_prompt() -> None:
    diagnostic = Diagnostic(
        path=ROOT / "app" / "services" / "example.py",
        line=12,
        error="File exceeds 300 lines limit.",
        fix="Split into smaller modules. See docs/conventions/file-size.md.",
    )

    rendered = diagnostic.render()

    assert "app/services/example.py:12" in rendered
    assert "ERROR: File exceeds 300 lines limit." in rendered
    assert "FIX: Split into smaller modules. See docs/conventions/file-size.md." in rendered
