class SpeechService:
    """Reserved service for future speech-to-text workflows."""

    async def transcribe(self, audio_url: str) -> str:
        return f"语音内容来自：{audio_url}"
