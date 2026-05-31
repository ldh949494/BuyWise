from types import SimpleNamespace

import pytest
from fastapi import FastAPI

from app.core import dependencies


@pytest.mark.anyio
async def test_lifespan_builds_app_container_once_and_closes_it(monkeypatch) -> None:
    built = []
    closed = []
    container = SimpleNamespace(close=lambda: closed.append("called"))

    def fake_build_app_container(container_builder=None):
        assert container_builder is None
        built.append("called")
        return container

    monkeypatch.setattr(dependencies, "build_app_container", fake_build_app_container)
    app = FastAPI()

    async with dependencies.lifespan(app):
        assert built == ["called"]
        assert dependencies.get_app_container_from_app(app) is container

    assert closed == ["called"]
    assert app not in dependencies._APP_CONTAINERS


def test_get_app_container_reuses_request_app_container(monkeypatch) -> None:
    request = SimpleNamespace(app=FastAPI())
    created = []

    def fake_build_app_container(container_builder=None):
        assert container_builder is None
        instance = SimpleNamespace(llm_client=object())
        created.append(instance)
        return instance

    monkeypatch.setattr(dependencies, "build_app_container", fake_build_app_container)

    first = dependencies.get_app_container(request)
    second = dependencies.get_app_container(request)

    assert first is second
    assert created == [first]


def test_container_builder_replaces_single_dependency() -> None:
    product_store = SimpleNamespace(indexed_product_ids=lambda: [1, 2], count=lambda: 2)
    builder = dependencies.AppContainerBuilder().with_product_store(product_store)

    container = dependencies.build_app_container(builder)

    assert container.product_store is product_store
    assert container.readiness_service.product_store is product_store
