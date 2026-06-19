from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.utils.subprocess_tools import run, run_with_input  # noqa: E402

ARTIFACTS_DIR = ROOT / "artifacts" / "doc-gardening"
DEFAULT_MODEL = "openai/gpt-4.1"
CONTEXT_PATHS = [
    "AGENTS.md",
    "README.md",
    "docker-compose.yml",
    "docker-compose.observability.yml",
    "requirements.in",
    "requirements.txt",
    "requirements-dev.in",
    "requirements-dev.txt",
    "scripts/auto_validate.ps1",
    "scripts/validate_docs.py",
]


def read_text(path: Path, *, limit: int = 12000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > limit:
        return text[:limit] + "\n[truncated]\n"
    return text


def collect_docs_index() -> str:
    files = []
    for base in [ROOT / "docs"]:
        if base.exists():
            files.extend(sorted(base.rglob("*.md")))
    lines = []
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        first_heading = ""
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("# "):
                first_heading = line[2:].strip()
                break
        lines.append(f"- {rel}: {first_heading}")
    return "\n".join(lines)


def collect_context() -> str:
    tracked_files = run(["git", "ls-files"])
    status = run(["git", "status", "--short"])
    diff_stat = run(["git", "diff", "--stat", "--", "AGENTS.md", "docs", "app", "android-app", "scripts", ".github", "README.md"])
    recent_commits = run(["git", "log", "--oneline", "-n", "20"])
    validation = run([sys.executable, "scripts/validate_docs.py"])

    file_sections = []
    for rel in CONTEXT_PATHS:
        text = read_text(ROOT / rel)
        if text:
            file_sections.append(f"## {rel}\n\n{text}")

    return "\n\n".join(
        [
            f"Generated at: {datetime.now(UTC).isoformat()}",
            "Tracked files:\n" + "\n".join(tracked_files.splitlines()[:400]),
            "Git status:\n" + (status or "[clean]"),
            "Diff stat:\n" + (diff_stat or "[none]"),
            "Recent commits:\n" + recent_commits,
            "Docs index:\n" + collect_docs_index(),
            "Docs validation:\n" + validation,
            "\n\n".join(file_sections),
        ]
    )


def build_prompt() -> str:
    return """
You are maintaining repository memory for an AI coding agent.
Review the repository context and produce a concise Chinese doc-gardening report.

Requirements:
1. Identify docs that appear stale, missing, too vague, or inconsistent with code structure.
2. Prioritize issues that would mislead future agents.
3. Recommend exact files to update and the intended content change.
4. Do not invent features that are not supported by the context.
5. Do not rewrite the docs. Return a Markdown report only.
6. Include sections: 摘要, 需要更新, 可暂缓, 验证建议.
""".strip()


def build_apply_prompt() -> str:
    return """
You are maintaining repository memory for an AI coding agent.
Review the repository context and propose direct documentation updates.

Return only JSON with this exact shape:
{"files":[{"path":"docs/...md","content":"complete file content"}]}

Rules:
1. Only edit AGENTS.md, README.md, or files under docs/.
2. Return complete file content for each changed file.
3. Do not change application code, scripts, workflow files, or generated artifacts.
4. Keep AGENTS.md short and map-like.
5. Preserve accurate existing content.
6. Do not invent features that are not supported by the context.
7. If no changes are needed, return {"files":[]}.
""".strip()


def normalize_json_output(output: str) -> str:
    stripped = output.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return stripped


def ensure_editable_path(path_text: str) -> Path:
    rel = Path(path_text)
    if rel.is_absolute():
        raise ValueError(f"Absolute paths are not allowed: {path_text}")
    normalized = rel.as_posix()
    if normalized not in {"AGENTS.md", "README.md"} and not normalized.startswith("docs/"):
        raise ValueError(f"doc-gardening --apply can only edit AGENTS.md, README.md, or docs/: {path_text}")
    target = (ROOT / rel).resolve()
    target.relative_to(ROOT)
    return target


def apply_updates(output: str) -> list[Path]:
    payload = json.loads(normalize_json_output(output))
    files = payload.get("files")
    if not isinstance(files, list):
        raise ValueError("Model output must contain a files list.")

    changed: list[Path] = []
    for item in files:
        if not isinstance(item, dict):
            raise ValueError("Each files item must be an object.")
        path_text = item.get("path")
        content = item.get("content")
        if not isinstance(path_text, str) or not isinstance(content, str):
            raise ValueError("Each files item must include string path and content.")
        target = ensure_editable_path(path_text)
        target.parent.mkdir(parents=True, exist_ok=True)
        current = target.read_text(encoding="utf-8") if target.exists() else ""
        desired = content.rstrip() + "\n"
        if current != desired:
            target.write_text(desired, encoding="utf-8")
            changed.append(target)

    return changed


def resolve_output_path(path_text: str) -> Path:
    output_path = Path(path_text)
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    return output_path


def write_report(output_path: Path, report: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a repository memory maintenance report.")
    parser.add_argument("--model", default=os.getenv("DOC_GARDENING_MODEL", DEFAULT_MODEL))
    parser.add_argument("--output", default=str(ARTIFACTS_DIR / "report.md"))
    parser.add_argument("--apply", action="store_true", help="Apply model-proposed updates to AGENTS.md, README.md, or docs/.")
    args = parser.parse_args()

    if not shutil.which("gh"):
        raise SystemExit("GitHub CLI is not available. Install gh or run this in GitHub Actions.")

    context = collect_context()
    prompt = build_apply_prompt() if args.apply else build_prompt()
    output = run_with_input(["gh", "models", "run", args.model, prompt], context)

    if args.apply:
        changed = apply_updates(output)
        run([sys.executable, "scripts/validate_docs.py"], check=True)
        if changed:
            print("Applied doc-gardening updates:")
            for path in changed:
                print(f"- {path.relative_to(ROOT).as_posix()}")
        else:
            print("No doc-gardening updates were needed.")
    else:
        output_path = resolve_output_path(args.output)
        write_report(output_path, output.strip() + "\n")
        print(f"Doc-gardening report written to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
