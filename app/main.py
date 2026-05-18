from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.core.providers import (
    get_error_provider,
    get_logging_provider,
    get_middleware_provider,
    get_telemetry_provider,
)


def create_app() -> FastAPI:
    get_logging_provider().configure()
    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    get_middleware_provider().register_middleware(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    get_error_provider().register_exception_handlers(app)
    get_telemetry_provider().instrument(app)
    return app


app = create_app()
