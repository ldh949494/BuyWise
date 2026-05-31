import pytest

from app.scripts import readiness_check


class FakeContainer:
    def __init__(self, report, captured=None) -> None:
        self.report = report
        self.captured = captured if captured is not None else {}
        self.closed = False
        self.readiness_service = self

    def validate_readiness(self, include_details=False, expected_active_products=None):
        self.captured["include_details"] = include_details
        self.captured["expected_active_products"] = expected_active_products
        return self.report

    def close(self):
        self.closed = True


def test_readiness_check_passes_expected_active_products(monkeypatch) -> None:
    captured = {}
    container = FakeContainer({"status": "ready", "service": "buywise-backend", "checks": {}}, captured)
    monkeypatch.setattr(readiness_check, "build_app_container", lambda: container)
    monkeypatch.setattr("sys.argv", ["readiness_check.py", "--expected-active-products", "50"])

    readiness_check.main()

    assert captured == {"include_details": True, "expected_active_products": 50}
    assert container.closed is True


def test_readiness_check_exits_nonzero_when_not_ready(monkeypatch) -> None:
    container = FakeContainer(
        {
            "status": "not_ready",
            "service": "buywise-backend",
            "checks": {"products": {"status": "failed", "product_count": 49}},
        }
    )
    monkeypatch.setattr(readiness_check, "build_app_container", lambda: container)
    monkeypatch.setattr("sys.argv", ["readiness_check.py", "--expected-active-products", "50"])

    with pytest.raises(SystemExit) as exc_info:
        readiness_check.main()

    assert exc_info.value.code == 1
    assert container.closed is True
