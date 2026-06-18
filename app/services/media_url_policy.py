"""Media URL safety policy for AI inputs."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse

from app.core.config import settings
from app.core.providers import AppError


class MediaUrlPolicy:
    def validate(self, url: str | None) -> None:
        if not url or not settings.ai_media_url_allowlist_enabled:
            return
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise self._blocked()
        if self._is_private_host(parsed.hostname):
            raise self._blocked()
        if not self._is_allowed_host(parsed.hostname):
            raise self._blocked()

    def _is_allowed_host(self, host: str) -> bool:
        allowed_hosts = set(settings.media_allowed_hosts)
        upload_host = urlparse(settings.upload_public_base_url).hostname
        if upload_host:
            allowed_hosts.add(upload_host)
        if settings.cos_bucket and settings.cos_region:
            allowed_hosts.add(f"{settings.cos_bucket}.cos.{settings.cos_region}.myqcloud.com")
        return host in allowed_hosts

    def _is_private_host(self, host: str) -> bool:
        if host in {"localhost"} or host.endswith(".localhost"):
            return True
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            return False
        return ip.is_private or ip.is_loopback or ip.is_link_local

    def _blocked(self) -> AppError:
        return AppError("Media URL is not allowed.", status_code=400, code="media_url_not_allowed")
