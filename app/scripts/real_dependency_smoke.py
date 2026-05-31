"""Smoke checks for real or sandbox external dependencies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.integrations.cos_storage_client import TencentCosStorageClient


def run_real_dependency_smoke(checks: list[str]) -> dict[str, Any]:
    results = {}
    if "mysql" in checks:
        results["mysql"] = check_mysql_connection()
    if "cos" in checks:
        results["cos"] = check_cos_read_access()
    return {"status": _overall_status(results), "checks": results}


def check_mysql_connection() -> dict[str, Any]:
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    try:
        if engine.dialect.name != "mysql":
            return _failed(f"Expected mysql dialect, got {engine.dialect.name}.")
        with engine.connect() as connection:
            value = connection.execute(text("SELECT 1")).scalar_one()
        return _ok({"dialect": engine.dialect.name, "select_one": int(value)})
    except SQLAlchemyError as exc:
        return _failed(str(exc))
    finally:
        engine.dispose()


def check_cos_read_access(client: TencentCosStorageClient | None = None) -> dict[str, Any]:
    try:
        result = (client or TencentCosStorageClient()).check_bucket_read_access()
        return _ok(result)
    except Exception as exc:
        return _failed(str(exc))


def main() -> None:
    args = _parse_args()
    report = run_real_dependency_smoke(args.check)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if report["status"] != "ok":
        raise SystemExit(1)


def _ok(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"status": "ok", **(extra or {})}


def _failed(reason: str) -> dict[str, str]:
    return {"status": "failed", "reason": reason}


def _overall_status(results: dict[str, dict[str, Any]]) -> str:
    return "ok" if results and all(result["status"] == "ok" for result in results.values()) else "failed"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run real dependency smoke checks.")
    parser.add_argument("--check", action="append", choices=["mysql", "cos"], required=True)
    parser.add_argument("--output-json", help="Optional path for a machine-readable smoke report.")
    return parser.parse_args()


if __name__ == "__main__":
    main()
