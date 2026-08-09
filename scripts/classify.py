"""
Classify each cached post. The `subtitle` field turns out to be a far more
reliable signal than any structural heuristic -- the team has consistently
subtitled every entry in the "what we're reading" franchise, in one of
four variants:
    "What we're reading, <date>"        -> normal weekly roundup
    "What we're reading spotlight"      -> single-author deep dive
    "A special edition of what we're reading" -> team member each write one
    "A look back at key readings..."    -> quarterly digest (excluded)
"Job Market Papers" posts are identified by title, not subtitle (their
subtitle is the unrelated "Where new researchers are looking").
Everything else is a solo essay / team post / unrelated (excluded).

For normal roundups we still inspect body_html structurally to pick the
right per-era parser later (era1/2/3).
"""
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

from substack import extract_post, extract_trailing_author

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
POSTS_INDEX = RAW_DIR / "posts_index.json"

DIGEST_TITLE_RE = re.compile(r"\d+\s+things to read about abundance", re.I)
DIGEST_SUBTITLE_RE = re.compile(r"^a look back at key readings", re.I)
JOB_MARKET_TITLE_RE = re.compile(r"job market papers", re.I)
SPOTLIGHT_SUBTITLE_RE = re.compile(r"reading spotlight", re.I)
SPECIAL_EDITION_SUBTITLE_RE = re.compile(r"special edition of what we.re reading", re.I)
NORMAL_SUBTITLE_RE = re.compile(r"^what we.re reading\b", re.I)

H4_BLOCK_RE = re.compile(r"<h4[^>]*>(.*?)</h4>", re.S)
OL_BLOCK_RE = re.compile(r"<ol[^>]*>(.*?)</ol>", re.S)


def all_ol_items(body_html):
    """Direct-child <li> of each top-level <ol>, as inner HTML strings.
    Ignores nested sub-<ul>/<ol> content -- some posts have sub-bullets
    elaborating one item, which must stay part of that item's blurb
    rather than becoming separate top-level items."""
    soup = BeautifulSoup(body_html, "html.parser")
    items = []
    for ol in soup.find_all("ol", recursive=True):
        # skip <ol> that are themselves nested inside another <li>
        # (already covered when we process their parent <ol>)
        if ol.find_parent("li"):
            continue
        for li in ol.find_all("li", recursive=False):
            items.append("".join(str(c) for c in li.contents))
    return items


def classify(post):
    title = post.get("title") or ""
    subtitle = post.get("subtitle") or ""
    body_html = post["body_html"]

    if DIGEST_TITLE_RE.search(title) or DIGEST_SUBTITLE_RE.search(subtitle):
        return "digest", {}
    if JOB_MARKET_TITLE_RE.search(title):
        return "job_market", {}
    if SPOTLIGHT_SUBTITLE_RE.search(subtitle):
        return "spotlight", {}
    if SPECIAL_EDITION_SUBTITLE_RE.search(subtitle):
        return "special_edition", {}
    if not NORMAL_SUBTITLE_RE.search(subtitle):
        return "other", {}

    # it's a normal roundup -- figure out which era's parser it needs
    h4_blocks = H4_BLOCK_RE.findall(body_html)
    era3_hits = sum(1 for h in h4_blocks if extract_trailing_author(h))

    li_items = all_ol_items(body_html)
    li_count = len(li_items)
    era2_hits = sum(1 for li in li_items if extract_trailing_author(li))

    stats = {"h4_count": len(h4_blocks), "era3_hits": era3_hits,
             "li_count": li_count, "era2_hits": era2_hits}

    if era3_hits >= 3:
        return "roundup_era3", stats
    if li_count and era2_hits / li_count >= 0.5:
        return "roundup_era2", stats
    if li_count:
        return "roundup_era1", stats
    return "roundup_unrecognized", stats


def main():
    posts = json.loads(POSTS_INDEX.read_text())
    out_path = RAW_DIR.parent / "classification.json"
    results = json.loads(out_path.read_text()) if out_path.exists() else []
    known_slugs = {r["slug"] for r in results}

    new_results = []
    for p in posts:
        if p["slug"] in known_slugs:
            continue
        html = (RAW_DIR / f"{p['slug']}.html").read_text()
        post = extract_post(html)
        label, stats = classify(post)
        new_results.append({**p, "subtitle": post.get("subtitle"), "label": label, "stats": stats})

    results.extend(new_results)
    out_path.write_text(json.dumps(results, indent=2))

    counts = {}
    for r in results:
        counts[r["label"]] = counts.get(r["label"], 0) + 1
    print("Counts (all-time):", counts)
    print()
    if new_results:
        print(f"{len(new_results)} newly classified post(s):")
        for r in new_results:
            print(f"[{r['label']:19}] {r['post_date'][:10]}  {r['slug']:55} stats={r['stats']}")
    else:
        print("No new posts to classify.")


if __name__ == "__main__":
    main()
