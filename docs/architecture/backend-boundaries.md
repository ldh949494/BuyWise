# Backend Boundaries

The backend is a FastAPI application organized by boundary rather than by endpoint file alone.

## Entry Points

- App factory: `app/main.py`
- Router registry: `app/api/router.py`
- Runtime configuration: `app/core/config.py`
- Database session setup: `app/core/database.py`

## Layer Responsibilities

- `app/api/v1/`: HTTP concerns, dependency wiring, request validation, response model selection.
- `app/services/`: use-case logic, orchestration, fallback behavior, AI/retrieval composition.
- `app/repositories/`: persistence access and query behavior.
- `app/models/`: SQLAlchemy persistence models.
- `app/schemas/`: Pydantic API contracts and service DTOs.
- `app/integrations/`: external vendor clients such as multimodal, object storage, and ASR integrations.

## API Versioning

All public HTTP routes should be registered below `settings.api_v1_prefix`, which defaults to `/api/v1`.

## Metrics And Logs

The app exposes Prometheus metrics at `/metrics` when `prometheus-fastapi-instrumentator` is installed. Application logs are JSON formatted through `app/core/logging.py`.
