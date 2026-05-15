from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

from scripts.validate_entropy import ROOT, EntropyIssue, collect_issues, load_baseline


ARTIFACTS_DIR = ROOT / "artifacts" / "entropy-cleanup"
DEFAULT_MODEL = "openai/gpt-4.1"
ALLOWED_ROOTS = {"app", "tests", "docs", "scripts"}
TARGET_RULES = ("bare-todo", "duplicate-function", "function-length", "broad-except")


def run_model(model: str, prompt: str, context: str) -> str:
    result = subprocess.run(
        ["gh", "models", "run", model, prompt],
        cwd=ROOT,
        input=context,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        message = "\n".join(part.strip() for part in [result.stdout, result.stderr] if part.strip())
        raise RuntimeError(message or "gh models failed")
    return result.stdout.strip()


def pick_issue() -> EntropyIssue | None:
    baseline = load_baseline()
    candidates = [issue for issue in collect_issues() if issue.key in baseline]
    for rule in TARGET_RULES:
        for issue in candidates:
            if issue.rule == rule:
                return issue
    return candidates[0] if candidates else None


def read_context(issue: EntropyIssue) -> str:
    path = ROOT / issue.path
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    return "\n\n".join(
        [
            "Selected entropy issue:",
            issue.render(),
            f"File: {issue.path}",
            text[:20000],
        ]
    )


def build_prompt() -> str:
    return """
You are a repository cleanup agent. Fix exactly the selected entropy issue.

Return only JSON with this exact shape:
{"summary":"...","files":[{"path":"app/...py","content":"complete file content"}]}

Rules:
1. Keep behavior unchanged unless the selected issue explicitly requires cleanup.
2. Prefer the smallest safe diff.
3. Only edit files under app/, tests/, docs/, scripts/, or AGENTS.md/README.md.
4. Do not refresh docs/entropy/baseline.json.
5. Return complete file contents for changed files.
6. If no safe cleanup is possible, return {"summary":"no safe cleanup","files":[]}.
""".strip()


def normalize_json(output: str) -> dict:
    stripped = output.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return json.loads(stripped)


def resolve_edit_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        raise ValueError(f"Absolute path is not allowed: {path_text}")
    normalized = path.as_posix()
    first = normalized.split("/", 1)[0]
    if normalized not in {"AGENTS.md", "README.md"} and first not in ALLOWED_ROOTS:
        raise ValueError(f"Path is outside cleanup allowlist: {path_text}")
    if normalized == "docs/entropy/baseline.json":
        raise ValueError("Cleanup agent must not refresh entropy baseline.")
    target = (ROOT / path).resolve()
    target.relative_to(ROOT)
    return target


def apply_files(payload: dict) -> list[Path]:
    changed = []
    for item in payload.get("files", []):
        target = resolve_edit_path(str(item["path"]))
        content = str(item["content"]).rstrip() + "\n"
        current = target.read_text(encoding="utf-8") if target.exists() else ""
        if current != content:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            changed.append(target)
    return changed


def write_report(issue: EntropyIssue | None, summary: str, changed: list[Path]) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    lines = ["# Entropy Cleanup Agent Report", ""]
    if issue is None:
        lines.append("No baseline entropy issue was available for cleanup.")
    else:
        lines.extend(["## Selected Issue", "", "```text", issue.render(), "```", ""])
        lines.extend(["## Summary", "", summary or "No summary provided.", ""])
        lines.append("## Changed Files")
        lines.extend(f"- {path.relative_to(ROOT).as_posix()}" for path in changed)
    (ARTIFACTS_DIR / "report.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply one low-risk entropy cleanup using gh models.")
    parser.add_argument("--model", default=os.getenv("ENTROPY_CLEANUP_MODEL", DEFAULT_MODEL))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not shutil.which("gh"):
        raise SystemExit("GitHub CLI is required for entropy cleanup agent.")
    issue = pick_issue()
    if issue is None:
        write_report(None, "", [])
        print("No entropy cleanup target found.")
        return 0

    payload = normalize_json(run_model(args.model, build_prompt(), read_context(issue)))
    changed = [] if args.dry_run else apply_files(payload)
    write_report(issue, str(payload.get("summary", "")), changed)
    print(f"Entropy cleanup changed {len(changed)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
