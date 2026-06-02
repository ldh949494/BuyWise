"""FastAPI dependency factories and application-scoped service objects."""

from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass, field, replace
from typing import Callable, TypeVar
from weakref import WeakKeyDictionary

from fastapi import Depends, FastAPI, Request
from sqlalchemy.orm import Session

from app.ai.llm_client import LLMClient
from app.ai.model_gateway import AIModelGateway
from app.ai.rag_pipeline import RAGPipeline
from app.core.config import Settings, settings
from app.core.database import SessionLocal, get_db
from app.services.chat_service import ChatService
from app.services.compare_service import CompareService
from app.services.admin_auth_service import AdminAuthService
from app.services.admin_ops_service import AdminOpsService
from app.services.product_service import ProductService
from app.services.rag_service import RagService
from app.services.rag_pipeline_factory import build_rag_pipeline
from app.services.readiness_service import ReadinessService
from app.services.speech_service import SpeechService
from app.services.upload_service import UploadService
from app.services.vision_service import VisionService
from app.vectorstore.chroma_client import ChromaProductStore
from app.vectorstore.retrieval_gateway import VectorRetrievalGateway


T = TypeVar("T")
_APP_CONTAINERS: WeakKeyDictionary[FastAPI, AppContainer] = WeakKeyDictionary()
_APP_CONTAINER_BUILDERS: WeakKeyDictionary[FastAPI, AppContainerBuilder] = WeakKeyDictionary()


@dataclass
class AppContainer:
    settings: Settings
    session_factory: Callable[[], Session]
    llm_client: AIModelGateway
    product_store: VectorRetrievalGateway
    rag_pipeline: RAGPipeline
    rag_service: RagService
    compare_service: CompareService
    chat_service: ChatService
    upload_service: UploadService
    speech_service: SpeechService
    vision_service: VisionService
    readiness_service: ReadinessService

    def close(self) -> None:
        close = getattr(self.product_store, "close", None)
        if callable(close):
            close()


@dataclass(frozen=True)
class AppContainerBuilder:
    settings: Settings = field(default_factory=lambda: settings)
    session_factory: Callable[[], Session] = SessionLocal
    llm_client: AIModelGateway | None = None
    product_store: VectorRetrievalGateway | None = None
    rag_pipeline: RAGPipeline | None = None
    rag_service: RagService | None = None
    compare_service: CompareService | None = None
    chat_service: ChatService | None = None
    upload_service: UploadService | None = None
    speech_service: SpeechService | None = None
    vision_service: VisionService | None = None
    readiness_service: ReadinessService | None = None

    def with_settings(self, app_settings: Settings) -> AppContainerBuilder:
        return replace(self, settings=app_settings)

    def with_session_factory(self, session_factory: Callable[[], Session]) -> AppContainerBuilder:
        return replace(self, session_factory=session_factory)

    def with_llm_client(self, llm_client: AIModelGateway) -> AppContainerBuilder:
        return replace(self, llm_client=llm_client)

    def with_product_store(self, product_store: VectorRetrievalGateway) -> AppContainerBuilder:
        return replace(self, product_store=product_store)

    def with_rag_pipeline(self, rag_pipeline: RAGPipeline) -> AppContainerBuilder:
        return replace(self, rag_pipeline=rag_pipeline)

    def with_rag_service(self, rag_service: RagService) -> AppContainerBuilder:
        return replace(self, rag_service=rag_service)

    def with_compare_service(self, compare_service: CompareService) -> AppContainerBuilder:
        return replace(self, compare_service=compare_service)

    def with_chat_service(self, chat_service: ChatService) -> AppContainerBuilder:
        return replace(self, chat_service=chat_service)

    def with_upload_service(self, upload_service: UploadService) -> AppContainerBuilder:
        return replace(self, upload_service=upload_service)

    def with_speech_service(self, speech_service: SpeechService) -> AppContainerBuilder:
        return replace(self, speech_service=speech_service)

    def with_vision_service(self, vision_service: VisionService) -> AppContainerBuilder:
        return replace(self, vision_service=vision_service)

    def with_readiness_service(self, readiness_service: ReadinessService) -> AppContainerBuilder:
        return replace(self, readiness_service=readiness_service)

    def build(self) -> AppContainer:
        product_store = self.product_store or ChromaProductStore()
        llm_client = self.llm_client or LLMClient()
        rag_pipeline = self.rag_pipeline or build_rag_pipeline(product_store=product_store)
        return AppContainer(
            settings=self.settings,
            session_factory=self.session_factory,
            llm_client=llm_client,
            product_store=product_store,
            rag_pipeline=rag_pipeline,
            rag_service=self.rag_service or RagService(product_store=product_store),
            compare_service=self.compare_service or CompareService(llm_client=llm_client),
            chat_service=self.chat_service or ChatService(rag_pipeline=rag_pipeline, llm_client=llm_client),
            upload_service=self.upload_service or UploadService(),
            speech_service=self.speech_service or SpeechService(),
            vision_service=self.vision_service or VisionService(),
            readiness_service=self.readiness_service
            or ReadinessService(
                app_settings=self.settings,
                session_factory=self.session_factory,
                product_store=product_store,
            ),
        )


def make_lifespan(container_builder: AppContainerBuilder | None = None):
    @asynccontextmanager
    async def app_lifespan(app: FastAPI):
        install_app_container(app, build_app_container(container_builder))
        try:
            yield
        finally:
            get_app_container_from_app(app).close()
            clear_app_container(app)

    return app_lifespan


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with make_lifespan()(app):
        yield


def build_app_container(container_builder: AppContainerBuilder | None = None) -> AppContainer:
    return (container_builder or AppContainerBuilder()).build()


def install_app_container(app: FastAPI, container: AppContainer) -> None:
    _APP_CONTAINERS[app] = container


def install_app_container_builder(app: FastAPI, container_builder: AppContainerBuilder | None) -> None:
    if container_builder is not None:
        _APP_CONTAINER_BUILDERS[app] = container_builder


def clear_app_container(app: FastAPI) -> None:
    _APP_CONTAINERS.pop(app, None)


def get_app_container(request: Request) -> AppContainer:
    return get_app_container_from_app(request.app)


def get_app_container_from_app(app: FastAPI) -> AppContainer:
    container = _APP_CONTAINERS.get(app)
    if container is None:
        container = build_app_container(_APP_CONTAINER_BUILDERS.get(app))
        install_app_container(app, container)
    return container


def get_container_attr(request: Request, getter: Callable[[AppContainer], T]) -> T:
    return getter(get_app_container(request))


def get_llm_client(request: Request) -> AIModelGateway:
    return get_container_attr(request, lambda container: container.llm_client)


def get_product_store(request: Request) -> VectorRetrievalGateway:
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


def get_upload_service(request: Request) -> UploadService:
    return get_container_attr(request, lambda container: container.upload_service)


def get_vision_service(request: Request) -> VisionService:
    return get_container_attr(request, lambda container: container.vision_service)


def get_speech_service(request: Request) -> SpeechService:
    return get_container_attr(request, lambda container: container.speech_service)


def get_readiness_service(request: Request) -> ReadinessService:
    return get_container_attr(request, lambda container: container.readiness_service)


def get_admin_ops_service(
    request: Request,
    db: Session = Depends(get_db),
) -> AdminOpsService:
    container = get_app_container(request)
    return AdminOpsService(
        db,
        readiness_service=container.readiness_service,
        product_store=container.product_store,
    )
