from app.scripts.image_downloads import _suffix_for_url


def test_suffix_for_url_prefers_response_content_type() -> None:
    assert _suffix_for_url("https://cdn.example-real.test/product.png", "image/webp") == ".webp"
    assert _suffix_for_url("https://cdn.example-real.test/product.webp", "image/png") == ".png"
    assert _suffix_for_url("https://cdn.example-real.test/product.jpeg", "image/jpeg") == ".jpg"
