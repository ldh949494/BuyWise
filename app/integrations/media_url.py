"""Helpers for resolving uploaded media URLs for external providers."""

from __future__ import annotations

from urllib.parse import urljoin, urlparse

from app.core.config import settings
from app.core.providers import AppError


def resolve_public_media_url(url: str, *, field_name: str) -> str:
    """Return an absolute media URL suitable for external AI/vendor APIs."""

    if _is_absolute_http_url(url):
        return url

    if not url.startswith("/"):
        raise AppError(
            f"{field_name} must be an absolute http(s) URL or an uploaded media path.",
            status_code=400,
            code="invalid_media_url",
            extra={"field": field_name},
        )

    base_url = settings.upload_public_base_url.strip()
    if not base_url:
        raise AppError(
            f"{field_name} is relative, but UPLOAD_PUBLIC_BASE_URL is not configured.",
            status_code=400,
            code="media_url_not_public",
            extra={"field": field_name},
        )

    return urljoin(base_url.rstrip("/") + "/", url.lstrip("/"))


def _is_absolute_http_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
