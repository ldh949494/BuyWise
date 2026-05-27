from app.scripts import print_runtime_config_summary


def test_runtime_config_summary_excludes_secret_values(monkeypatch) -> None:
    settings = print_runtime_config_summary.settings
    monkeypatch.setattr(settings, "app_env", "prod")
    monkeypatch.setattr(settings, "app_debug", False)
    monkeypatch.setattr(settings, "allow_mock_providers_in_prod", False)
    monkeypatch.setattr(settings, "llm_provider", "openai-compatible")
    monkeypatch.setattr(settings, "embedding_provider", "dashscope")
    monkeypatch.setattr(settings, "vision_provider", "dashscope")
    monkeypatch.setattr(settings, "speech_provider", "mock")
    monkeypatch.setattr(settings, "upload_provider", "cos")
    monkeypatch.setattr(settings, "mysql_host", "mysql")
    monkeypatch.setattr(settings, "mysql_database", "buywise")
    monkeypatch.setattr(settings, "chroma_persist_dir", "/app/vector_store/chroma")
    monkeypatch.setattr(settings, "chroma_product_collection", "buywise_products")
    monkeypatch.setattr(settings, "llm_api_key", "secret-key")
    monkeypatch.setattr(settings, "mysql_password", "secret-password")
    monkeypatch.setattr(settings, "readiness_token", "secret-readiness-token")

    summary = print_runtime_config_summary.runtime_config_summary()

    assert summary["app_env"] == "prod"
    assert summary["llm_provider"] == "openai-compatible"
    assert "llm_api_key" not in summary
    assert "mysql_password" not in summary
    assert "readiness_token" not in summary
    assert "secret-key" not in str(summary)
