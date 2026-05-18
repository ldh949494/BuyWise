from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


TEXT_FILE_SUFFIXES = {
    ".csv",
    ".env",
    ".example",
    ".ini",
    ".json",
    ".kt",
    ".md",
    ".ps1",
    ".py",
    ".toml",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
TEXT_FILE_NAMES = {
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    ".python-version",
    "Dockerfile",
    "requirements.txt",
}
IGNORED_TEXT_PARTS = {
    ".git",
    ".gradle",
    ".idea",
    ".kotlin",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "artifacts",
    "build",
    "vector_store",
}
MOJIBAKE_RE = re.compile(r"[\u00c2\u00c3\u00c5\u00e2\u00e5][\u0080-\u00bf\u0100-\u017f]")
REPLACEMENT_CHAR = "\ufffd"


@dataclass(frozen=True)
class TextEncodingDiagnostic:
    path: Path
    line: int
    error: str
    fix: str


def iter_text_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or any(part in IGNORED_TEXT_PARTS for part in path.parts):
            continue
        if path.name in TEXT_FILE_NAMES or path.suffix in TEXT_FILE_SUFFIXES:
            files.append(path)
    return sorted(files)


def check_text_encoding(path: Path) -> list[TextEncodingDiagnostic]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return [
            TextEncodingDiagnostic(
                path,
                exc.start + 1,
                "Text file is not valid UTF-8.",
                "Re-save this file as UTF-8. Do not commit GBK/ANSI encoded text.",
            )
        ]

    diagnostics: list[TextEncodingDiagnostic] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if REPLACEMENT_CHAR in line or MOJIBAKE_RE.search(line):
            diagnostics.append(
                TextEncodingDiagnostic(
                    path,
                    lineno,
                    "Line contains likely mojibake or replacement characters.",
                    "Restore the intended text and save the file as UTF-8. "
                    "For PowerShell output, run scripts through scripts/set_utf8.ps1.",
                )
            )
    return diagnostics


def collect_text_encoding_diagnostics(root: Path) -> list[TextEncodingDiagnostic]:
    diagnostics: list[TextEncodingDiagnostic] = []
    for path in iter_text_files(root):
        diagnostics.extend(check_text_encoding(path))
    return diagnostics
