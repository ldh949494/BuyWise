from types import SimpleNamespace
from io import BytesIO

import pytest

from app.core.providers import AppError
from app.integrations.cos_storage_client import TencentCosStorageClient
from app.scripts import real_dependency_smoke


def test_mysql_smoke_requires_mysql_dialect(monkeypatch) -> None:
    class FakeEngine:
        dialect = SimpleNamespace(name="sqlite")

        def dispose(self) -> None:
            pass

    monkeypatch.setattr(real_dependency_smoke, "create_engine", lambda *args, **kwargs: FakeEngine())

    assert real_dependency_smoke.check_mysql_connection() == {
        "status": "failed",
        "reason": "Expected mysql dialect, got sqlite.",
    }


def test_mysql_smoke_runs_select_one_on_mysql(monkeypatch) -> None:
    class FakeResult:
        def scalar_one(self) -> int:
            return 1

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def execute(self, statement):
            return FakeResult()

    class FakeEngine:
        dialect = SimpleNamespace(name="mysql")

        def connect(self):
            return FakeConnection()

        def dispose(self) -> None:
            pass

    monkeypatch.setattr(real_dependency_smoke, "create_engine", lambda *args, **kwargs: FakeEngine())

    assert real_dependency_smoke.check_mysql_connection() == {
        "status": "ok",
        "dialect": "mysql",
        "select_one": 1,
    }


def test_cos_smoke_uses_read_only_bucket_probe(monkeypatch) -> None:
    previous_bucket = real_dependency_smoke.settings.cos_bucket
    previous_region = real_dependency_smoke.settings.cos_region
    previous_secret_id = real_dependency_smoke.settings.tencent_secret_id
    previous_secret_key = real_dependency_smoke.settings.tencent_secret_key

    class FakeCosClient:
        def __init__(self) -> None:
            self.calls = []

        def head_bucket(self, **kwargs):
            self.calls.append(("head_bucket", kwargs["Bucket"]))

    fake_client = FakeCosClient()
    real_dependency_smoke.settings.cos_bucket = "bucket"
    real_dependency_smoke.settings.cos_region = "ap-shanghai"
    real_dependency_smoke.settings.tencent_secret_id = "sid"
    real_dependency_smoke.settings.tencent_secret_key = "skey"
    try:
        client = TencentCosStorageClient(client=fake_client)
        assert real_dependency_smoke.check_cos_read_access(client) == {
            "status": "ok",
            "bucket": "bucket",
            "operation": "head_bucket",
        }
        assert fake_client.calls == [("head_bucket", "bucket")]
    finally:
        real_dependency_smoke.settings.cos_bucket = previous_bucket
        real_dependency_smoke.settings.cos_region = previous_region
        real_dependency_smoke.settings.tencent_secret_id = previous_secret_id
        real_dependency_smoke.settings.tencent_secret_key = previous_secret_key


def test_cos_upload_sets_public_read_acl(monkeypatch) -> None:
    previous_bucket = real_dependency_smoke.settings.cos_bucket
    previous_region = real_dependency_smoke.settings.cos_region
    previous_secret_id = real_dependency_smoke.settings.tencent_secret_id
    previous_secret_key = real_dependency_smoke.settings.tencent_secret_key
    previous_public_base = real_dependency_smoke.settings.upload_public_base_url

    class FakeCosClient:
        def __init__(self) -> None:
            self.put_object_kwargs = None

        def put_object(self, **kwargs):
            self.put_object_kwargs = kwargs

    fake_client = FakeCosClient()
    real_dependency_smoke.settings.cos_bucket = "bucket"
    real_dependency_smoke.settings.cos_region = "ap-shanghai"
    real_dependency_smoke.settings.tencent_secret_id = "sid"
    real_dependency_smoke.settings.tencent_secret_key = "skey"
    real_dependency_smoke.settings.upload_public_base_url = ""
    try:
        client = TencentCosStorageClient(client=fake_client)
        url = client.upload_fileobj(
            key="product-images/demo/main.jpg",
            fileobj=BytesIO(b"image"),
            content_type="image/jpeg",
        )

        assert url == "https://bucket.cos.ap-shanghai.myqcloud.com/product-images/demo/main.jpg"
        assert fake_client.put_object_kwargs["ACL"] == "public-read"
        assert fake_client.put_object_kwargs["Bucket"] == "bucket"
        assert fake_client.put_object_kwargs["ContentType"] == "image/jpeg"
    finally:
        real_dependency_smoke.settings.cos_bucket = previous_bucket
        real_dependency_smoke.settings.cos_region = previous_region
        real_dependency_smoke.settings.tencent_secret_id = previous_secret_id
        real_dependency_smoke.settings.tencent_secret_key = previous_secret_key
        real_dependency_smoke.settings.upload_public_base_url = previous_public_base


def test_cos_upload_wraps_provider_failure() -> None:
    previous_bucket = real_dependency_smoke.settings.cos_bucket
    previous_region = real_dependency_smoke.settings.cos_region
    previous_secret_id = real_dependency_smoke.settings.tencent_secret_id
    previous_secret_key = real_dependency_smoke.settings.tencent_secret_key

    class FailingCosClient:
        def put_object(self, **kwargs):
            raise RuntimeError("remote cos failed")

    real_dependency_smoke.settings.cos_bucket = "bucket"
    real_dependency_smoke.settings.cos_region = "ap-shanghai"
    real_dependency_smoke.settings.tencent_secret_id = "sid"
    real_dependency_smoke.settings.tencent_secret_key = "skey"
    try:
        client = TencentCosStorageClient(client=FailingCosClient())

        with pytest.raises(AppError) as exc_info:
            client.upload_fileobj(
                key="voice.wav",
                fileobj=BytesIO(b"audio"),
                content_type="audio/wav",
            )
    finally:
        real_dependency_smoke.settings.cos_bucket = previous_bucket
        real_dependency_smoke.settings.cos_region = previous_region
        real_dependency_smoke.settings.tencent_secret_id = previous_secret_id
        real_dependency_smoke.settings.tencent_secret_key = previous_secret_key

    assert exc_info.value.status_code == 503
    assert exc_info.value.code == "provider_error"
    assert exc_info.value.extra == {"provider": "tencent_cos"}


def test_real_dependency_smoke_aggregates_selected_checks(monkeypatch) -> None:
    monkeypatch.setattr(real_dependency_smoke, "check_mysql_connection", lambda: {"status": "ok"})
    monkeypatch.setattr(real_dependency_smoke, "check_cos_read_access", lambda: {"status": "ok"})

    assert real_dependency_smoke.run_real_dependency_smoke(["mysql", "cos"]) == {
        "status": "ok",
        "checks": {"mysql": {"status": "ok"}, "cos": {"status": "ok"}},
    }
