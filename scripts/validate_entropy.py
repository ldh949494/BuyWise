from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "docs" / "entropy" / "baseline.json"
FUNCTION_LINE_LIMIT = 30
MIN_DUPLICATE_LINES = 5
APP_ROOT = ROOT / "app"
SCRIPT_ROOT = ROOT / "scripts"
TODO_RE = re.compile(r"\b(TODO|FIXME|HACK)\b", re.IGNORECASE)
TODO_OWNER_RE = re.compile(r"\b(owner|issue):", re.IGNORECASE)
PUBLIC_VERB_PREFIXES = (
    "get",
    "list",
    "create",
    "update",
    "delete",
    "search",
    "build",
    "extract",
    "generate",
    "handle",
    "import",
    "seed",
    "compare",
    "rank",
    "validate",
    "register",
    "configure",
)
VERB_RULE_LAYERS = {"services", "repositories"}

@dataclass(frozen=True)
class EntropyIssue:
    rule: str
    path: str
    line: int
    symbol: str
    detail: str
    fix: str
    see: str

    @property
    def key(self) -> str:
        return f"{self.rule}|{self.path}|{self.symbol}"

    def to_baseline(self) -> dict[str, object]:
        return {
            "key": self.key,
            "rule": self.rule,
            "path": self.path,
            "line": self.line,
            "symbol": self.symbol,
            "detail": self.detail,
        }

    def render(self) -> str:
        location = self.path if self.line == 0 else f"{self.path}:{self.line}"
        return f"{location}\nERROR: {self.detail}\nFIX: {self.fix}\nSEE: {self.see}"

def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()

def iter_python_files() -> list[Path]:
    files = []
    for root in [APP_ROOT, SCRIPT_ROOT]:
        if root.exists():
            files.extend(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)
    return sorted(files)

def read_tree(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

def function_length(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    end = getattr(node, "end_lineno", node.lineno)
    return end - node.lineno + 1

def source_layer(path: Path) -> str | None:
    relative = path.relative_to(ROOT)
    if len(relative.parts) < 3 or relative.parts[0] != "app":
        return None
    return relative.parts[1]

def is_test_or_script_path(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    return relative.parts[0] == "scripts" or relative.parts[:2] == ("app", "scripts")

def normalized_function_hash(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    clone = ast.FunctionDef(
        name="_",
        args=node.args,
        body=node.body,
        decorator_list=[],
        returns=None,
        type_comment=None,
    )
    normalized = ast.dump(clone, include_attributes=False)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def check_function_lengths(path: Path, tree: ast.AST, issues: list[EntropyIssue]) -> None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            lines = function_length(node)
            if lines > FUNCTION_LINE_LIMIT:
                issues.append(
                    EntropyIssue(
                        rule="function-length",
                        path=rel(path),
                        line=node.lineno,
                        symbol=node.name,
                        detail=f"Function exceeds {FUNCTION_LINE_LIMIT} lines limit; found {lines}.",
                        fix="Split orchestration into smaller helpers or move behavior to a service. "
                        "Keep each function focused on one level of abstraction.",
                        see="docs/conventions/golden-principles.md",
                    )
                )

def check_public_verb_names(path: Path, tree: ast.AST, issues: list[EntropyIssue]) -> None:
    layer = source_layer(path)
    if layer not in VERB_RULE_LAYERS:
        return

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name.startswith("_") or node.name.startswith("test_"):
            continue
        if not node.name.startswith(PUBLIC_VERB_PREFIXES):
            issues.append(
                EntropyIssue(
                    rule="public-function-verb",
                    path=rel(path),
                    line=node.lineno,
                    symbol=node.name,
                    detail=f"Public {layer} function '{node.name}' does not start with an approved verb.",
                    fix="Rename the function to start with a clear action verb such as get, list, create, "
                    "update, search, build, extract, generate, handle, compare, rank, validate, or configure.",
                    see="docs/conventions/golden-principles.md",
                )
            )

def check_todo_lines(path: Path, lines: list[str], issues: list[EntropyIssue]) -> None:
    for lineno, line in enumerate(lines, start=1):
        if TODO_RE.search(line) and not TODO_OWNER_RE.search(line):
            issues.append(
                EntropyIssue(
                    rule="bare-todo",
                    path=rel(path),
                    line=lineno,
                    symbol=f"line-{lineno}",
                    detail="Comment contains TODO/FIXME/HACK without owner: or issue:.",
                    fix="Add owner: or issue: to make the cleanup accountable, or delete the stale comment "
                    "and move real work to docs/plans/current.md.",
                    see="docs/conventions/entropy-gc.md",
                )
            )

def check_todos(path: Path, issues: list[EntropyIssue]) -> None:
    if is_test_or_script_path(path):
        return
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    check_todo_lines(path, lines, issues)

def exception_reports_to_error_provider(handler: ast.ExceptHandler) -> bool:
    for node in ast.walk(handler):
        if isinstance(node, ast.Raise):
            return True
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and "error" in node.func.attr.lower():
                return True
            if isinstance(node.func, ast.Name) and node.func.id in {"get_error_provider", "get_provider"}:
                return True
    return False

def check_error_handling(path: Path, tree: ast.AST, issues: list[EntropyIssue]) -> None:
    if is_test_or_script_path(path):
        return
    for handler in [node for node in ast.walk(tree) if isinstance(node, ast.ExceptHandler)]:
        catches_exception = handler.type is None
        if isinstance(handler.type, ast.Name) and handler.type.id == "Exception":
            catches_exception = True
        if isinstance(handler.type, ast.Tuple):
            catches_exception = any(isinstance(elt, ast.Name) and elt.id == "Exception" for elt in handler.type.elts)
        if catches_exception and not exception_reports_to_error_provider(handler):
            issues.append(
                EntropyIssue(
                    rule="broad-except",
                    path=rel(path),
                    line=handler.lineno,
                    symbol=f"except-{handler.lineno}",
                    detail="Broad exception handler does not report through ErrorProvider or re-raise.",
                    fix="Use get_provider('errors') or get_error_provider() to report/map the error, or re-raise "
                    "after adding context. Do not create local ad-hoc error handling.",
                    see="docs/conventions/providers.md",
                )
            )

def collect_duplicate_issues(functions: list[tuple[str, Path, ast.FunctionDef | ast.AsyncFunctionDef]]) -> list[EntropyIssue]:
    by_hash: dict[str, list[tuple[Path, ast.FunctionDef | ast.AsyncFunctionDef]]] = {}
    for digest, path, node in functions:
        if function_length(node) >= MIN_DUPLICATE_LINES:
            by_hash.setdefault(digest, []).append((path, node))

    issues: list[EntropyIssue] = []
    for entries in by_hash.values():
        if len(entries) < 2:
            continue
        locations = ", ".join(f"{rel(path)}:{node.lineno}:{node.name}" for path, node in entries)
        first_path, first_node = entries[0]
        issues.append(
            EntropyIssue(
                rule="duplicate-function",
                path=rel(first_path),
                line=first_node.lineno,
                symbol=normalized_function_hash(first_node)[:12],
                detail=f"Duplicate function implementation detected across {len(entries)} functions: {locations}.",
                fix="Extract the shared behavior into the existing owner layer or app/utils/. Prefer reuse over "
                "copying helper functions.",
                see="docs/conventions/golden-principles.md",
            )
        )
    return issues

def collect_issues() -> list[EntropyIssue]:
    issues: list[EntropyIssue] = []
    duplicate_inputs: list[tuple[str, Path, ast.FunctionDef | ast.AsyncFunctionDef]] = []
    for path in iter_python_files():
        tree = read_tree(path)
        check_function_lengths(path, tree, issues)
        check_public_verb_names(path, tree, issues)
        check_todos(path, issues)
        check_error_handling(path, tree, issues)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                duplicate_inputs.append((normalized_function_hash(node), path, node))
    issues.extend(collect_duplicate_issues(duplicate_inputs))
    return sorted(issues, key=lambda issue: (issue.rule, issue.path, issue.line, issue.symbol))

def load_baseline() -> set[str]:
    if not BASELINE_PATH.exists():
        return set()
    payload = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    return {str(item["key"]) for item in payload.get("issues", [])}

def write_baseline(issues: list[EntropyIssue]) -> None:
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "description": "Existing entropy debt. CI fails only on new issues not listed here.",
        "issues": [issue.to_baseline() for issue in issues],
    }
    BASELINE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def main() -> int:
    parser = argparse.ArgumentParser(description="Validate entropy and garbage-collection rules.")
    parser.add_argument("--refresh-baseline", action="store_true", help="Accept current entropy issues as baseline.")
    args = parser.parse_args()

    issues = collect_issues()
    if args.refresh_baseline:
        write_baseline(issues)
        print(f"Entropy baseline refreshed with {len(issues)} issues.")
        return 0

    baseline = load_baseline()
    new_issues = [issue for issue in issues if issue.key not in baseline]
    stale_keys = baseline - {issue.key for issue in issues}

    if new_issues:
        print("Entropy validation failed:")
        for issue in new_issues:
            print()
            print(issue.render())
        return 1

    if stale_keys:
        print(f"Entropy validation passed. {len(stale_keys)} baseline issues appear fixed; refresh baseline when ready.")
    else:
        print("Entropy validation passed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
