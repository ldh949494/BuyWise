import json
from pathlib import Path

import pytest

from app.scripts.job_artifacts import run_job_with_artifact


def test_run_job_with_artifact_records_success(tmp_path: Path) -> None:
    artifact = tmp_path / "job.json"

    result = run_job_with_artifact(
        job_name="demo_job",
        inputs={"value": 1},
        artifact_path=artifact,
        action=lambda: {"ok": True},
    )

    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert result == {"ok": True}
    assert payload["job_name"] == "demo_job"
    assert payload["status"] == "succeeded"
    assert payload["inputs"] == {"value": 1}
    assert payload["output"] == {"ok": True}
    assert payload["error"] is None
    assert payload["duration_ms"] >= 0
    assert payload["environment"]["operator"]


def test_run_job_with_artifact_records_failure(tmp_path: Path) -> None:
    artifact = tmp_path / "job.json"

    with pytest.raises(ValueError, match="bad input"):
        run_job_with_artifact(
            job_name="demo_job",
            inputs={"value": 1},
            artifact_path=artifact,
            action=lambda: (_ for _ in ()).throw(ValueError("bad input")),
        )

    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert payload["output"] is None
    assert payload["error"] == {"type": "ValueError", "message": "bad input"}
