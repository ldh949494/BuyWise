"""Clean expired local upload files."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.upload_service import ALLOWED_EXTENSIONS_BY_TYPE


@dataclass(frozen=True)
class CleanupUploadReport:
    scanned: int
    deleted: int
    skipped: int
    bytes_freed: int
    dry_run: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "scanned": self.scanned,
            "deleted": self.deleted,
            "skipped": self.skipped,
            "bytes_freed": self.bytes_freed,
            "dry_run": self.dry_run,
        }


def cleanup_uploads(
    upload_dir: str | Path = settings.upload_dir,
    *,
    max_age_hours: int = 24,
    dry_run: bool = False,
    now: datetime | None = None,
) -> CleanupUploadReport:
    root = Path(upload_dir).resolve()
    if not root.exists():
        return CleanupUploadReport(scanned=0, deleted=0, skipped=0, bytes_freed=0, dry_run=dry_run)

    cutoff = (now or datetime.now(timezone.utc)) - timedelta(hours=max_age_hours)
    allowed_extensions = set().union(*ALLOWED_EXTENSIONS_BY_TYPE.values())
    scanned = deleted = skipped = bytes_freed = 0

    for path in root.iterdir():
        if not path.is_file():
            skipped += 1
            continue
        scanned += 1
        if not _is_cleanable(path, root, allowed_extensions, cutoff):
            skipped += 1
            continue
        size = path.stat().st_size
        if not dry_run:
            path.unlink()
        deleted += 1
        bytes_freed += size
    return CleanupUploadReport(scanned, deleted, skipped, bytes_freed, dry_run)


def _is_cleanable(path: Path, root: Path, allowed_extensions: set[str], cutoff: datetime) -> bool:
    try:
        path.resolve().relative_to(root)
    except ValueError:
        return False
    if path.suffix.lower() not in allowed_extensions:
        return False
    modified_at = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    return modified_at < cutoff


def main() -> None:
    args = _parse_args()
    report = cleanup_uploads(args.upload_dir, max_age_hours=args.max_age_hours, dry_run=args.dry_run)
    print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean expired local BuyWise upload files.")
    parser.add_argument("--upload-dir", default=settings.upload_dir, help="Local upload directory to clean.")
    parser.add_argument("--max-age-hours", type=int, default=24, help="Delete files older than this many hours.")
    parser.add_argument("--dry-run", action="store_true", help="Report files that would be deleted without deleting.")
    return parser.parse_args()


if __name__ == "__main__":
    main()
