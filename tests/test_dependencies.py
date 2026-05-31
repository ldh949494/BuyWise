from types import SimpleNamespace

import pytest
from fastapi import FastAPI

from app.core import dependencies


@pytest.mark.anyio
async def test_lifespan_builds_app_container_once_and_closes_it(monkeypatch) -> None:
    built = []
    closed = []
    container = SimpleNamespace(close=lambda: closed.append("called"))

    def fake_build_app_container():
        built.append("called")
        return container

    monkeypatch.setattr(dependencies, "build_app_container", fake_build_app_container)
    app = FastAPI()

    async with dependencies.lifespan(app):
        assert built == ["called"]
        assert app.state.buywise_dependencies is container

    assert closed == ["called"]
    assert app.state.buywise_dependencies is None


def test_get_app_container_reuses_request_app_container(monkeypatch) -> None:
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace()))
    created = []

    def fake_build_app_container():
        instance = SimpleNamespace(llm_client=object())
        created.append(instance)
        return instance

    monkeypatch.setattr(dependencies, "build_app_container", fake_build_app_container)

    first = dependencies.get_app_container(request)
    second = dependencies.get_app_container(request)

    assert first is second
    assert created == [first]
