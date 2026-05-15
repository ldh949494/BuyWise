"""Logging access through the unified provider interface."""

import logging

from app.core.providers import get_logging_provider

def get_logger(name: str) -> logging.Logger:
    return get_logging_provider().get_logger(name)
