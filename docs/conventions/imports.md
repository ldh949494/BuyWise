# Import Boundaries

Layered imports keep implementation choices from leaking across the codebase.

## Backend Rules

- API modules call services and use schemas/core dependencies.
- Services orchestrate repositories, integrations, AI, vector stores, schemas, and utilities.
- Repositories use models and core database helpers.
- Models do not import API, service, or repository modules.
- Schemas may import shared schemas, but not services, repositories, models, or API modules.

## Fix Pattern

When a lint error says a layer imports a forbidden layer, move that dependency behind the nearest allowed owner. For example, if an API route imports a repository, create or extend a service method and inject that service into the route.
