from types import SimpleNamespace

import pytest
from fastapi import FastAPI

from app.core import dependencies


@pytest.mark.anyio
async def test_lifespan_builds_dependency_cache_once_and_clears_it(monkeypatch) -> None:
    built = []
    cache = {"compare_service": object()}

    def fake_build_dependencies():
        built.append("called")
        return cache

    monkeypatch.setattr(dependencies, "build_app_dependencies", fake_build_dependencies)
    app = FastAPI()

    async with dependencies.lifespan(app):
        assert built == ["called"]
        assert app.state.buywise_dependencies is cache

    assert app.state.buywise_dependencies == {}


def test_get_cached_dependency_reuses_request_app_cache() -> None:
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace()))
    created = []

    def factory():
        instance = object()
        created.append(instance)
        return instance

    first = dependencies.get_cached_dependency(request, "service", factory)
    second = dependencies.get_cached_dependency(request, "service", factory)

    assert first is second
    assert created == [first]
