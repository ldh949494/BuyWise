from fastapi.testclient import TestClient

from app.api.v1.chat import get_chat_service
from app.api.v1.compare import get_compare_service
from app.api.v1.rag import get_rag_service
from app.core.config import Settings, settings
from app.core.database import get_db
from app.core.dependencies import AppContainerBuilder
from app.main import create_app
from app.schemas.chat import ChatResponse
from app.schemas.compare import CompareResponse
from app.schemas.rag import RagSearchResponse


def test_create_app_applies_cors_policy() -> None:
    settings.cors_allowed_origins = "https://app.example.com"
    settings.cors_allow_credentials = False

    response = TestClient(create_app()).options(
        "/api/v1/health",
        headers={
            "Origin": "https://app.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://app.example.com"


def test_production_config_validation_rejects_insecure_settings() -> None:
    config = Settings(
        app_env="prod",
        app_debug=True,
        mysql_password="change-me",
        auth_api_keys="api:change-me:upload:write",
        readiness_token="change-me",
        cors_allowed_origins="",
        llm_provider="openai",
        llm_api_key="change-me",
    )

    try:
        config.validate_production()
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected production validation to fail.")

    assert "APP_DEBUG" in message
    assert "AUTH_API_KEYS" in message
    assert "LLM_API_KEY" in message
    assert "READINESS_TOKEN" in message


def test_readiness_requires_token_in_prod() -> None:
    settings.app_env = "prod"
    settings.app_debug = False
    settings.mysql_password = "secret"
    settings.auth_api_keys = "api:token:orders:read"
    settings.readiness_token = "ready-token"
    settings.allow_mock_providers_in_prod = True

    class FakeReadinessService:
        def validate_readiness(self, include_details=False):
            return {"status": "ready", "service": "buywise-backend", "checks": {}}

    app = create_app(AppContainerBuilder().with_readiness_service(FakeReadinessService()))
    client = TestClient(app)

    missing = client.get("/api/v1/ready")
    allowed = client.get("/api/v1/ready", headers={"X-Readiness-Token": "ready-token"})

    assert missing.status_code == 401
    assert allowed.status_code == 200
    assert allowed.json()["status"] == "ready"


def test_high_cost_android_contract_routes_remain_public() -> None:
    class FakeChatService:
        async def handle_chat(self, request, db):
            return ChatResponse(reply="公开导购响应", extra={"session_id": "public"})

    class FakeCompareService:
        async def compare(self, product_ids, user_need, db):
            return CompareResponse(items=[], summary="公开对比响应", winner_id=None)

    class FakeRagService:
        def search(self, request, db):
            return RagSearchResponse(query=request.query, items=[], total=0)

    def override_get_db():
        yield object()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_chat_service] = lambda: FakeChatService()
    app.dependency_overrides[get_compare_service] = lambda: FakeCompareService()
    app.dependency_overrides[get_rag_service] = lambda: FakeRagService()
    client = TestClient(app)

    chat = client.post("/api/v1/ai/chat", json={"message": "推荐一个键盘"})
    compare = client.post("/api/v1/products/compare", json={"product_ids": [1, 2]})
    rag = client.post("/api/v1/rag/search", json={"query": "机械键盘"})

    assert chat.status_code == 200
    assert compare.status_code == 200
    assert rag.status_code == 200
