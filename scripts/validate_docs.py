from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTS_PATH = ROOT / "AGENTS.md"
DOCS_ROOT = ROOT / "docs"
MAX_AGENTS_LINES = 120
VALID_STATUSES = {"Draft", "Approved", "Implemented", "Deprecated"}
REQUIRED_PATHS = [
    DOCS_ROOT / "architecture",
    DOCS_ROOT / "design",
    DOCS_ROOT / "conventions",
    DOCS_ROOT / "plans",
    DOCS_ROOT / "product",
    DOCS_ROOT / "reference",
    DOCS_ROOT / "plans" / "current.md",
]
LOCAL_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
STATUS_RE = re.compile(r"^Status:\s*(\w+)\s*$", re.MULTILINE)


def is_url(target: str) -> bool:
    return target.startswith(("http://", "https://", "mailto:"))


def normalize_link_target(target: str) -> str:
    return target.split("#", 1)[0].strip()


def should_check_code_path(value: str) -> bool:
    if not value or " " in value or value.startswith(("-", "$", ".")):
        return False
    if any(ch in value for ch in "*?{}"):
        return False
    if value.startswith(("http://", "https://")):
        return False
    if "\\" in value:
        value = value.replace("\\", "/")
    parts = value.split("/")
    return parts[0] in {
        "app",
        "android-app",
        "data",
        "docs",
        "observability",
        "scripts",
        "tests",
    } or value in {
        "AGENTS.md",
        "Dockerfile",
        "README.md",
        "docker-compose.yml",
        "docker-compose.observability.yml",
        "requirements.txt",
    }


def check_agents(errors: list[str]) -> None:
    if not AGENTS_PATH.exists():
        errors.append("AGENTS.md is missing.")
        return

    lines = AGENTS_PATH.read_text(encoding="utf-8").splitlines()
    if len(lines) > MAX_AGENTS_LINES:
        errors.append(f"AGENTS.md has {len(lines)} lines; limit is {MAX_AGENTS_LINES}.")

    text = "\n".join(lines)
    for required in REQUIRED_PATHS:
        rel = required.relative_to(ROOT).as_posix()
        if rel not in text:
            errors.append(f"AGENTS.md does not reference required path: {rel}")


def check_required_paths(errors: list[str]) -> None:
    for path in REQUIRED_PATHS:
        if not path.exists():
            errors.append(f"Required docs path is missing: {path.relative_to(ROOT).as_posix()}")


def check_links(path: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for match in LOCAL_LINK_RE.finditer(text):
        target = normalize_link_target(match.group(1))
        if not target or is_url(target):
            continue
        candidate = (path.parent / target).resolve()
        try:
            candidate.relative_to(ROOT)
        except ValueError:
            errors.append(f"{path.relative_to(ROOT).as_posix()} links outside repo: {target}")
            continue
        if not candidate.exists():
            errors.append(f"{path.relative_to(ROOT).as_posix()} has broken link: {target}")


def check_inline_paths(path: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for match in INLINE_CODE_RE.finditer(text):
        value = match.group(1).strip().replace("\\", "/")
        if not should_check_code_path(value):
            continue
        candidate = ROOT / value
        if not candidate.exists():
            errors.append(f"{path.relative_to(ROOT).as_posix()} references missing path: {value}")


def check_design_status(path: Path, errors: list[str]) -> None:
    if path.name.startswith("_"):
        return
    text = path.read_text(encoding="utf-8")
    statuses = STATUS_RE.findall(text)
    if len(statuses) != 1:
        errors.append(f"{path.relative_to(ROOT).as_posix()} must contain exactly one Status line.")
        return
    if statuses[0] not in VALID_STATUSES:
        valid = ", ".join(sorted(VALID_STATUSES))
        errors.append(f"{path.relative_to(ROOT).as_posix()} has invalid Status: {statuses[0]}; expected one of {valid}.")


def iter_markdown_files() -> list[Path]:
    files = []
    if AGENTS_PATH.exists():
        files.append(AGENTS_PATH)
    if DOCS_ROOT.exists():
        files.extend(sorted(DOCS_ROOT.rglob("*.md")))
    return files


def main() -> int:
    errors: list[str] = []
    check_agents(errors)
    check_required_paths(errors)

    for path in iter_markdown_files():
        check_links(path, errors)
        check_inline_paths(path, errors)
        if path.parent == DOCS_ROOT / "design":
            check_design_status(path, errors)

    if errors:
        print("Documentation validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Documentation validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
