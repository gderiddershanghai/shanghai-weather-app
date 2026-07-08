# pipeline/og_images.py
# Build-time Open Graph thumbnail fetcher for curated events. Run LOCALLY
# (not in CI — news sites block bots and paywall intermittently); resulting
# thumbnails are committed to git under static/data/derived/event-images/.
#
#   python3 -m pipeline.og_images [--force]

from __future__ import annotations

import argparse
import io
import sys

import requests
from bs4 import BeautifulSoup
from PIL import Image

from .config import EVENT_IMAGES_DIR

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
THUMB_WIDTH = 640
JPEG_QUALITY = 80


def _og_image_url(article_url: str) -> str | None:
    resp = requests.get(article_url, headers={"User-Agent": UA}, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for selector in (
        ("meta", {"property": "og:image"}),
        ("meta", {"name": "twitter:image"}),
        ("meta", {"property": "twitter:image"}),
    ):
        tag = soup.find(*selector[:1], attrs=selector[1])
        if tag and tag.get("content", "").startswith("http"):
            return tag["content"]
    return None


def _save_thumbnail(image_url: str, slug: str) -> str:
    resp = requests.get(image_url, headers={"User-Agent": UA}, timeout=30)
    resp.raise_for_status()
    img = Image.open(io.BytesIO(resp.content)).convert("RGB")
    if img.width > THUMB_WIDTH:
        img = img.resize((THUMB_WIDTH, round(img.height * THUMB_WIDTH / img.width)))
    out = EVENT_IMAGES_DIR / f"{slug}.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "JPEG", quality=JPEG_QUALITY, optimize=True)
    return out.name


def fetch_event_images(events: list[dict], force: bool = False) -> None:
    """Fetch OG thumbnails for events that have article URLs. Failures are warnings."""
    for event in events:
        slug = event["id"]
        target = EVENT_IMAGES_DIR / f"{slug}.jpg"
        if target.exists() and not force:
            continue
        urls = [
            link["url"]
            for lang in ("en", "zh")
            if (link := (event.get("links") or {}).get(lang)) and link.get("url")
        ]
        for url in urls:
            try:
                og = _og_image_url(url)
                if og:
                    name = _save_thumbnail(og, slug)
                    print(f"  {slug}: saved {name}")
                    break
            except Exception as exc:  # noqa: BLE001 — never fail the build over a thumbnail
                print(f"  {slug}: WARN {type(exc).__name__}: {exc}", file=sys.stderr)
        else:
            if urls:
                print(f"  {slug}: no og:image found")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch OG thumbnails for curated events")
    parser.add_argument("--force", action="store_true", help="refetch existing thumbnails")
    args = parser.parse_args()

    from .events_curated import load_curated_events

    fetch_event_images(load_curated_events(), force=args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
