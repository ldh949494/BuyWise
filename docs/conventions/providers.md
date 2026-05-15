# Provider Pattern

Cross-cutting concerns must have a single entrypoint. Do not introduce direct imports for authentication, telemetry, logging, or error handling from feature modules.

## Backend Provider Entrypoint

Use `app.core.providers`:

```python
from app.core.providers import get_provider

auth = get_provider("auth")
logger = get_provider("logging").get_logger(__name__)
telemetry = get_provider("telemetry")
errors = get_provider("errors")
```

Typed helpers are also available:

```python
from app.core.providers import get_logging_provider

logger = get_logging_provider().get_logger(__name__)
```

## Forbidden Pattern

Feature modules must not directly import cross-cutting implementations:

```python
import logging
from prometheus_fastapi_instrumentator import Instrumentator
from app.core.logging import configure_logging
```

## Ownership

- `auth`: authentication and current principal access.
- `telemetry`: metrics, tracing, and instrumentation.
- `logging`: logger creation and logging configuration.
- `errors`: global exception handler registration and error mapping.

## Validation

`scripts/validate_providers.py` scans backend imports and fails when app modules bypass `app.core.providers`. Compatibility wrappers may exist only in approved core utility files.
