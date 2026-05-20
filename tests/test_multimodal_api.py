from pathlib import Path
from shutil import rmtree

from fastapi.testclient import TestClient

from app.api.v1.upload import get_upload_service
from app.core.config import settings
from app.main import create_app
from app.services.upload_service import UploadService

AUTH_HEADER = {"Authorization": "Bearer upload-token"}


def configure_upload_auth() -> None:
    settings.auth_api_keys = "uploader:upload-token:upload:write"
    settings.upload_provider = "local"
    settings.upload_public_base_url = ""


def configure_mock_multimodal() -> None:
    settings.vision_provider = "mock"
    settings.speech_provider = "mock"


class UnsafeUploadService(UploadService):
    def _build_storage_name(self, suffix: str) -> str:
        return f"../unsafe{suffix}"


def test_upload_endpoint_saves_file_to_local_directory() -> None:
    configure_upload_auth()
    upload_dir = Path(".test_uploads")
    if upload_dir.exists():
        rmtree(upload_dir)

    app = create_app()
    app.dependency_overrides[get_upload_service] = lambda: UploadService(upload_dir=upload_dir)
    client = TestClient(app)

    try:
        response = client.post(
            "/api/v1/upload",
            files={"file": ("demo.png", b"fake image bytes", "image/png")},
            headers=AUTH_HEADER,
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["filename"].endswith(".png")
        assert payload["url"] == f"/uploads/{payload['filename']}"
        assert (upload_dir / payload["filename"]).read_bytes() == b"fake image bytes"
    finally:
        if upload_dir.exists():
            rmtree(upload_dir)


def test_upload_endpoint_accepts_audio_file() -> None:
    configure_upload_auth()
    upload_dir = Path(".test_uploads")
    if upload_dir.exists():
        rmtree(upload_dir)

    app = create_app()
    app.dependency_overrides[get_upload_service] = lambda: UploadService(upload_dir=upload_dir)
    client = TestClient(app)

    try:
        response = client.post(
            "/api/v1/upload",
            files={"file": ("voice.mp3", b"fake audio bytes", "audio/mpeg")},
            headers=AUTH_HEADER,
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["filename"].endswith(".mp3")
        assert (upload_dir / payload["filename"]).read_bytes() == b"fake audio bytes"
    finally:
        if upload_dir.exists():
            rmtree(upload_dir)


def test_upload_endpoint_can_return_public_local_url() -> None:
    configure_upload_auth()
    settings.upload_public_base_url = "https://api.example.com"
    upload_dir = Path(".test_uploads")
    if upload_dir.exists():
        rmtree(upload_dir)

    app = create_app()
    app.dependency_overrides[get_upload_service] = lambda: UploadService(upload_dir=upload_dir)
    client = TestClient(app)

    try:
        response = client.post(
            "/api/v1/upload",
            files={"file": ("demo.png", b"fake image bytes", "image/png")},
            headers=AUTH_HEADER,
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["url"] == f"https://api.example.com/uploads/{payload['filename']}"
    finally:
        settings.upload_public_base_url = ""
        if upload_dir.exists():
            rmtree(upload_dir)


def test_upload_endpoint_can_store_with_cos_client() -> None:
    class FakeStorageClient:
        def __init__(self) -> None:
            self.calls = []

        def upload_fileobj(self, *, key, fileobj, content_type):
            self.calls.append((key, fileobj.read(), content_type))
            return f"https://cos.example.com/{key}"

    configure_upload_auth()
    settings.upload_provider = "cos"
    storage_client = FakeStorageClient()
    app = create_app()
    app.dependency_overrides[get_upload_service] = lambda: UploadService(storage_client=storage_client)
    client = TestClient(app)

    try:
        response = client.post(
            "/api/v1/upload",
            files={"file": ("demo.png", b"fake image bytes", "image/png")},
            headers=AUTH_HEADER,
        )
    finally:
        settings.upload_provider = "local"

    assert response.status_code == 200
    payload = response.json()
    assert payload["url"] == f"https://cos.example.com/{payload['filename']}"
    assert storage_client.calls == [(payload["filename"], b"fake image bytes", "image/png")]


def test_upload_endpoint_rejects_unsupported_extension() -> None:
    configure_upload_auth()
    app = create_app()
    app.dependency_overrides[get_upload_service] = lambda: UploadService()
    client = TestClient(app)

    response = client.post(
        "/api/v1/upload",
        files={"file": ("demo.exe", b"fake image bytes", "image/png")},
        headers=AUTH_HEADER,
    )

    assert response.status_code == 415
    assert response.json()["code"] == "unsupported_upload_type"


def test_upload_endpoint_rejects_unsupported_content_type() -> None:
    configure_upload_auth()
    app = create_app()
    app.dependency_overrides[get_upload_service] = lambda: UploadService()
    client = TestClient(app)

    response = client.post(
        "/api/v1/upload",
        files={"file": ("demo.png", b"plain text", "text/plain")},
        headers=AUTH_HEADER,
    )

    assert response.status_code == 415
    assert response.json()["code"] == "unsupported_upload_type"


def test_upload_endpoint_rejects_oversized_file_without_partial_file() -> None:
    configure_upload_auth()
    upload_dir = Path(".test_uploads")
    if upload_dir.exists():
        rmtree(upload_dir)

    app = create_app()
    app.dependency_overrides[get_upload_service] = lambda: UploadService(upload_dir=upload_dir, max_bytes=4)
    client = TestClient(app)

    try:
        response = client.post(
            "/api/v1/upload",
            files={"file": ("demo.png", b"too large", "image/png")},
            headers=AUTH_HEADER,
        )

        assert response.status_code == 413
        assert response.json()["code"] == "upload_too_large"
        assert list(upload_dir.iterdir()) == []
    finally:
        if upload_dir.exists():
            rmtree(upload_dir)


def test_upload_endpoint_rejects_unsafe_storage_path() -> None:
    configure_upload_auth()
    upload_dir = Path(".test_uploads")
    if upload_dir.exists():
        rmtree(upload_dir)

    app = create_app()
    app.dependency_overrides[get_upload_service] = lambda: UnsafeUploadService(upload_dir=upload_dir)
    client = TestClient(app)

    try:
        response = client.post(
            "/api/v1/upload",
            files={"file": ("demo.png", b"fake image bytes", "image/png")},
            headers=AUTH_HEADER,
        )

        assert response.status_code == 400
        assert response.json()["code"] == "unsafe_upload_path"
        assert not Path("unsafe.png").exists()
    finally:
        if upload_dir.exists():
            rmtree(upload_dir)


def test_vision_recognize_endpoint_returns_mock_product_info() -> None:
    configure_mock_multimodal()
    client = TestClient(create_app())

    response = client.post("/api/v1/vision/recognize", json={"image_url": "/uploads/demo.png"})

    assert response.status_code == 200
    assert response.json() == {
        "category": "\u673a\u68b0\u952e\u76d8",
        "features": ["\u767d\u8272", "\u65e0\u7ebf", "\u7d27\u51d1\u5e03\u5c40"],
        "query": "\u767d\u8272 \u65e0\u7ebf \u7d27\u51d1\u5e03\u5c40 \u673a\u68b0\u952e\u76d8",
    }


def test_upload_endpoint_requires_authentication() -> None:
    configure_upload_auth()
    app = create_app()
    app.dependency_overrides[get_upload_service] = lambda: UploadService()
    client = TestClient(app)

    response = client.post(
        "/api/v1/upload",
        files={"file": ("demo.png", b"fake image bytes", "image/png")},
    )

    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


def test_speech_asr_endpoint_returns_mock_transcription() -> None:
    configure_mock_multimodal()
    client = TestClient(create_app())

    response = client.post("/api/v1/speech/asr", json={"audio_url": "/uploads/demo.wav"})

    assert response.status_code == 200
    assert response.json() == {
        "text": "\u6211\u60f3\u4e70\u4e00\u4e2a\u5bbf\u820d\u7528\u7684\u673a\u68b0\u952e\u76d8\uff0c\u9884\u7b97\u4e09\u767e\u4ee5\u5185"
    }


def test_multimodal_routes_are_registered() -> None:
    app = create_app()
    paths = {route.path for route in app.routes}

    assert "/api/v1/upload" in paths
    assert "/api/v1/vision/recognize" in paths
    assert "/api/v1/speech/asr" in paths
