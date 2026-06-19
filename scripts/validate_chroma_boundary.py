from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SELF_PATH = Path(__file__).resolve()
SCAN_PATHS = [
    ROOT / "app",
    ROOT / "scripts",
    ROOT / "Dockerfile",
    *sorted(ROOT.glob("docker-compose*.yml")),
]
DISALLOWED_PATTERNS = {
    "chromadb.HttpClient": "Do not connect to a Chroma HTTP server from runtime code.",
    "chromadb.Client(": "Use chromadb.PersistentClient; do not use the default network-capable client.",
    "chroma run": "Do not start the Chroma HTTP server from project scripts.",
    "chromadb/chroma": "Do not deploy the Chroma HTTP server container.",
}


@dataclass(frozen=True)
class BoundaryFinding:
    path: Path
    pattern: str
    message: str

    def render(self) -> str:
        return f"{self.path.relative_to(ROOT).as_posix()}: {self.message} Pattern: {self.pattern}"


def iter_scanned_files() -> list[Path]:
    files: list[Path] = []
    for path in SCAN_PATHS:
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(item for item in path.rglob("*") if item.is_file() and "__pycache__" not in item.parts)
    return sorted({path for path in files if path.resolve() != SELF_PATH})


def scan_file(path: Path) -> list[BoundaryFinding]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return [
        BoundaryFinding(path, pattern, message)
        for pattern, message in DISALLOWED_PATTERNS.items()
        if pattern in text
    ]


def main() -> int:
    findings = [finding for path in iter_scanned_files() for finding in scan_file(path)]
    if findings:
        print("Chroma boundary validation failed:")
        for finding in findings:
            print(f"- {finding.render()}")
        return 1
    print("Chroma boundary validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
