from datetime import datetime, timedelta, timezone
from os import utime

from app.scripts.cleanup_uploads import cleanup_uploads


def test_cleanup_uploads_deletes_only_expired_allowed_files(tmp_path) -> None:
    now = datetime(2026, 5, 22, tzinfo=timezone.utc)
    old_png = tmp_path / "old.png"
    fresh_png = tmp_path / "fresh.png"
    old_txt = tmp_path / "old.txt"
    old_png.write_bytes(b"old image")
    fresh_png.write_bytes(b"fresh image")
    old_txt.write_bytes(b"old text")
    old_time = (now - timedelta(hours=25)).timestamp()
    fresh_time = (now - timedelta(hours=1)).timestamp()
    utime(old_png, (old_time, old_time))
    utime(old_txt, (old_time, old_time))
    utime(fresh_png, (fresh_time, fresh_time))

    report = cleanup_uploads(tmp_path, max_age_hours=24, now=now)

    assert report.as_dict() == {
        "scanned": 3,
        "deleted": 1,
        "skipped": 2,
        "bytes_freed": len(b"old image"),
        "dry_run": False,
    }
    assert not old_png.exists()
    assert fresh_png.exists()
    assert old_txt.exists()


def test_cleanup_uploads_dry_run_keeps_files(tmp_path) -> None:
    now = datetime(2026, 5, 22, tzinfo=timezone.utc)
    old_wav = tmp_path / "old.wav"
    old_wav.write_bytes(b"audio")
    old_time = (now - timedelta(hours=48)).timestamp()
    utime(old_wav, (old_time, old_time))

    report = cleanup_uploads(tmp_path, max_age_hours=24, dry_run=True, now=now)

    assert report.deleted == 1
    assert report.bytes_freed == len(b"audio")
    assert report.dry_run is True
    assert old_wav.exists()
