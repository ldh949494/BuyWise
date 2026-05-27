"""Print a non-sensitive runtime configuration summary."""

from __future__ import annotations

import json

from app.core.config import settings


def runtime_config_summary() -> dict[str, object]:
    return {
        "app_env": settings.app_env,
        "app_debug": settings.app_debug,
        "allow_mock_providers_in_prod": settings.allow_mock_providers_in_prod,
        "llm_provider": settings.llm_provider,
        "embedding_provider": settings.embedding_provider,
        "vision_provider": settings.vision_provider,
        "speech_provider": settings.speech_provider,
        "upload_provider": settings.upload_provider,
        "mysql_host": settings.mysql_host,
        "mysql_database": settings.mysql_database,
        "chroma_persist_dir": settings.chroma_persist_dir,
        "chroma_product_collection": settings.chroma_product_collection,
    }


def main() -> None:
    print(json.dumps(runtime_config_summary(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
