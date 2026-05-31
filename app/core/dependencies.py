"""FastAPI dependency factories and application-scoped service objects."""

from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Callable, TypeVar

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
from app.services.rag_pipeline_factory import build_rag_pipeline
from app.services.speech_service import SpeechService
from app.services.upload_service import UploadService
from app.services.vision_service import VisionService
from app.vectorstore.chroma_client import ChromaProductStore


STATE_KEY = "buywise_dependencies"
T = TypeVar("T")


@dataclass
class AppContainer:
    llm_client: LLMClient
    product_store: ChromaProductStore
    rag_pipeline: RAGPipeline
    rag_service: RagService
    compare_service: CompareService
    chat_service: ChatService
    speech_service: SpeechService
    vision_service: VisionService

    def close(self) -> None:
        close = getattr(self.product_store, "close", None)
        if callable(close):
            close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.buywise_dependencies = build_app_container()
    try:
        yield
    finally:
        get_app_container_from_app(app).close()
        app.state.buywise_dependencies = None


def build_app_container() -> AppContainer:
    product_store = ChromaProductStore()
    llm_client = LLMClient()
    rag_pipeline = build_rag_pipeline(product_store=product_store)
    return AppContainer(
        llm_client=llm_client,
        product_store=product_store,
        rag_pipeline=rag_pipeline,
        rag_service=RagService(product_store=product_store),
        compare_service=CompareService(llm_client=llm_client),
        chat_service=ChatService(rag_pipeline=rag_pipeline, llm_client=llm_client),
        speech_service=SpeechService(),
        vision_service=VisionService(),
    )


def get_app_container(request: Request) -> AppContainer:
    return get_app_container_from_app(request.app)


def get_app_container_from_app(app: FastAPI) -> AppContainer:
    container = getattr(app.state, STATE_KEY, None)
    if container is None:
        container = build_app_container()
        app.state.buywise_dependencies = container
    return container


def get_container_attr(request: Request, getter: Callable[[AppContainer], T]) -> T:
    return getter(get_app_container(request))


def get_llm_client(request: Request) -> LLMClient:
    return get_container_attr(request, lambda container: container.llm_client)


def get_product_store(request: Request) -> ChromaProductStore:
    return get_container_attr(request, lambda container: container.product_store)


def get_rag_pipeline(request: Request) -> RAGPipeline:
    return get_container_attr(request, lambda container: container.rag_pipeline)


def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(db)


def get_admin_auth_service(db: Session = Depends(get_db)) -> AdminAuthService:
    return AdminAuthService(db)


def get_compare_service(request: Request) -> CompareService:
    return get_container_attr(request, lambda container: container.compare_service)


def get_chat_service(request: Request) -> ChatService:
    return get_container_attr(request, lambda container: container.chat_service)


def get_rag_service(request: Request) -> RagService:
    return get_container_attr(request, lambda container: container.rag_service)


def get_upload_service() -> UploadService:
    return UploadService()


def get_vision_service(request: Request) -> VisionService:
    return get_container_attr(request, lambda container: container.vision_service)


def get_speech_service(request: Request) -> SpeechService:
    return get_container_attr(request, lambda container: container.speech_service)
