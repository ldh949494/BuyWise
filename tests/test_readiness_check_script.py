import pytest

from app.scripts import readiness_check


def test_readiness_check_passes_expected_active_products(monkeypatch) -> None:
    captured = {}

    def fake_validate_readiness(include_details=False, expected_active_products=None):
        captured["include_details"] = include_details
        captured["expected_active_products"] = expected_active_products
        return {"status": "ready", "service": "buywise-backend", "checks": {}}

    monkeypatch.setattr(readiness_check, "validate_readiness", fake_validate_readiness)
    monkeypatch.setattr("sys.argv", ["readiness_check.py", "--expected-active-products", "50"])

    readiness_check.main()

    assert captured == {"include_details": True, "expected_active_products": 50}


def test_readiness_check_exits_nonzero_when_not_ready(monkeypatch) -> None:
    monkeypatch.setattr(
        readiness_check,
        "validate_readiness",
        lambda include_details=False, expected_active_products=None: {
            "status": "not_ready",
            "service": "buywise-backend",
            "checks": {"products": {"status": "failed", "product_count": 49}},
        },
    )
    monkeypatch.setattr("sys.argv", ["readiness_check.py", "--expected-active-products", "50"])

    with pytest.raises(SystemExit) as exc_info:
        readiness_check.main()

    assert exc_info.value.code == 1
