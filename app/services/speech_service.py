"""Speech service."""


class SpeechService:
    """Mock speech service, replaceable with Tencent ASR later."""

    async def transcribe(self, audio_url: str) -> str:
        _ = audio_url
        return "\u6211\u60f3\u4e70\u4e00\u4e2a\u5bbf\u820d\u7528\u7684\u673a\u68b0\u952e\u76d8\uff0c\u9884\u7b97\u4e09\u767e\u4ee5\u5185"
