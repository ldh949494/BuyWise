from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "app"
PROVIDER_MODULE = "app.core.providers"
ALLOWED_FILES = {
    Path("app/core/providers.py"),
    Path("app/core/logging.py"),
    Path("app/utils/logging.py"),
}
FORBIDDEN_MODULES = {
    "logging": "Use app.core.providers.get_provider('logging') or app.utils.logging.get_logger().",
    "prometheus_fastapi_instrumentator": "Use app.core.providers.get_provider('telemetry').",
    "app.core.logging": "Use app.core.providers.get_provider('logging') or app.utils.logging.get_logger().",
}
FORBIDDEN_PREFIXES = {
    "opentelemetry": "Use app.core.providers.get_provider('telemetry').",
}


def is_allowed_file(path: Path) -> bool:
    return path.relative_to(ROOT) in ALLOWED_FILES


def check_module(module: str | None, path: Path, lineno: int, errors: list[str]) -> None:
    if not module:
        return
    if is_allowed_file(path):
        return
    if module == PROVIDER_MODULE:
        return
    if module in FORBIDDEN_MODULES:
        rel = path.relative_to(ROOT).as_posix()
        errors.append(f"{rel}:{lineno}: forbidden import '{module}'. {FORBIDDEN_MODULES[module]}")
        return
    for prefix, message in FORBIDDEN_PREFIXES.items():
        if module == prefix or module.startswith(f"{prefix}."):
            rel = path.relative_to(ROOT).as_posix()
            errors.append(f"{rel}:{lineno}: forbidden import '{module}'. {message}")


def check_file(path: Path, errors: list[str]) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                check_module(alias.name, path, node.lineno, errors)
        elif isinstance(node, ast.ImportFrom):
            check_module(node.module, path, node.lineno, errors)


def main() -> int:
    errors: list[str] = []
    for path in sorted(APP_ROOT.rglob("*.py")):
        check_file(path, errors)

    if errors:
        print("Provider validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Provider validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
