"""Generate and verify the committed OpenAPI contract snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.main import create_app


DEFAULT_SNAPSHOT = Path("docs/reference/openapi.snapshot.json")


def build_openapi_snapshot() -> dict[str, Any]:
    return create_app().openapi()


def write_snapshot(path: Path = DEFAULT_SNAPSHOT) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_format_json(build_openapi_snapshot()), encoding="utf-8")


def check_snapshot(path: Path = DEFAULT_SNAPSHOT) -> list[str]:
    expected = _format_json(build_openapi_snapshot())
    if not path.exists():
        return [f"OpenAPI snapshot is missing: {path}"]
    actual = path.read_text(encoding="utf-8")
    if actual != expected:
        return ["OpenAPI snapshot is out of date. Run python -m app.scripts.openapi_contract --write."]
    return []


def main() -> None:
    args = _parse_args()
    path = Path(args.snapshot)
    if args.write:
        write_snapshot(path)
        print(f"OpenAPI snapshot written: {path}")
        return
    failures = check_snapshot(path)
    if failures:
        for failure in failures:
            print(failure)
        raise SystemExit(1)
    print(f"OpenAPI snapshot matches: {path}")


def _format_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate or verify BuyWise OpenAPI contract snapshot.")
    parser.add_argument("--snapshot", default=str(DEFAULT_SNAPSHOT), help="OpenAPI snapshot path.")
    parser.add_argument("--write", action="store_true", help="Write the current OpenAPI schema to the snapshot.")
    return parser.parse_args()


if __name__ == "__main__":
    main()
