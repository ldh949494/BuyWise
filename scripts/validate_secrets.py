from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_BYTES = 5 * 1024 * 1024
SKIP_PATH_PARTS = {
    ".git",
    ".venv",
    "node_modules",
    "build",
    "dist",
}
SKIP_SUFFIXES = {
    ".jar",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".ico",
    ".pdf",
    ".zip",
}


@dataclass(frozen=True)
class SecretPattern:
    name: str
    regex: re.Pattern[str]


@dataclass(frozen=True)
class SecretFinding:
    path: Path
    line: int
    pattern: str

    def render(self) -> str:
        try:
            rel_path = self.path.relative_to(ROOT).as_posix()
        except ValueError:
            rel_path = self.path.as_posix()
        return f"{rel_path}:{self.line} matched {self.pattern}"


PATTERNS = (
    SecretPattern(
        "OpenAI API key",
        re.compile(r"(?<![A-Za-z0-9_-])(?:sk-proj-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]{32,})(?![A-Za-z0-9_-])"),
    ),
    SecretPattern("GitHub personal access token", re.compile(r"\b(?:ghp_[A-Za-z0-9_]{30,}|github_pat_[A-Za-z0-9_]{40,})\b")),
    SecretPattern("AWS access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    SecretPattern("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    SecretPattern("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    SecretPattern(
        "private key block",
        re.compile(r"-----BEGIN (?:RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"),
    ),
)


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return [ROOT / line for line in result.stdout.splitlines() if line.strip()]


def should_scan(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in SKIP_PATH_PARTS for part in rel.parts):
        return False
    if path.suffix.lower() in SKIP_SUFFIXES:
        return False
    try:
        return path.is_file() and path.stat().st_size <= MAX_FILE_BYTES
    except OSError:
        return False


def scan_file(path: Path) -> list[SecretFinding]:
    findings: list[SecretFinding] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return findings

    for line_number, line in enumerate(text.splitlines(), start=1):
        for pattern in PATTERNS:
            if pattern.regex.search(line):
                findings.append(SecretFinding(path=path, line=line_number, pattern=pattern.name))
    return findings


def collect_findings(paths: list[Path] | None = None) -> list[SecretFinding]:
    candidates = paths if paths is not None else tracked_files()
    findings: list[SecretFinding] = []
    for path in candidates:
        if should_scan(path):
            findings.extend(scan_file(path))
    return findings


def main() -> int:
    findings = collect_findings()
    if findings:
        print("Secret validation failed:")
        for finding in findings:
            print(finding.render())
        print("Rotate any exposed credential before removing it from the repository.")
        return 1

    print("Secret validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
