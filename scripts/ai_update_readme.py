import os
import subprocess
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
DIFF_PATHS = ("app", "android-app", "scripts", ".github", "requirements.txt", "README.md")


def run(cmd: list[str], *, check: bool = False) -> str:
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )
    output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    return output.strip()


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


def update_readme_with_ai(readme: str, diff: str, tree: str) -> str:
    from openai import OpenAI

    client = OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    )

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    prompt = f"""
你是一个专业的软件工程文档维护助手。

请根据当前仓库变更，更新 README.md。
要求：
1. 保留原有 README 的有用内容。
2. 根据代码变更同步更新功能说明、启动方式、测试方式、项目结构。
3. 不要编造不存在的功能。
4. 输出完整 README.md 内容。
5. 使用中文。
6. 如果检测到是 FastAPI / Android / Docker / RAG / Agent 项目，请补充对应运行说明。
7. 不要输出解释，只输出 README.md 正文。

当前文件树：
{tree}

当前 git diff：
{diff}

原 README：
{readme}
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "你负责维护项目 README 文档。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content.strip() + "\n"


def main() -> int:
    if not README_PATH.exists():
        README_PATH.write_text("# Project\n\n", encoding="utf-8")

    diff = get_git_diff()
    if not diff:
        print("README_CHANGED=false")
        print("No relevant code changes detected. Skip README update.")
        return 0

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("README_CHANGED=false")
        print("OPENAI_API_KEY is not set. Skip README update.")
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
