"""Compatibility wrappers for the logging provider."""

from app.core.providers import get_logging_provider


def configure_logging() -> None:
    get_logging_provider().configure()
