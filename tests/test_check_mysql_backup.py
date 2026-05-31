from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from app.scripts.check_mysql_backup import check_mysql_backup, main


def test_check_mysql_backup_records_valid_backup_artifact(tmp_path: Path, monkeypatch) -> None:
    backup = tmp_path / "backup.sql"
    backup.write_text("create table products(id int);\n", encoding="utf-8")
    artifact = tmp_path / "backup-check.json"

    result = check_mysql_backup(backup, min_bytes=10, max_age_hours=1)

    monkeypatch.setattr(
        "sys.argv",
        [
            "check_mysql_backup",
            "--path",
            str(backup),
            "--min-bytes",
            "10",
            "--max-age-hours",
            "1",
            "--artifact-json",
            str(artifact),
        ],
    )
    main()

    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert result["ok"] is True
    assert result["path"] == str(backup)
    assert result["size_bytes"] >= 10
    assert payload["job_name"] == "check_mysql_backup"
    assert payload["status"] == "succeeded"
    assert payload["inputs"] == {"path": str(backup), "min_bytes": 10, "max_age_hours": 1.0}
    assert payload["output"]["ok"] is True


def test_check_mysql_backup_rejects_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.sql"

    with pytest.raises(FileNotFoundError, match="Backup file not found"):
        check_mysql_backup(missing)


def test_check_mysql_backup_rejects_stale_file(tmp_path: Path) -> None:
    backup = tmp_path / "backup.sql"
    backup.write_text("old backup\n", encoding="utf-8")
    old_timestamp = time.time() - (3 * 60 * 60)
    os.utime(backup, (old_timestamp, old_timestamp))

    with pytest.raises(ValueError, match="older than 1.0 hours"):
        check_mysql_backup(backup, max_age_hours=1)
