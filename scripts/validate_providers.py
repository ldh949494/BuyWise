from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "app"
PROVIDER_MODULE = "app.core.providers"
ALLOWED_FILES = {
    Path("app/core/auth_provider.py"),
    Path("app/core/error_provider.py"),
    Path("app/core/exceptions.py"),
    Path("app/core/logging_provider.py"),
    Path("app/core/logging_utils.py"),
    Path("app/core/middleware_provider.py"),
    Path("app/core/providers.py"),
    Path("app/core/logging.py"),
    Path("app/core/request_context.py"),
    Path("app/core/telemetry_provider.py"),
    Path("app/core/traffic.py"),
    Path("app/utils/logging.py"),
}
FORBIDDEN_MODULES = {
    "app.core.auth_provider": "Use app.core.providers for authentication dependencies and principals.",
    "app.core.error_provider": "Use app.core.providers.get_provider('errors') or get_error_provider().",
    "app.core.exceptions": "Use app.core.providers.AppError so cross-cutting errors stay behind providers.",
    "logging": "Use app.core.providers.get_provider('logging') or app.utils.logging.get_logger().",
    "app.core.logging_utils": "Use app.core.providers or app.utils.logging instead of logging internals.",
    "prometheus_fastapi_instrumentator": "Use app.core.providers.get_provider('telemetry').",
    "app.core.logging": "Use app.core.providers.get_provider('logging') or app.utils.logging.get_logger().",
    "app.core.request_context": "Use app.core.providers-managed request context instead of importing internals.",
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
