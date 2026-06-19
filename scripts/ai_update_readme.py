import os
import shutil
from pathlib import Path
from typing import Optional

from app.utils.subprocess_tools import run, run_with_input

ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
DIFF_PATHS = ("app", "android-app", "scripts", ".github", "requirements.txt", "README.md")
AUTO_DOCS_START = "<!-- AUTO-DOCS:START -->"
AUTO_DOCS_END = "<!-- AUTO-DOCS:END -->"


def resolve_diff_range() -> Optional[str]:
    explicit_range = os.getenv("README_DIFF_RANGE", "").strip()
    if explicit_range:
        return explicit_range

    before = os.getenv("GITHUB_EVENT_BEFORE", "").strip()
    sha = os.getenv("GITHUB_SHA", "").strip()
    if before and sha and before != "0" * 40:
        return f"{before}..{sha}"

    if sha:
        return f"{sha}^..{sha}"

    return None


def get_git_diff() -> str:
    diff_range = resolve_diff_range()

    if diff_range:
        diff_stat = run(["git", "diff", "--stat", diff_range, "--", *DIFF_PATHS])
        diff_detail = run(["git", "diff", diff_range, "--", *DIFF_PATHS])
    else:
        diff_stat = run(["git", "diff", "--stat", "--", *DIFF_PATHS])
        diff_detail = run(["git", "diff", "--", *DIFF_PATHS])

    return "\n\n".join(part for part in (diff_stat, diff_detail) if part).strip()


def get_file_tree() -> str:
    tracked_files = run(["git", "ls-files", *DIFF_PATHS])
    lines = [line for line in tracked_files.splitlines() if line.strip()]
    return "\n".join(lines[:200])


def normalize_readme_output(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()

    return stripped


def replace_auto_docs_block(readme: str, generated: str) -> str:
    start_index = readme.find(AUTO_DOCS_START)
    end_index = readme.find(AUTO_DOCS_END)

    if start_index == -1 or end_index == -1 or end_index < start_index:
        raise ValueError("README.md is missing a valid AUTO-DOCS block.")

    block_start = start_index + len(AUTO_DOCS_START)
    generated_block = "\n\n" + generated.strip() + "\n\n"
    return readme[:block_start] + generated_block + readme[end_index:]


def build_readme_prompt() -> str:
    return """
You are a professional software engineering documentation maintainer.
Read the repository file tree, git diff, and current README.md from stdin.
Return only the Markdown content that should appear inside the AUTO-DOCS block.

Requirements:
1. Do not return the AUTO-DOCS markers.
2. Do not rewrite any content outside the AUTO-DOCS block.
3. Do not invent features that are not supported by the diff or file tree.
4. Write in Chinese.
5. Return only Markdown. Do not include explanations or Markdown code fences.
6. If FastAPI, Android, Docker, RAG, or Agent-related content is detected, include the relevant run instructions.
""".strip()


def build_readme_context(readme: str, diff: str, tree: str) -> str:
    return f"""
Instructions:
{build_readme_prompt()}

Current file tree:
{tree}

Current git diff:
{diff}

Current README.md:
{readme}
""".strip()


def update_readme_with_ai(readme: str, diff: str, tree: str) -> str:
    model = os.getenv("GITHUB_MODELS_README_MODEL", "openai/gpt-4.1")
    output = run_with_input(
        [
            "gh",
            "models",
            "run",
            model,
            "Read stdin and return only the Markdown content for the README AUTO-DOCS block.",
        ],
        build_readme_context(readme, diff, tree),
    )
    return replace_auto_docs_block(readme, normalize_readme_output(output))


def ensure_readme_exists() -> None:
    if not README_PATH.exists():
        README_PATH.write_text("# Project\n\n", encoding="utf-8")


def report_readme_status(changed: bool, message: str) -> int:
    print(f"README_CHANGED={'true' if changed else 'false'}")
    print(message)
    return 0


def main() -> int:
    ensure_readme_exists()
    diff = get_git_diff()
    if not diff:
        return report_readme_status(False, "No relevant code changes detected. Skip README update.")

    if not shutil.which("gh"):
        return report_readme_status(False, "GitHub CLI is not available. Skip README update.")

    readme = README_PATH.read_text(encoding="utf-8")
    tree = get_file_tree()

    try:
        new_readme = update_readme_with_ai(readme, diff, tree)
    except Exception as exc:  # noqa: BLE001
        return report_readme_status(False, f"README AI update skipped: {exc}")

    if new_readme == readme:
        return report_readme_status(False, "README content unchanged after AI update.")

    README_PATH.write_text(new_readme, encoding="utf-8")
    return report_readme_status(True, "README.md updated by AI.")


if __name__ == "__main__":
    raise SystemExit(main())
