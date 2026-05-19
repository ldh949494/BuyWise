"""Authentication provider implementation."""

from __future__ import annotations

import hmac
from typing import Callable

from fastapi import Request, status
from starlette.exceptions import HTTPException

from app.core.config import settings


class Principal:
    def __init__(self, subject: str, scopes: tuple[str, ...] = ()) -> None:
        self.subject = subject
        self.scopes = scopes


class AuthProvider:
    name = "auth"

    def get_current_principal(self, request: Request | None = None) -> Principal | None:
        if request is None:
            return None
        token = self._bearer_token(request.headers.get("authorization"))
        if token is None:
            return None
        for configured_token, data in settings.configured_auth_api_keys.items():
            if hmac.compare_digest(token, configured_token):
                return Principal(
                    subject=str(data["subject"]),
                    scopes=tuple(str(scope) for scope in data["scopes"]),
                )
        return None

    def require_principal(self, request: Request, required_scopes: tuple[str, ...] = ()) -> Principal:
        principal = self.get_current_principal(request)
        if principal is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        missing_scopes = [scope for scope in required_scopes if scope not in principal.scopes]
        if missing_scopes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return principal

    def _bearer_token(self, authorization: str | None) -> str | None:
        if not authorization:
            return None
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            return None
        return token.strip()


def require_principal_dependency(
    auth_provider: AuthProvider,
    required_scopes: tuple[str, ...],
) -> Callable[[Request], Principal]:
    def dependency(request: Request) -> Principal:
        return auth_provider.require_principal(request, required_scopes)

    return dependency
