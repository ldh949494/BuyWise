from pathlib import Path

from scripts.validate_secrets import scan_file


def test_secret_scan_rejects_high_confidence_openai_key(tmp_path: Path) -> None:
    secret = "sk-" + ("A" * 40)
    path = tmp_path / "sample.txt"
    path.write_text(f"LLM_API_KEY={secret}\n", encoding="utf-8")

    findings = scan_file(path)

    assert [finding.pattern for finding in findings] == ["OpenAI API key"]
    assert all(secret not in finding.render() for finding in findings)


def test_secret_scan_allows_public_product_slug(tmp_path: Path) -> None:
    path = tmp_path / "products.csv"
    path.write_text(
        "https://www.ikea.com/us/en/p/roedflik-desk-lamp-light-beige-40584057/\n",
        encoding="utf-8",
    )

    assert scan_file(path) == []
