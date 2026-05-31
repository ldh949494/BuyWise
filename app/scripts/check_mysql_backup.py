"""Validate that a MySQL backup artifact exists before release work."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.scripts.job_artifacts import run_job_with_artifact


def check_mysql_backup(
    path: str | Path,
    *,
    min_bytes: int = 1,
    max_age_hours: float | None = None,
) -> dict[str, Any]:
    backup_path = Path(path)
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")
    if not backup_path.is_file():
        raise ValueError(f"Backup path is not a file: {backup_path}")

    stat = backup_path.stat()
    if stat.st_size < min_bytes:
        raise ValueError(f"Backup file is smaller than {min_bytes} bytes: {backup_path}")

    modified_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
    age_seconds = (datetime.now(timezone.utc) - modified_at).total_seconds()
    if max_age_hours is not None and age_seconds > max_age_hours * 3600:
        raise ValueError(f"Backup file is older than {float(max_age_hours):.1f} hours: {backup_path}")

    return {
        "ok": True,
        "path": str(backup_path),
        "size_bytes": stat.st_size,
        "modified_at": modified_at.isoformat(),
        "age_seconds": round(age_seconds, 3),
    }


def main() -> None:
    args = _parse_args()
    inputs = {"path": args.path, "min_bytes": args.min_bytes, "max_age_hours": args.max_age_hours}
    result = run_job_with_artifact(
        job_name="check_mysql_backup",
        inputs=inputs,
        artifact_path=args.artifact_json,
        action=lambda: check_mysql_backup(
            args.path,
            min_bytes=args.min_bytes,
            max_age_hours=args.max_age_hours,
        ),
    )
    print(f"Backup check passed: {result['path']} ({result['size_bytes']} bytes).")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a MySQL backup file before release work.")
    parser.add_argument("--path", required=True, help="Path to the MySQL backup file to validate.")
    parser.add_argument("--min-bytes", type=int, default=1, help="Minimum accepted backup size in bytes.")
    parser.add_argument("--max-age-hours", type=float, default=None, help="Maximum accepted backup age in hours.")
    parser.add_argument("--artifact-json", help="Optional path for a machine-readable job artifact.")
    return parser.parse_args()


if __name__ == "__main__":
    main()
