# Backend Conventions

## FastAPI

- Create the app through `create_app()` in `app/main.py`.
- Register versioned route modules in `app/api/router.py`.
- Keep HTTP-specific concerns in `app/api/v1/`.
- Use dependency injection for services and database sessions.

## Services And Repositories

- Put business logic and orchestration in `app/services/`.
- Put persistence queries in `app/repositories/`.
- Do not put SQLAlchemy query logic directly in route handlers unless the endpoint is intentionally trivial.

## Schemas And Models

- Put Pydantic request and response contracts in `app/schemas/`.
- Put SQLAlchemy models in `app/models/`.
- Put database schema changes in Alembic revisions under `alembic/versions/`.
- Generate migrations from `app.core.database.Base.metadata` and review generated operations before committing.
- Keep API response shape changes covered by tests.

## Configuration

- Use `app/core/config.py` for environment-backed settings.
- Add new public environment variables to `.env.*.example` and `docs/reference/configuration.md`.

## Cross-Cutting Concerns

- Use `app.core.providers` for authentication, telemetry, logging, and error handling.
- Do not import logging, telemetry, auth session helpers, or exception handler implementations directly from feature modules.
- Run `python scripts/validate_providers.py` after changing provider-owned concerns.
