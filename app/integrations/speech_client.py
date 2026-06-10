"""Speech-to-text provider integrations."""

from __future__ import annotations

from urllib.parse import urlparse

from typing import Any
from typing import Protocol

from app.core.concurrency import run_blocking_io
from app.core.config import settings
from app.core.providers import AppError
from app.core.resilience import provider_policy, run_provider_call_async
from app.integrations.media_url import resolve_public_media_url


class SpeechClient(Protocol):
    async def transcribe(self, audio_url: str) -> str:
        ...


class MockSpeechClient:
    async def transcribe(self, audio_url: str) -> str:
        _ = audio_url
        return "我想买一个宿舍用的机械键盘，预算三百以内"


class TencentSpeechClient:
    async def transcribe(self, audio_url: str) -> str:
        public_url = resolve_public_media_url(audio_url, field_name="audio_url")
        return await run_provider_call_async(
            provider_policy("speech", "transcribe"),
            lambda: run_blocking_io(self._transcribe_sync, public_url),
            capacity_resource="speech",
        )

    def _transcribe_sync(self, audio_url: str) -> str:
        self._validate_settings()
        modules = self._load_tencent_modules()
        client = self._build_tencent_client(modules)
        request = self._build_tencent_request(modules["models"], audio_url)
        response = self._send_tencent_request(client, request)
        return response.Result or ""

    def _load_tencent_modules(self) -> dict[str, Any]:
        try:
            from tencentcloud.asr.v20190614 import asr_client, models
            from tencentcloud.common import credential
            from tencentcloud.common.profile.client_profile import ClientProfile
            from tencentcloud.common.profile.http_profile import HttpProfile
        except ImportError as exc:
            raise AppError(
                "tencentcloud-sdk-python is required for Tencent ASR.",
                status_code=500,
                code="speech_provider_dependency_missing",
            ) from exc

        return {
            "asr_client": asr_client,
            "models": models,
            "credential": credential,
            "ClientProfile": ClientProfile,
            "HttpProfile": HttpProfile,
        }

    def _build_tencent_client(self, modules: dict[str, Any]) -> Any:
        credential = modules["credential"]
        http_profile = modules["HttpProfile"]()
        http_profile.endpoint = "asr.tencentcloudapi.com"
        client_profile = modules["ClientProfile"]()
        client_profile.httpProfile = http_profile
        cred = credential.Credential(settings.tencent_secret_id, settings.tencent_secret_key)
        return modules["asr_client"].AsrClient(cred, settings.tencent_asr_region, client_profile)

    def _build_tencent_request(self, models: Any, audio_url: str) -> Any:
        request = models.SentenceRecognitionRequest()
        request.ProjectId = 0
        request.SubServiceType = 2
        request.EngSerViceType = settings.tencent_asr_engine_model_type
        request.SourceType = 0
        request.Url = audio_url
        request.VoiceFormat = resolve_tencent_voice_format(audio_url)
        return request

    def _send_tencent_request(self, client: Any, request: Any) -> Any:
        try:
            return client.SentenceRecognition(request)
        except Exception as exc:
            raise AppError(
                "Tencent ASR provider request failed.",
                status_code=503,
                code="provider_error",
                extra={"provider": "tencent_asr"},
            ) from exc

    def _validate_settings(self) -> None:
        if not settings.tencent_secret_id or not settings.tencent_secret_key:
            raise AppError(
                "Tencent ASR credentials are not configured.",
                status_code=500,
                code="speech_provider_not_configured",
            )


def resolve_tencent_voice_format(audio_url: str) -> str:
    configured = settings.tencent_asr_voice_format.strip().lower()
    if configured:
        return configured

    suffix = urlparse(audio_url).path.rsplit(".", 1)[-1].lower()
    if suffix in {"wav", "mp3", "m4a", "aac", "pcm", "ogg", "silk"}:
        return suffix
    return "wav"
