# Logging

Runtime code must use structured logging through the Provider entrypoint.

## Python

```python
from app.core.providers import get_provider

logger = get_provider("logging").get_logger(__name__)
logger.info("Product search completed", extra={"category": category})
```

Backend JSON logs include the active request ID when a request is in progress. Use the `X-Request-ID` response header to correlate client-visible errors with logs.

Do not log full request bodies, AI prompts, uploaded file contents, credentials, or user private text. Common sensitive fields such as passwords, tokens, secrets, API keys, and authorization headers are redacted by the backend formatter.

Avoid Python `LogRecord` reserved names in `extra`; use domain-specific names such as `stored_filename` instead of `filename`.

`print()` is allowed in command-line scripts, tests, and app scripts, but not in runtime application modules.

## Kotlin

Do not add `console.log`, `System.out.println`, or direct `Log.d` style calls. Route logging through the app logging provider when a Kotlin provider is introduced.
