from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate BuyWise in Chromium via Playwright/CDP.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--artifacts-dir", default="artifacts/browser")
    parser.add_argument("--cdp-url", default="", help="Existing Chrome CDP endpoint, for example http://127.0.0.1:9222")
    parser.add_argument("--record-video", action="store_true")
    args = parser.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit("Playwright is not installed. Run: python -m pip install -r requirements.txt") from exc

    artifacts_dir = Path(args.artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    video_dir = artifacts_dir / "videos" if args.record_video else None
    if video_dir:
        video_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        if args.cdp_url:
            browser = p.chromium.connect_over_cdp(args.cdp_url)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
        else:
            browser = p.chromium.launch()
            context = browser.new_context(record_video_dir=str(video_dir) if video_dir else None)

        page = context.new_page()

        health_response = page.request.get(f"{args.base_url}/api/v1/health")
        if not health_response.ok:
            raise SystemExit(f"Health check failed: HTTP {health_response.status}")
        health_payload = health_response.json()

        page.goto(f"{args.base_url}/docs", wait_until="networkidle")
        page.screenshot(path=artifacts_dir / "docs.png", full_page=True)

        snapshot = {
            "title": page.title(),
            "url": page.url,
            "health": health_payload,
            "heading": page.locator("h1, h2").first.text_content(),
            "links": page.locator("a").evaluate_all("(links) => links.map((link) => link.href)"),
        }
        (artifacts_dir / "dom_snapshot.json").write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        context.close()
        browser.close()

    print(f"Browser check passed. Artifacts written to {artifacts_dir}")
