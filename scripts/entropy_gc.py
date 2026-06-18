from __future__ import annotations

import argparse
import os
import shutil
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.validate_entropy import BASELINE_PATH, collect_issues  # noqa: E402
from app.utils.subprocess_tools import run_with_input  # noqa: E402

ARTIFACTS_DIR = ROOT / "artifacts" / "entropy-gc"
DEFAULT_MODEL = "openai/gpt-4.1"


def render_deterministic_report() -> str:
    issues = collect_issues()
    counts = Counter(issue.rule for issue in issues)
    lines = [
        "# Entropy GC Report",
        "",
        f"Generated at: {datetime.now(UTC).isoformat()}",
        f"Baseline: {BASELINE_PATH.relative_to(ROOT).as_posix()}",
        "",
        "## Summary",
        "",
        f"- Total detected entropy issues: {len(issues)}",
    ]
    for rule, count in sorted(counts.items()):
        lines.append(f"- {rule}: {count}")

    lines.extend(["", "## Cleanup Candidates", ""])
    if not issues:
        lines.append("- No entropy issues detected.")
    for issue in issues:
        lines.extend(
            [
                f"### {issue.rule}: {issue.symbol}",
                "",
                f"- Location: `{issue.path}:{issue.line}`",
                f"- ERROR: {issue.detail}",
                f"- FIX: {issue.fix}",
                f"- SEE: `{issue.see}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Operating Notes",
            "",
            "- This report is read-only. Apply cleanup through normal code changes and tests.",
            "- After intentionally paying down or accepting debt, run `python scripts/validate_entropy.py --refresh-baseline`.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_ai_prompt() -> str:
    return """
You are reviewing a repository entropy and garbage-collection report.
Return concise Chinese cleanup guidance.

Requirements:
1. Prioritize changes that reduce drift, duplicated helpers, long functions, stale TODOs, or ad-hoc error handling.
2. Do not propose behavior changes unless required to preserve existing contracts.
3. Group suggestions by safe incremental PRs.
4. Include validation commands for each group.
5. Return Markdown only.
""".strip()


def append_ai_guidance(report: str, model: str) -> str:
    if not shutil.which("gh"):
        return report + "\n## AI Guidance\n\nGitHub CLI is unavailable; skipped AI guidance.\n"
    try:
        guidance = run_with_input(["gh", "models", "run", model, build_ai_prompt()], report)
    except Exception as exc:  # noqa: BLE001
        return report + f"\n## AI Guidance\n\nAI guidance skipped: {exc}\n"
    return report + "\n## AI Guidance\n\n" + guidance.strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a read-only entropy garbage-collection report.")
    parser.add_argument("--with-ai", action="store_true", help="Append gh models cleanup guidance.")
    parser.add_argument("--model", default=os.getenv("ENTROPY_GC_MODEL", DEFAULT_MODEL))
    parser.add_argument("--output", default=str(ARTIFACTS_DIR / "report.md"))
    args = parser.parse_args()

    report = render_deterministic_report()
    if args.with_ai:
        report = append_ai_guidance(report, args.model)

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"Entropy GC report written to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
