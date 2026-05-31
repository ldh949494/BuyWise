"""Machine-readable artifact helpers for maintenance scripts."""

from __future__ import annotations

import getpass
import json
import os
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypeVar

from app.core.config import settings

T = TypeVar("T")


def run_job_with_artifact(
    *,
    job_name: str,
    inputs: dict[str, Any],
    artifact_path: str | Path | None,
    action: Callable[[], T],
) -> T:
    started = datetime.now(timezone.utc)
    started_perf = time.perf_counter()
    try:
        output = action()
    except Exception as exc:
        _record_failure(artifact_path, job_name, inputs, started, started_perf, exc)
        raise
    _record_success(artifact_path, job_name, inputs, started, started_perf, output)
    return output


def _record_success(
    artifact_path: str | Path | None,
    job_name: str,
    inputs: dict[str, Any],
    started_at: datetime,
    started_perf: float,
    output: Any,
) -> None:
    payload = _artifact_payload(
        job_name=job_name,
        started_at=started_at,
        duration_ms=_duration_ms(started_perf),
        status="succeeded",
        inputs=inputs,
        output=output,
        error=None,
    )
    _write_artifact(artifact_path, payload=payload)


def _record_failure(
    artifact_path: str | Path | None,
    job_name: str,
    inputs: dict[str, Any],
    started_at: datetime,
    started_perf: float,
    exc: Exception,
) -> None:
    payload = _artifact_payload(
        job_name=job_name,
        started_at=started_at,
        duration_ms=_duration_ms(started_perf),
        status="failed",
        inputs=inputs,
        output=None,
        error={"type": type(exc).__name__, "message": str(exc)},
    )
    _write_artifact(artifact_path, payload=payload)


def _write_artifact(
    artifact_path: str | Path | None,
    *,
    payload: dict[str, Any],
) -> None:
    if not artifact_path:
        return
    path = Path(artifact_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_format_json(payload), encoding="utf-8")


def _artifact_payload(
    *,
    job_name: str,
    started_at: datetime,
    duration_ms: int,
    status: str,
    inputs: dict[str, Any],
    output: Any,
    error: dict[str, str] | None,
) -> dict[str, Any]:
    finished_at = datetime.now(timezone.utc)
    return {
        "job_name": job_name,
        "status": status,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_ms": duration_ms,
        "inputs": inputs,
        "output": output,
        "error": error,
        "environment": _environment(),
    }


def _format_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _environment() -> dict[str, str]:
    return {
        "app_env": settings.app_env,
        "cwd": os.getcwd(),
        "operator": os.environ.get("BUYWISE_JOB_OPERATOR") or getpass.getuser(),
    }


def _duration_ms(started_perf: float) -> int:
    return round((time.perf_counter() - started_perf) * 1000)
