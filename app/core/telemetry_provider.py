"""Telemetry provider implementation."""

from __future__ import annotations

from typing import Literal

from fastapi import FastAPI

try:
    from prometheus_fastapi_instrumentator import Instrumentator
except ImportError:  # pragma: no cover - dependency is installed in normal runtime.
    Instrumentator = None

ProviderName = Literal["auth", "telemetry", "logging", "errors", "middleware"]


class TelemetryProvider:
    name: ProviderName = "telemetry"

    def instrument(self, app: FastAPI) -> None:
        if Instrumentator is not None:
            _patch_instrumentator_included_router_support()
            Instrumentator().instrument(app).expose(app)


def _effective_candidates(route) -> list:
    candidates = getattr(route, "effective_candidates", None)
    if not callable(candidates):
        return []
    return list(candidates())


def _patch_instrumentator_included_router_support() -> None:
    from prometheus_fastapi_instrumentator import routing
    from starlette.routing import Match, Mount

    if getattr(routing, "_buywise_included_router_patch", False):
        return

    def _get_route_name(scope, routes, route_name=None):
        for route in routes:
            match, child_scope = route.matches(scope)
            if match == Match.FULL:
                route_path = getattr(route, "path", None)
                if route_path is None:
                    return _get_route_name(scope, _effective_candidates(route), route_name)
                child_scope = {**scope, **child_scope}
                if isinstance(route, Mount) and route.routes:
                    child_route_name = _get_route_name(child_scope, route.routes, route_path)
                    return None if child_route_name is None else route_path + child_route_name
                return route_path
            if match == Match.PARTIAL and route_name is None:
                route_name = getattr(route, "path", None)
        return route_name

    routing._get_route_name = _get_route_name
    routing._buywise_included_router_patch = True
