from pathlib import Path

from app.scripts.openapi_contract import check_snapshot, write_snapshot


def test_openapi_contract_write_and_check_round_trip(tmp_path: Path) -> None:
    snapshot = tmp_path / "openapi.json"

    write_snapshot(snapshot)

    assert check_snapshot(snapshot) == []


def test_openapi_contract_reports_drift(tmp_path: Path) -> None:
    snapshot = tmp_path / "openapi.json"
    snapshot.write_text("{}\n", encoding="utf-8")

    failures = check_snapshot(snapshot)

    assert failures == ["OpenAPI snapshot is out of date. Run python -m app.scripts.openapi_contract --write."]
