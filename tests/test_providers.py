import json
import logging

from fastapi import FastAPI
from fastapi import Depends
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.providers import (
    AuthProvider,
    ErrorProvider,
    JsonFormatter,
    LoggingProvider,
    MiddlewareProvider,
    TelemetryProvider,
    get_middleware_provider,
    get_provider,
    require_principal,
)


def test_get_provider_returns_cross_cutting_providers() -> None:
    assert isinstance(get_provider("auth"), AuthProvider)
    assert isinstance(get_provider("telemetry"), TelemetryProvider)
    assert isinstance(get_provider("logging"), LoggingProvider)
    assert isinstance(get_provider("errors"), ErrorProvider)
    assert isinstance(get_provider("middleware"), MiddlewareProvider)


def test_auth_provider_defaults_to_anonymous_context() -> None:
    auth = get_provider("auth")

    assert auth.get_current_principal() is None


def test_auth_dependency_accepts_bearer_api_key() -> None:
    settings.auth_api_keys = "android:test-token:upload:write"
    app = FastAPI()

    @app.get("/secure")
    def secure(principal=Depends(require_principal(("upload:write",)))) -> dict[str, object]:
        return {"subject": principal.subject, "scopes": list(principal.scopes)}

    response = TestClient(app).get("/secure", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    assert response.json() == {"subject": "android", "scopes": ["upload:write"]}


def test_auth_dependency_rejects_missing_and_insufficient_tokens() -> None:
    settings.auth_api_keys = "android:test-token:upload:write"
    app = FastAPI()
    get_provider("errors").register_exception_handlers(app)

    @app.get("/secure")
    def secure(principal=Depends(require_principal(("products:write",)))) -> dict[str, str]:
        return {"subject": principal.subject}

    missing = TestClient(app).get("/secure")
    insufficient = TestClient(app).get("/secure", headers={"Authorization": "Bearer test-token"})

    assert missing.status_code == 401
    assert missing.json()["code"] == "unauthorized"
    assert insufficient.status_code == 403
    assert insufficient.json()["code"] == "forbidden"


def test_error_provider_registers_without_side_effect_error() -> None:
    app = FastAPI()
    errors = get_provider("errors")

    errors.register_exception_handlers(app)

    assert isinstance(app, FastAPI)


def test_json_formatter_includes_request_id_and_extra_fields() -> None:
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Product search completed",
        args=(),
        exc_info=None,
    )
    record.category = "phone"

    payload = json.loads(JsonFormatter().format(record))

    assert payload["message"] == "Product search completed"
    assert "request_id" in payload
    assert payload["category"] == "phone"


def test_json_formatter_redacts_sensitive_extra_fields() -> None:
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Sensitive event",
        args=(),
        exc_info=None,
    )
    record.api_key = "secret-key"
    record.context = {"password": "pass", "safe": "value"}

    payload = json.loads(JsonFormatter().format(record))

    assert payload["api_key"] == "[redacted]"
    assert payload["context"] == {"password": "[redacted]", "safe": "value"}


def test_logging_provider_configures_log_level() -> None:
    get_provider("logging").configure(level="WARNING")

    assert logging.getLogger().level == logging.WARNING
    assert logging.getLogger("uvicorn").level == logging.WARNING
    get_provider("logging").configure(level="INFO")


def test_middleware_generates_request_id_for_success_response() -> None:
    app = FastAPI()
    get_middleware_provider().register_middleware(app)

    @app.get("/ok")
    def ok() -> dict[str, str]:
        return {"status": "ok"}

    response = TestClient(app).get("/ok")

    assert response.status_code == 200
    assert response.headers["x-request-id"]


def test_middleware_logs_request_completion(caplog) -> None:
    app = FastAPI()
    get_middleware_provider().register_middleware(app)
    caplog.set_level(logging.INFO, logger="app.middleware")

    @app.get("/ok")
    def ok() -> dict[str, str]:
        return {"status": "ok"}

    response = TestClient(app).get("/ok")

    records = [record for record in caplog.records if record.message == "Request completed"]
    assert response.status_code == 200
    assert records
    assert records[-1].method == "GET"
    assert records[-1].path == "/ok"
    assert records[-1].status_code == 200
    assert records[-1].duration_ms >= 0


def test_middleware_echoes_incoming_request_id() -> None:
    app = FastAPI()
    get_middleware_provider().register_middleware(app)

    @app.get("/ok")
    def ok() -> dict[str, str]:
        return {"status": "ok"}

    response = TestClient(app).get("/ok", headers={"X-Request-ID": "req-123"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req-123"


def test_middleware_rejects_oversized_requests() -> None:
    settings.request_max_bytes = 4
    app = FastAPI()
    get_middleware_provider().register_middleware(app)

    @app.post("/items")
    async def items() -> dict[str, str]:
        return {"status": "ok"}

    response = TestClient(app).post("/items", content=b"too large")

    assert response.status_code == 413
    assert response.json()["code"] == "request_too_large"
    settings.request_max_bytes = 20 * 1024 * 1024


def test_error_provider_renders_app_error_with_request_id() -> None:
    app = FastAPI()
    get_middleware_provider().register_middleware(app)
    get_provider("errors").register_exception_handlers(app)

    @app.get("/fail")
    def fail() -> None:
        raise AppError("Bad input", status_code=409, code="conflict")

    response = TestClient(app).get("/fail", headers={"X-Request-ID": "req-456"})

    assert response.status_code == 409
    assert response.headers["x-request-id"] == "req-456"
    assert response.json() == {
        "detail": "Bad input",
        "code": "conflict",
        "extra": {"request_id": "req-456"},
    }


def test_error_provider_renders_validation_errors() -> None:
    app = FastAPI()
    get_middleware_provider().register_middleware(app)
    get_provider("errors").register_exception_handlers(app)

    @app.get("/items/{item_id}")
    def item(item_id: int) -> dict[str, int]:
        return {"item_id": item_id}

    response = TestClient(app).get("/items/not-an-int", headers={"X-Request-ID": "req-789"})

    assert response.status_code == 422
    payload = response.json()
    assert payload["detail"] == "Request validation failed"
    assert payload["code"] == "validation_error"
    assert payload["extra"]["request_id"] == "req-789"
    assert payload["extra"]["errors"]


def test_error_provider_redacts_sensitive_validation_input() -> None:
    class LoginRequest(BaseModel):
        token: int

    app = FastAPI()
    get_middleware_provider().register_middleware(app)
    get_provider("errors").register_exception_handlers(app)

    @app.post("/login")
    def login(request: LoginRequest) -> dict[str, int]:
        return {"token": request.token}

    response = TestClient(app).post("/login", json={"token": "secret-value"})

    assert response.status_code == 422
    errors = response.json()["extra"]["errors"]
    assert errors[0]["input"] == "[redacted]"


def test_error_provider_hides_unexpected_exception_details() -> None:
    app = FastAPI()
    get_middleware_provider().register_middleware(app)
    get_provider("errors").register_exception_handlers(app)

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError("database password leaked")

    response = TestClient(app, raise_server_exceptions=False).get(
        "/boom",
        headers={"X-Request-ID": "req-999"},
    )

    assert response.status_code == 500
    assert response.headers["x-request-id"] == "req-999"
    assert response.json() == {
        "detail": "Internal server error",
        "code": "internal_error",
        "extra": {"request_id": "req-999"},
    }

