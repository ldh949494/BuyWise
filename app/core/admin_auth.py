"""Admin authentication dependencies."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request

from app.core.providers import AppError
from app.services.admin_auth_service import get_admin_token_payload


@dataclass(frozen=True)
class AdminPrincipal:
    user_id: int
    username: str
    role: str


def require_admin(request: Request) -> AdminPrincipal:
    token = _bearer_token(request.headers.get("authorization"))
    if token is None:
        raise AppError("Missing admin token.", status_code=401, code="unauthorized", headers={"WWW-Authenticate": "Bearer"})
    payload = get_admin_token_payload(token)
    role = str(payload.get("role") or "")
    if role != "admin":
        raise AppError("Admin privileges are required.", status_code=403, code="forbidden")
    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise AppError("Invalid admin token.", status_code=401, code="unauthorized") from exc
    return AdminPrincipal(
        user_id=user_id,
        username=str(payload.get("username") or ""),
        role=role,
    )


def _bearer_token(authorization: str | None) -> str | None:
    if authorization is None:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()
