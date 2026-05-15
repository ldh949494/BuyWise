# Logging

Runtime code must use structured logging through the Provider entrypoint.

## Python

```python
from app.core.providers import get_provider

logger = get_provider("logging").get_logger(__name__)
logger.info("Product search completed", extra={"category": category})
```

`print()` is allowed in command-line scripts, tests, and app scripts, but not in runtime application modules.

## Kotlin

Do not add `console.log`, `System.out.println`, or direct `Log.d` style calls. Route logging through the app logging provider when a Kotlin provider is introduced.
