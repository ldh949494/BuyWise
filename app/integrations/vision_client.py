"""Vision provider integrations."""

from __future__ import annotations

import json
import re
from typing import Any, Protocol

from app.core.config import settings
from app.core.resilience import provider_policy, run_provider_call_async
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
            "colors": ["白色"],
            "materials": [],
            "shape": "紧凑布局",
            "style": "简约",
            "brand_cues": [],
            "confidence": 0.92,
            "detected_objects": [category],
        }


class LlmVisionClient:
    def __init__(self, client: Any | None = None, model: str | None = None) -> None:
        self.model = model or settings.effective_vision_model
        self.client = client or self._create_client()

    async def recognize(self, image_url: str) -> dict[str, Any]:
        public_url = resolve_public_media_url(image_url, field_name="image_url")
        response = await run_provider_call_async(
            provider_policy("vision", "recognize"),
            lambda: self._recognize_with_provider(public_url),
            capacity_resource="vision",
        )
        content = response.choices[0].message.content or "{}"
        return parse_vision_json(content)

    async def _recognize_with_provider(self, public_url: str) -> Any:
        return await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是电商识图助手。只返回 JSON，字段为 "
                        "category:string, features:string[], query:string, "
                        "colors:string[], materials:string[], shape:string, "
                        "style:string, brand_cues:string[], confidence:number, "
                        "detected_objects:string[]。"
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "识别图片中的商品类别、颜色、材质、形状、风格、品牌线索和关键特征，并生成中文搜索 query。",
                        },
                        {"type": "image_url", "image_url": {"url": public_url}},
                    ],
                },
            ],
            temperature=0.1,
        )

    def _create_client(self) -> Any:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:  # pragma: no cover - dependency is in requirements.
            raise RuntimeError("openai package is required for LLM vision provider") from exc

        api_key = settings.effective_vision_api_key
        if not api_key:
            raise RuntimeError("VISION_API_KEY or LLM_API_KEY is required for LLM vision provider")
        return AsyncOpenAI(
            base_url=settings.effective_vision_base_url,
            api_key=api_key,
            timeout=provider_policy("vision", "recognize").timeout_seconds,
        )


def parse_vision_json(content: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", content, re.S)
    raw = match.group(0) if match else content
    data = json.loads(raw)

    category = str(data.get("category") or "").strip()
    features = [str(item).strip() for item in data.get("features") or [] if str(item).strip()]
    query = str(data.get("query") or " ".join([*features, category])).strip()
    colors = [str(item).strip() for item in data.get("colors") or [] if str(item).strip()]
    materials = [str(item).strip() for item in data.get("materials") or [] if str(item).strip()]
    brand_cues = [str(item).strip() for item in data.get("brand_cues") or [] if str(item).strip()]
    detected_objects = [str(item).strip() for item in data.get("detected_objects") or [] if str(item).strip()]
    return {
        "category": category,
        "features": features,
        "query": query,
        "colors": colors,
        "materials": materials,
        "shape": str(data.get("shape") or "").strip() or None,
        "style": str(data.get("style") or "").strip() or None,
        "brand_cues": brand_cues,
        "confidence": _optional_float(data.get("confidence")),
        "detected_objects": detected_objects,
    }


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
