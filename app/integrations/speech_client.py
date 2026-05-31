"""Speech-to-text provider integrations."""

from __future__ import annotations

from urllib.parse import urlparse

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
        try:
            from tencentcloud.asr.v20190614 import asr_client, models
            from tencentcloud.common import credential
            from tencentcloud.common.profile.client_profile import ClientProfile
            from tencentcloud.common.profile.http_profile import HttpProfile
        except ImportError as exc:
            raise RuntimeError("tencentcloud-sdk-python is required for Tencent ASR") from exc

        cred = credential.Credential(settings.tencent_secret_id, settings.tencent_secret_key)
        http_profile = HttpProfile()
        http_profile.endpoint = "asr.tencentcloudapi.com"
        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile
        client = asr_client.AsrClient(cred, settings.tencent_asr_region, client_profile)

        request = models.SentenceRecognitionRequest()
        request.ProjectId = 0
        request.SubServiceType = 2
        request.EngSerViceType = settings.tencent_asr_engine_model_type
        request.SourceType = 0
        request.Url = audio_url
        request.VoiceFormat = resolve_tencent_voice_format(audio_url)

        response = client.SentenceRecognition(request)
        return response.Result or ""

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
