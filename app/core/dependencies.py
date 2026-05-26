"""FastAPI dependency factories and application-scoped service objects."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Request
from sqlalchemy.orm import Session

from app.ai.llm_client import LLMClient
from app.ai.rag_pipeline import RAGPipeline
from app.core.database import get_db
from app.services.chat_service import ChatService
from app.services.compare_service import CompareService
from app.services.admin_auth_service import AdminAuthService
from app.services.product_service import ProductService
from app.services.rag_service import RagService
from app.services.speech_service import SpeechService
from app.services.upload_service import UploadService
from app.services.vision_service import VisionService
from app.vectorstore.chroma_client import ChromaProductStore


STATE_KEY = "buywise_dependencies"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.buywise_dependencies = build_app_dependencies()
    try:
        yield
    finally:
        app.state.buywise_dependencies = {}


def build_app_dependencies() -> dict[str, Any]:
    product_store = ChromaProductStore()
    llm_client = LLMClient()
    rag_pipeline = RAGPipeline(product_store=product_store)
    return {
        "llm_client": llm_client,
        "product_store": product_store,
        "rag_pipeline": rag_pipeline,
        "rag_service": RagService(product_store=product_store),
        "compare_service": CompareService(llm_client=llm_client),
        "chat_service": ChatService(rag_pipeline=rag_pipeline, llm_client=llm_client),
        "speech_service": SpeechService(),
        "vision_service": VisionService(),
    }


def get_dependency_cache(request: Request) -> dict[str, Any]:
    cache = getattr(request.app.state, STATE_KEY, None)
    if cache is None:
        cache = {}
        request.app.state.buywise_dependencies = cache
    return cache


def get_cached_dependency(request: Request, key: str, factory):
    cache = get_dependency_cache(request)
    if key not in cache:
        cache[key] = factory()
    return cache[key]


def get_llm_client(request: Request) -> LLMClient:
    return get_cached_dependency(request, "llm_client", LLMClient)


def get_product_store(request: Request) -> ChromaProductStore:
    return get_cached_dependency(request, "product_store", ChromaProductStore)


def get_rag_pipeline(request: Request) -> RAGPipeline:
    return get_cached_dependency(
        request,
        "rag_pipeline",
        lambda: RAGPipeline(product_store=get_product_store(request)),
    )


def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(db)


def get_admin_auth_service(db: Session = Depends(get_db)) -> AdminAuthService:
    return AdminAuthService(db)


def get_compare_service(request: Request) -> CompareService:
    return get_cached_dependency(
        request,
        "compare_service",
        lambda: CompareService(llm_client=get_llm_client(request)),
    )


def get_chat_service(request: Request) -> ChatService:
    return get_cached_dependency(
        request,
        "chat_service",
        lambda: ChatService(
            rag_pipeline=get_rag_pipeline(request),
            llm_client=get_llm_client(request),
        ),
    )


def get_rag_service(request: Request) -> RagService:
    return get_cached_dependency(
        request,
        "rag_service",
        lambda: RagService(product_store=get_product_store(request)),
    )


def get_upload_service() -> UploadService:
    return UploadService()


def get_vision_service(request: Request) -> VisionService:
    return get_cached_dependency(request, "vision_service", VisionService)


def get_speech_service(request: Request) -> SpeechService:
    return get_cached_dependency(request, "speech_service", SpeechService)
