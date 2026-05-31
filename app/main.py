from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.dependencies import AppContainerBuilder, install_app_container_builder, make_lifespan
from app.core.providers import (
    get_error_provider,
    get_logging_provider,
    get_middleware_provider,
    get_telemetry_provider,
)


def create_app(container_builder: AppContainerBuilder | None = None) -> FastAPI:
    settings.validate_production()
    get_logging_provider().configure()
    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=make_lifespan(container_builder),
    )
    install_app_container_builder(app, container_builder)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )
    get_middleware_provider().register_middleware(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    mount_admin_web(app)
    get_error_provider().register_exception_handlers(app)
    get_telemetry_provider().instrument(app)
    return app


def mount_admin_web(app: FastAPI) -> None:
    admin_dist = Path("admin-web/dist")
    index_file = admin_dist / "index.html"
    if not index_file.exists():
        return

    @app.get("/admin", include_in_schema=False)
    @app.get("/admin/{asset_path:path}", include_in_schema=False)
    def serve_admin(asset_path: str = ""):
        target = (admin_dist / asset_path).resolve()
        root = admin_dist.resolve()
        if target.is_file() and target.is_relative_to(root):
            return FileResponse(target)
        return FileResponse(index_file)


app = create_app()
