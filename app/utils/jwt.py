"""Minimal HS256 JWT helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Any, Callable


def build_hs256_jwt(payload: dict[str, Any], secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    segments = [_json_b64(header), _json_b64(payload)]
    signing_input = ".".join(segments).encode("ascii")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    segments.append(encode_base64_url(signature))
    return ".".join(segments)


def decode_hs256_jwt(token: str, secret: str, invalid_error: Callable[[], Exception]) -> dict[str, Any]:
    try:
        header_raw, payload_raw, signature_raw = token.split(".", 2)
    except ValueError as exc:
        raise invalid_error() from exc
    signing_input = f"{header_raw}.{payload_raw}".encode("ascii")
    expected = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    try:
        supplied = decode_base64_url(signature_raw)
    except ValueError as exc:
        raise invalid_error() from exc
    if not hmac.compare_digest(expected, supplied):
        raise invalid_error()
    return decode_json_segment(payload_raw, invalid_error)


def encode_base64_url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def decode_base64_url(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def decode_json_segment(segment: str, invalid_error: Callable[[], Exception]) -> dict[str, Any]:
    try:
        decoded = json.loads(decode_base64_url(segment))
    except (ValueError, json.JSONDecodeError) as exc:
        raise invalid_error() from exc
    if not isinstance(decoded, dict):
        raise invalid_error()
    return decoded


def _json_b64(value: dict[str, Any]) -> str:
    return encode_base64_url(json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8"))
