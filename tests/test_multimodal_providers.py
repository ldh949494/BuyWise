import asyncio

import pytest

from app.core.config import settings
from app.integrations.media_url import resolve_public_media_url
from app.integrations.speech_client import MockSpeechClient, TencentSpeechClient, resolve_tencent_voice_format
from app.integrations.vision_client import LlmVisionClient, MockVisionClient, parse_vision_json
from app.services.speech_service import SpeechService
from app.services.vision_service import VisionService


def test_vision_service_uses_injected_client() -> None:
    class FakeVisionClient:
        async def recognize(self, image_url: str) -> dict:
            assert image_url == "https://cdn.example.com/demo.png"
            return {
                "category": "台灯",
                "features": ["护眼"],
                "query": "护眼 台灯",
            }

    service = VisionService(client=FakeVisionClient())

    result = asyncio.run(service.recognize("https://cdn.example.com/demo.png"))

    assert result["category"] == "台灯"
    assert result["features"] == ["护眼"]


def test_speech_service_uses_injected_client() -> None:
    class FakeSpeechClient:
        async def transcribe(self, audio_url: str) -> str:
            assert audio_url == "https://cdn.example.com/demo.wav"
            return "想买护眼台灯"

    service = SpeechService(client=FakeSpeechClient())

    result = asyncio.run(service.transcribe("https://cdn.example.com/demo.wav"))

    assert result == "想买护眼台灯"


def test_mock_clients_preserve_existing_contract() -> None:
    vision = asyncio.run(MockVisionClient().recognize("/uploads/demo.png"))
    speech = asyncio.run(MockSpeechClient().transcribe("/uploads/demo.wav"))

    assert vision == {
        "category": "机械键盘",
        "features": ["白色", "无线", "紧凑布局"],
        "query": "白色 无线 紧凑布局 机械键盘",
    }
    assert speech == "我想买一个宿舍用的机械键盘，预算三百以内"


def test_parse_vision_json_extracts_json_from_model_text() -> None:
    result = parse_vision_json(
        '```json\n{"category":"蓝牙耳机","features":["降噪","通勤"],"query":"降噪 通勤 蓝牙耳机"}\n```'
    )

    assert result == {
        "category": "蓝牙耳机",
        "features": ["降噪", "通勤"],
        "query": "降噪 通勤 蓝牙耳机",
    }


def test_llm_vision_client_sends_public_image_url_to_model() -> None:
    class FakeCompletions:
        async def create(self, **kwargs):
            user_content = kwargs["messages"][1]["content"]
            assert user_content[1]["image_url"]["url"] == "https://api.example.com/uploads/demo.png"
            assert kwargs["model"] == "qwen-vl-plus"
            message = type(
                "Message",
                (),
                {"content": '{"category":"双肩包","features":["轻便"],"query":"轻便 双肩包"}'},
            )()
            choice = type("Choice", (), {"message": message})()
            return type("Response", (), {"choices": [choice]})()

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        chat = FakeChat()

    previous = settings.upload_public_base_url
    previous_model = settings.vision_model
    settings.upload_public_base_url = "https://api.example.com"
    settings.vision_model = "qwen-vl-plus"
    try:
        result = asyncio.run(LlmVisionClient(client=FakeClient()).recognize("/uploads/demo.png"))
    finally:
        settings.upload_public_base_url = previous
        settings.vision_model = previous_model

    assert result["category"] == "双肩包"
    assert result["query"] == "轻便 双肩包"


def test_public_media_url_joins_relative_upload_path() -> None:
    previous = settings.upload_public_base_url
    settings.upload_public_base_url = "https://api.example.com"
    try:
        assert (
            resolve_public_media_url("/uploads/demo.wav", field_name="audio_url")
            == "https://api.example.com/uploads/demo.wav"
        )
    finally:
        settings.upload_public_base_url = previous


def test_public_media_url_requires_base_for_relative_upload_path() -> None:
    previous = settings.upload_public_base_url
    settings.upload_public_base_url = ""
    try:
        with pytest.raises(Exception) as exc_info:
            resolve_public_media_url("/uploads/demo.wav", field_name="audio_url")
    finally:
        settings.upload_public_base_url = previous

    assert getattr(exc_info.value, "code") == "media_url_not_public"


def test_tencent_speech_client_resolves_public_url_before_sdk_call(monkeypatch) -> None:
    previous_base = settings.upload_public_base_url
    previous_secret_id = settings.tencent_secret_id
    previous_secret_key = settings.tencent_secret_key
    settings.upload_public_base_url = "https://api.example.com"
    settings.tencent_secret_id = "sid"
    settings.tencent_secret_key = "skey"
    captured = {}

    def fake_transcribe_sync(self, audio_url: str) -> str:
        captured["audio_url"] = audio_url
        return "识别文本"

    monkeypatch.setattr(TencentSpeechClient, "_transcribe_sync", fake_transcribe_sync)
    try:
        result = asyncio.run(TencentSpeechClient().transcribe("/uploads/demo.wav"))
    finally:
        settings.upload_public_base_url = previous_base
        settings.tencent_secret_id = previous_secret_id
        settings.tencent_secret_key = previous_secret_key

    assert captured["audio_url"] == "https://api.example.com/uploads/demo.wav"
    assert result == "识别文本"


def test_tencent_voice_format_uses_configured_override() -> None:
    previous = settings.tencent_asr_voice_format
    settings.tencent_asr_voice_format = "mp3"
    try:
        assert resolve_tencent_voice_format("https://cdn.example.com/audio.wav") == "mp3"
    finally:
        settings.tencent_asr_voice_format = previous


def test_tencent_voice_format_infers_from_audio_url() -> None:
    previous = settings.tencent_asr_voice_format
    settings.tencent_asr_voice_format = ""
    try:
        assert resolve_tencent_voice_format("https://cdn.example.com/audio.wav?token=1") == "wav"
        assert resolve_tencent_voice_format("https://cdn.example.com/audio.mp3") == "mp3"
        assert resolve_tencent_voice_format("https://cdn.example.com/audio") == "wav"
    finally:
        settings.tencent_asr_voice_format = previous
