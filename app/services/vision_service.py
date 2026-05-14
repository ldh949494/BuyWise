"""Vision service."""


class VisionService:
    """Mock vision service, replaceable with multimodal model calls later."""

    async def recognize(self, image_url: str) -> dict:
        _ = image_url
        category = "\u673a\u68b0\u952e\u76d8"
        features = ["\u767d\u8272", "\u65e0\u7ebf", "\u7d27\u51d1\u5e03\u5c40"]
        return {
            "category": category,
            "features": features,
            "query": " ".join([*features, category]),
        }
