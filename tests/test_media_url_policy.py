import pytest

from app.core.config import settings
from app.core.providers import AppError
from app.services.media_url_policy import MediaUrlPolicy


def test_media_url_policy_blocks_private_hosts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ai_media_url_allowlist_enabled", True)
    monkeypatch.setattr(settings, "ai_media_allowed_hosts", "cdn.example.com")

    with pytest.raises(AppError) as exc:
        MediaUrlPolicy().validate("https://127.0.0.1/demo.png")

    assert exc.value.code == "media_url_not_allowed"


def test_media_url_policy_allows_configured_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ai_media_url_allowlist_enabled", True)
    monkeypatch.setattr(settings, "ai_media_allowed_hosts", "cdn.example.com")

    MediaUrlPolicy().validate("https://cdn.example.com/demo.png")
