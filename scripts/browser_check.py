from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate BuyWise in Chromium via Playwright/CDP.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--artifacts-dir", default="artifacts/browser")
    parser.add_argument("--cdp-url", default="", help="Existing Chrome CDP endpoint, for example http://127.0.0.1:9222")
    parser.add_argument("--record-video", action="store_true")
    return parser.parse_args()


def load_playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit("Playwright is not installed. Run: python -m pip install -r requirements.txt") from exc
    return sync_playwright


def prepare_artifacts_dir(path: Path, record_video: bool) -> Path | None:
    path.mkdir(parents=True, exist_ok=True)
    video_dir = path / "videos" if record_video else None
    if video_dir:
        video_dir.mkdir(parents=True, exist_ok=True)
    return video_dir


def open_browser(playwright, cdp_url: str, video_dir: Path | None):
    if cdp_url:
        browser = playwright.chromium.connect_over_cdp(cdp_url)
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        return browser, context

    browser = playwright.chromium.launch()
    context = browser.new_context(record_video_dir=str(video_dir) if video_dir else None)
    return browser, context


def build_snapshot(page, health_payload: dict[str, object]) -> dict[str, object]:
    return {
        "title": page.title(),
        "url": page.url,
        "health": health_payload,
        "heading": page.locator("h1, h2").first.text_content(),
        "links": page.locator("a").evaluate_all("(links) => links.map((link) => link.href)"),
    }


def write_snapshot(artifacts_dir: Path, page, health_payload: dict[str, object]) -> None:
    snapshot = build_snapshot(page, health_payload)
    (artifacts_dir / "dom_snapshot.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    sync_playwright = load_playwright()
    artifacts_dir = Path(args.artifacts_dir)
    video_dir = prepare_artifacts_dir(artifacts_dir, args.record_video)

    with sync_playwright() as p:
        browser, context = open_browser(p, args.cdp_url, video_dir)
        page = context.new_page()
        health_response = page.request.get(f"{args.base_url}/api/v1/health")
        if not health_response.ok:
            raise SystemExit(f"Health check failed: HTTP {health_response.status}")
        health_payload = health_response.json()
        page.goto(f"{args.base_url}/docs", wait_until="networkidle")
        page.screenshot(path=artifacts_dir / "docs.png", full_page=True)
        write_snapshot(artifacts_dir, page, health_payload)
        context.close()
        browser.close()

    print(f"Browser check passed. Artifacts written to {artifacts_dir}")
