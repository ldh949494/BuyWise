import pytest

from app.scripts import check_vector_index


def test_check_vector_index_exits_nonzero_when_unhealthy(monkeypatch) -> None:
    monkeypatch.setattr(
        check_vector_index,
        "validate_vector_index_health",
        lambda expected_product_ids=None, profile=None: {"ok": False, "missing_in_index": [1], "stale_in_index": []},
    )
    monkeypatch.setattr(check_vector_index, "known_seed_product_ids", lambda profile: set())
    monkeypatch.setattr("sys.argv", ["check_vector_index.py"])

    with pytest.raises(SystemExit) as exc_info:
        check_vector_index.main()

    assert exc_info.value.code == 1


def test_check_vector_index_allows_healthy_report(monkeypatch) -> None:
    monkeypatch.setattr(
        check_vector_index,
        "validate_vector_index_health",
        lambda expected_product_ids=None, profile=None: {"ok": True, "missing_in_index": [], "stale_in_index": []},
    )
    monkeypatch.setattr(check_vector_index, "known_seed_product_ids", lambda profile: set())
    monkeypatch.setattr("sys.argv", ["check_vector_index.py"])

    check_vector_index.main()
