"""
Fetch the full post list for the Abundance and Growth Substack via
sitemap.xml (the archive API's offset/limit pagination turned out to
silently skip posts -- sitemap.xml is the reliable enumeration), then
fetch each post's raw HTML body. Caches everything to disk under
data/raw/ so we don't hammer the site on every dev run.
"""
import json
import re
import time
from pathlib import Path

import requests

BASE = "https://www.abundanceandgrowth.org"
RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)
POSTS_INDEX = RAW_DIR / "posts_index.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AGArchiveBot/1.0)"}

DATE_PUBLISHED_RE = re.compile(r'"datePublished"\s*:\s*"([^"]+)"')
TITLE_RE = re.compile(r'"headline"\s*:\s*"((?:[^"\\]|\\.)*)"')


def fetch_slugs_from_sitemap():
    resp = requests.get(f"{BASE}/sitemap.xml", headers=HEADERS, timeout=30)
    resp.raise_for_status()
    locs = re.findall(r"<loc>([^<]+)</loc>", resp.text)
    slugs = []
    for url in locs:
        m = re.match(rf"{re.escape(BASE)}/p/([^/]+)/?$", url.strip())
        if m:
            slugs.append(m.group(1))
    return slugs


def extract_date_and_title(html):
    date_match = DATE_PUBLISHED_RE.search(html)
    title_match = TITLE_RE.search(html)
    post_date = date_match.group(1) if date_match else None
    title = title_match.group(1).encode().decode("unicode_escape") if title_match else None
    return post_date, title


def fetch_post_index(force=False):
    """Enumerate every post via sitemap.xml, then pull date+title out of
    each post's own HTML (the archive API can't be trusted for this)."""
    if POSTS_INDEX.exists() and not force:
        return json.loads(POSTS_INDEX.read_text())

    slugs = fetch_slugs_from_sitemap()
    posts = []
    for i, slug in enumerate(slugs):
        html = fetch_post_html(slug, force=force)
        post_date, title = extract_date_and_title(html)
        posts.append({
            "slug": slug,
            "title": title,
            "post_date": post_date,
            "canonical_url": f"{BASE}/p/{slug}",
        })
        print(f"  [{i+1}/{len(slugs)}] {slug} -> {post_date} | {title}")

    posts.sort(key=lambda p: p["post_date"] or "", reverse=True)
    POSTS_INDEX.write_text(json.dumps(posts, indent=2))
    return posts


def slug_html_path(slug):
    return RAW_DIR / f"{slug}.html"


def fetch_post_html(slug, canonical_url=None, force=False):
    path = slug_html_path(slug)
    if path.exists() and not force:
        return path.read_text()

    url = canonical_url or f"{BASE}/p/{slug}"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    path.write_text(resp.text)
    time.sleep(0.3)
    return resp.text


def fetch_all(force=False):
    posts = fetch_post_index(force=force)
    print(f"Found {len(posts)} total posts in archive.")
    return posts


if __name__ == "__main__":
    fetch_all()
