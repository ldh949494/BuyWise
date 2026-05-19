from pathlib import Path

from scripts.validate_repo_lint import Diagnostic, ROOT


FORBIDDEN_SERVICE_IMPORTS = (
    "from fastapi",
    "import fastapi",
    "from starlette.exceptions",
    "from starlette.responses",
)


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


def test_services_do_not_import_http_framework_types() -> None:
    service_root = ROOT / "app" / "services"
    offenders: list[str] = []

    for path in service_root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        source = path.read_text(encoding="utf-8")
        for forbidden_import in FORBIDDEN_SERVICE_IMPORTS:
            if forbidden_import in source:
                rel_path = path.relative_to(ROOT).as_posix()
                offenders.append(f"{rel_path}: imports {forbidden_import!r}")

    assert offenders == []
