from __future__ import annotations

import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.text_encoding_checks import collect_text_encoding_diagnostics  # noqa: E402

MAX_SOURCE_LINES = 300
PYTHON_ROOTS = [ROOT / "app", ROOT / "tests", ROOT / "scripts"]
KOTLIN_ROOT = ROOT / "android-app" / "app" / "src" / "main" / "java"
SNAKE_CASE_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
PASCAL_CASE_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")
CONSTANT_RE = re.compile(r"^[A-Z_][A-Z0-9_]*$")
KOTLIN_FILE_RE = re.compile(r"^[A-Z][A-Za-z0-9]*\.kt$")
PYTHON_FILE_RE = re.compile(r"^(__init__|[a-z_][a-z0-9_]*)\.py$")
KOTLIN_UNSTRUCTURED_LOG_RE = re.compile(r"\b(console\.log|System\.out\.println|Log\.[diewv]\s*\()")
RUNTIME_IMPORT_LAYERS = {"services", "ai"}
RUNTIME_IMPORT_PREFIXES = ("fastapi", "starlette")
RUNTIME_PREFIX_TUPLE = tuple(f"{prefix}." for prefix in RUNTIME_IMPORT_PREFIXES)


LAYER_RULES: dict[str, set[str]] = {
    "api": {"api", "core", "schemas", "services"},
    "services": {
        "ai",
        "core",
        "integrations",
        "models",
        "repositories",
        "schemas",
        "services",
        "utils",
        "vectorstore",
    },
    "repositories": {"core", "models", "repositories"},
    "models": {"core", "models"},
    "schemas": {"schemas"},
    "ai": {"ai", "core", "models", "repositories", "schemas", "utils", "vectorstore"},
    "vectorstore": {"ai", "core", "vectorstore"},
    "integrations": {"core", "integrations"},
    "utils": {"core", "schemas", "utils"},
}


@dataclass(frozen=True)
class Diagnostic:
    path: Path
    line: int
    error: str
    fix: str

    def render(self) -> str:
        location = self.path.relative_to(ROOT).as_posix()
        if self.line:
            location = f"{location}:{self.line}"
        return f"{location}\nERROR: {self.error}\nFIX: {self.fix}"
def iter_python_files() -> list[Path]:
    files: list[Path] = []
    for root in PYTHON_ROOTS:
        if root.exists():
            files.extend(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)
    return sorted(files)
def iter_kotlin_files() -> list[Path]:
    if not KOTLIN_ROOT.exists():
        return []
    return sorted(path for path in KOTLIN_ROOT.rglob("*.kt") if "build" not in path.parts)
def check_file_size(path: Path, diagnostics: list[Diagnostic]) -> None:
    line_count = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    if line_count > MAX_SOURCE_LINES:
        diagnostics.append(
            Diagnostic(
                path,
                0,
                f"File exceeds {MAX_SOURCE_LINES} lines limit; found {line_count}.",
                "Split into smaller modules. Move helper functions to a service, repository, or utils module. "
                "See docs/conventions/file-size.md for guidelines.",
            )
        )
def check_python_filename(path: Path, diagnostics: list[Diagnostic]) -> None:
    if not PYTHON_FILE_RE.match(path.name):
        diagnostics.append(
            Diagnostic(
                path,
                0,
                "Python filename does not use snake_case.",
                "Rename the file to snake_case.py. Keep package exports in __init__.py if callers need a stable import.",
            )
        )
def check_kotlin_filename(path: Path, diagnostics: list[Diagnostic]) -> None:
    if not KOTLIN_FILE_RE.match(path.name):
        diagnostics.append(
            Diagnostic(
                path,
                0,
                "Kotlin filename does not use PascalCase.",
                "Rename the file to PascalCase.kt and keep the primary class or composable name aligned with it.",
            )
        )


def check_python_names(path: Path, tree: ast.AST, diagnostics: list[Diagnostic]) -> None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not SNAKE_CASE_RE.match(node.name):
                diagnostics.append(
                    Diagnostic(
                        path,
                        node.lineno,
                        f"Function name '{node.name}' does not use snake_case.",
                        "Rename the function to snake_case and update all call sites.",
                    )
                )
            for arg in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]:
                if arg.arg in {"self", "cls"}:
                    continue
                if not SNAKE_CASE_RE.match(arg.arg):
                    diagnostics.append(
                        Diagnostic(
                            path,
                            arg.lineno,
                            f"Argument name '{arg.arg}' does not use snake_case.",
                            "Rename the argument to snake_case and update callers that pass it by keyword.",
                    )
                )
            for child in ast.walk(node):
                if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                    if not (SNAKE_CASE_RE.match(child.id) or CONSTANT_RE.match(child.id)):
                        diagnostics.append(
                            Diagnostic(
                                path,
                                child.lineno,
                                f"Variable name '{child.id}' does not use snake_case or CONSTANT_CASE.",
                                "Rename local variables to snake_case and module constants to CONSTANT_CASE.",
                            )
                        )
        elif isinstance(node, ast.ClassDef):
            if not PASCAL_CASE_RE.match(node.name):
                diagnostics.append(
                    Diagnostic(
                        path,
                        node.lineno,
                        f"Class name '{node.name}' does not use PascalCase.",
                        "Rename the class to PascalCase and update imports and type references.",
                    )
                )


def check_python_logging(path: Path, tree: ast.AST, diagnostics: list[Diagnostic]) -> None:
    rel = path.relative_to(ROOT)
    if rel.parts[0] in {"scripts", "tests"} or rel.parts[:2] == ("app", "scripts"):
        return
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
            diagnostics.append(
                Diagnostic(
                    path,
                    node.lineno,
                    "Runtime code uses print() instead of structured logging.",
                    "Use app.core.providers.get_provider('logging').get_logger(__name__) or app.utils.logging.get_logger(). "
                    "Log structured context as named fields or a dictionary.",
                )
            )


def layer_for(path: Path) -> str | None:
    rel = path.relative_to(ROOT)
    if len(rel.parts) < 3 or rel.parts[0] != "app":
        return None
    return rel.parts[1]


def imported_app_layer(module: str | None) -> str | None:
    if not module or not module.startswith("app."):
        return None
    parts = module.split(".")
    if len(parts) < 2:
        return None
    return parts[1]


def check_import_layers(path: Path, tree: ast.AST, diagnostics: list[Diagnostic]) -> None:
    source_layer = layer_for(path)
    if source_layer not in LAYER_RULES:
        return

    allowed_layers = LAYER_RULES[source_layer]
    for node in ast.walk(tree):
        module: str | None = None
        if isinstance(node, ast.ImportFrom):
            module = node.module
        elif isinstance(node, ast.Import):
            for alias in node.names:
                target_layer = imported_app_layer(alias.name)
                if target_layer and target_layer not in allowed_layers:
                    diagnostics.append(
                        Diagnostic(
                            path,
                            node.lineno,
                            f"Layer '{source_layer}' imports forbidden layer '{target_layer}'.",
                            "Move the dependency behind the next allowed layer. API code should call services; "
                            "services should call repositories or integrations. See docs/conventions/imports.md.",
                        )
                    )
            continue

        target_layer = imported_app_layer(module)
        if target_layer and target_layer not in allowed_layers:
            diagnostics.append(
                Diagnostic(
                    path,
                    node.lineno,
                    f"Layer '{source_layer}' imports forbidden layer '{target_layer}'.",
                    "Move the dependency behind the next allowed layer. API code should call services; "
                    "services should call repositories or integrations. See docs/conventions/imports.md.",
                )
            )


def check_runtime_framework_imports(path: Path, tree: ast.AST, diagnostics: list[Diagnostic]) -> None:
    source_layer = layer_for(path)
    if source_layer not in RUNTIME_IMPORT_LAYERS:
        return
    for node in ast.walk(tree):
        modules: list[str] = []
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        elif isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        for module in modules:
            if module not in RUNTIME_IMPORT_PREFIXES and not module.startswith(RUNTIME_PREFIX_TUPLE):
                continue
            fix = "Move HTTP/runtime framework usage behind app.core or app.api before calling it here."
            if module == "starlette.concurrency":
                fix = "Use app.core.concurrency.run_blocking_io instead of Starlette threadpool helpers."
            diagnostics.append(
                Diagnostic(path, node.lineno, f"Layer '{source_layer}' imports runtime framework module '{module}'.", fix)
            )


def check_python_file(path: Path, diagnostics: list[Diagnostic]) -> None:
    check_file_size(path, diagnostics)
    check_python_filename(path, diagnostics)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    check_python_names(path, tree, diagnostics)
    check_python_logging(path, tree, diagnostics)
    check_import_layers(path, tree, diagnostics)
    check_runtime_framework_imports(path, tree, diagnostics)


def check_kotlin_file(path: Path, diagnostics: list[Diagnostic]) -> None:
    check_file_size(path, diagnostics)
    check_kotlin_filename(path, diagnostics)
    for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if KOTLIN_UNSTRUCTURED_LOG_RE.search(line):
            diagnostics.append(
                Diagnostic(
                    path,
                    lineno,
                    "Kotlin code uses console/System/Log direct logging.",
                    "Route logging through the app logging provider when one exists. Do not introduce ad-hoc logging APIs.",
                )
            )


def main() -> int:
    diagnostics: list[Diagnostic] = []
    diagnostics.extend(
        Diagnostic(item.path, item.line, item.error, item.fix)
        for item in collect_text_encoding_diagnostics(ROOT)
    )
    for path in iter_python_files():
        check_python_file(path, diagnostics)
    for path in iter_kotlin_files():
        check_kotlin_file(path, diagnostics)

    if diagnostics:
        print("Custom repository lint failed:")
        for diagnostic in diagnostics:
            print()
            print(diagnostic.render())
        return 1

    print("Custom repository lint passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
