import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
SITE_DIR = Path(__file__).parent.parent / "site"


def slugify(text):
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s-]+", "-", s).strip("-")
    return s or "unknown"


def load_blurbs():
    return json.loads((DATA_DIR / "blurbs.json").read_text())


def load_related():
    return json.loads((DATA_DIR / "related.json").read_text())


def load_taxonomy():
    return json.loads((DATA_DIR / "taxonomy.json").read_text())


def by_post(blurbs):
    posts = {}
    for b in blurbs:
        posts.setdefault(b["post_slug"], []).append(b)
    for items in posts.values():
        items.sort(key=lambda b: b["order_in_post"])
    return posts


def facet_index(blurbs, field, multi=False):
    """Map facet value -> list of blurbs. `multi` for list-valued fields
    (topics, article_authors)."""
    index = {}
    for b in blurbs:
        values = b[field] if multi else [b[field]]
        for v in values:
            if not v or v == "unknown":
                continue
            index.setdefault(v, []).append(b)
    return index
