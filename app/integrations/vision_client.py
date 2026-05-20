"""Vision provider integrations."""

from __future__ import annotations

import json
import re
from typing import Any, Protocol

from app.core.config import settings
from app.integrations.media_url import resolve_public_media_url


class VisionClient(Protocol):
    async def recognize(self, image_url: str) -> dict[str, Any]:
        ...


class MockVisionClient:
    async def recognize(self, image_url: str) -> dict[str, Any]:
        _ = image_url
        category = "机械键盘"
        features = ["白色", "无线", "紧凑布局"]
        return {
            "category": category,
            "features": features,
            "query": " ".join([*features, category]),
        }


class LlmVisionClient:
    def __init__(self, client: Any | None = None, model: str | None = None) -> None:
        self.model = model or settings.llm_model
        self.client = client or self._create_client()

    async def recognize(self, image_url: str) -> dict[str, Any]:
        public_url = resolve_public_media_url(image_url, field_name="image_url")
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是电商识图助手。只返回 JSON，字段为 "
                        "category:string, features:string[], query:string。"
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "识别图片中的商品类别、关键特征，并生成中文搜索 query。",
                        },
                        {"type": "image_url", "image_url": {"url": public_url}},
                    ],
                },
            ],
            temperature=0.1,
        )
        content = response.choices[0].message.content or "{}"
        return parse_vision_json(content)

    def _create_client(self) -> Any:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:  # pragma: no cover - dependency is in requirements.
            raise RuntimeError("openai package is required for LLM vision provider") from exc

        if not settings.llm_api_key:
            raise RuntimeError("LLM_API_KEY is required for LLM vision provider")
        return AsyncOpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
        )


def parse_vision_json(content: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", content, re.S)
    raw = match.group(0) if match else content
    data = json.loads(raw)

    category = str(data.get("category") or "").strip()
    features = [str(item).strip() for item in data.get("features") or [] if str(item).strip()]
    query = str(data.get("query") or " ".join([*features, category])).strip()
    return {
        "category": category,
        "features": features,
        "query": query,
    }
