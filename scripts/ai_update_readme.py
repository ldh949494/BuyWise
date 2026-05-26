import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from app.utils.subprocess_tools import run

ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
DIFF_PATHS = ("app", "android-app", "scripts", ".github", "requirements.txt", "README.md")
AUTO_DOCS_START = "<!-- AUTO-DOCS:START -->"
AUTO_DOCS_END = "<!-- AUTO-DOCS:END -->"


def run_with_input(cmd: list[str], stdin: str) -> str:
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        input=stdin,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        output = "\n".join(
            part.strip() for part in (result.stdout, result.stderr) if part.strip()
        )
        raise RuntimeError(output or f"Command failed: {' '.join(cmd)}")

    return result.stdout.strip()


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


def update_readme_with_ai(readme: str, diff: str, tree: str) -> str:
    model = os.getenv("GITHUB_MODELS_README_MODEL", "openai/gpt-4.1")
    prompt = """
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

    context = f"""
Instructions:
{prompt}

Current file tree:
{tree}

Current git diff:
{diff}

Current README.md:
{readme}
""".strip()

    output = run_with_input(
        [
            "gh",
            "models",
            "run",
            model,
            "Read stdin and return only the Markdown content for the README AUTO-DOCS block.",
        ],
        context,
    )
    generated = normalize_readme_output(output)
    return replace_auto_docs_block(readme, generated)


def main() -> int:
    if not README_PATH.exists():
        README_PATH.write_text("# Project\n\n", encoding="utf-8")

    diff = get_git_diff()
    if not diff:
        print("README_CHANGED=false")
        print("No relevant code changes detected. Skip README update.")
        return 0

    if not shutil.which("gh"):
        print("README_CHANGED=false")
        print("GitHub CLI is not available. Skip README update.")
        return 0

    readme = README_PATH.read_text(encoding="utf-8")
    tree = get_file_tree()

    try:
        new_readme = update_readme_with_ai(readme, diff, tree)
    except Exception as exc:  # noqa: BLE001
        print("README_CHANGED=false")
        print(f"README AI update skipped: {exc}")
        return 0

    if new_readme == readme:
        print("README_CHANGED=false")
        print("README content unchanged after AI update.")
        return 0

    README_PATH.write_text(new_readme, encoding="utf-8")
    print("README_CHANGED=true")
    print("README.md updated by AI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
