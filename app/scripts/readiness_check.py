"""Run detailed readiness checks for deployment verification."""

from __future__ import annotations

import json

from app.services.readiness_service import validate_readiness


def main() -> None:
    report = validate_readiness(include_details=True)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "ready":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
