"""Image download helpers for maintenance scripts."""

from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.request import Request, urlopen

SUPPORTED_IMAGE_TYPES = {"image/gif", "image/jpeg", "image/png", "image/webp"}
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_MAX_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True)
class DownloadedImage:
    content: bytes
    content_type: str
    suffix: str


def download_image(
    url: str,
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> DownloadedImage:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http(s) image URLs can be migrated.")

    request = Request(url, headers={"User-Agent": "BuyWiseImageMigrator/1.0"})
    with urlopen(request, timeout=timeout_seconds) as response:
        content_type = response.headers.get_content_type().lower()
        if content_type not in SUPPORTED_IMAGE_TYPES:
            raise ValueError(f"Unsupported image content type: {content_type}")
        content = response.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise ValueError(f"Image exceeds max size of {max_bytes} bytes.")
    return DownloadedImage(
        content=content,
        content_type=content_type,
        suffix=_suffix_for_url(url, content_type),
    )


def _suffix_for_url(url: str, content_type: str) -> str:
    if content_type == "image/jpeg":
        return ".jpg"
    if content_type == "image/png":
        return ".png"
    if content_type == "image/webp":
        return ".webp"
    if content_type == "image/gif":
        return ".gif"
    parsed_path = urlparse(url).path
    path_suffix = "." + parsed_path.rsplit(".", 1)[-1].lower() if "." in parsed_path else ""
    if path_suffix in {".gif", ".jpeg", ".jpg", ".png", ".webp"}:
        return ".jpg" if path_suffix == ".jpeg" else path_suffix
    guessed = mimetypes.guess_extension(content_type) or ".jpg"
    return ".jpg" if guessed == ".jpe" else guessed
