from pathlib import Path
from shutil import rmtree

from fastapi.testclient import TestClient

from app.api.v1.upload import get_upload_service
from app.main import create_app
from app.services.upload_service import UploadService


def test_upload_endpoint_saves_file_to_local_directory() -> None:
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
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["filename"].endswith(".png")
        assert payload["url"] == f"/uploads/{payload['filename']}"
        assert (upload_dir / payload["filename"]).read_bytes() == b"fake image bytes"
    finally:
        if upload_dir.exists():
            rmtree(upload_dir)


def test_vision_recognize_endpoint_returns_mock_product_info() -> None:
    client = TestClient(create_app())

    response = client.post("/api/v1/vision/recognize", json={"image_url": "/uploads/demo.png"})

    assert response.status_code == 200
    assert response.json() == {
        "category": "\u673a\u68b0\u952e\u76d8",
        "features": ["\u767d\u8272", "\u65e0\u7ebf", "\u7d27\u51d1\u5e03\u5c40"],
        "query": "\u767d\u8272 \u65e0\u7ebf \u7d27\u51d1\u5e03\u5c40 \u673a\u68b0\u952e\u76d8",
    }


def test_speech_asr_endpoint_returns_mock_transcription() -> None:
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
