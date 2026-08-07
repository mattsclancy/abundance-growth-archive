"""
Parse every included post (per classification.json) into individual
blurb records. Structural parsing only -- no LLM calls here. Output:
data/blurbs.json, a flat list of:

  {
    id, post_slug, post_url, post_date, order_in_post, format_era,
    team_author,            # one of the 7 names, or "unknown" (era1)
    article_title,          # present for era3/spotlight/special_edition;
                            # null for era1/era2 (LLM fills this in later)
    article_title_generated,# bool, set in the enrichment pass
    article_urls,           # list of external hrefs cited in this blurb
    blurb_html,             # inner HTML of the blurb body
    blurb_text,             # plain-text version
  }
"""
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

from substack import extract_post, extract_trailing_author, normalize_team_author, strip_trailing_author_credit

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
DATA_DIR = RAW_DIR.parent
CLASSIFICATION = DATA_DIR / "classification.json"
OUT_PATH = DATA_DIR / "blurbs.json"

TAG_RE = re.compile(r"<[^>]+>")
AUTHOR_MISMATCHES = []


def plain_text(html):
    return re.sub(r"\s+", " ", TAG_RE.sub(" ", html)).strip()


def extract_links(html):
    soup = BeautifulSoup(html, "html.parser")
    seen = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href not in seen:
            seen.append(href)
    return seen


def top_level_ol_items(body_html):
    """Direct-child <li> of every top-level <ol>, merging <ol>/<ol
    start=N> fragments (Substack splits one logical list whenever
    something like an image interrupts it)."""
    soup = BeautifulSoup(body_html, "html.parser")
    items = []
    for ol in soup.find_all("ol"):
        if ol.find_parent("li"):
            continue
        for li in ol.find_all("li", recursive=False):
            items.append("".join(str(c) for c in li.contents))
    return items


def make_blurb(post, order, team_author, article_title, blurb_html, article_title_generated=False):
    canonical, matched = normalize_team_author(team_author)
    if not matched:
        AUTHOR_MISMATCHES.append(f"{post['slug']} #{order}: unrecognized author {team_author!r}")
    return {
        "post_slug": post["slug"],
        "post_url": post["canonical_url"],
        "post_title": post["title"],
        "post_date": post["post_date"],
        "order_in_post": order,
        "format_era": post["_label"],
        "team_author": canonical,
        "article_title": article_title,
        "article_title_generated": article_title_generated,
        "article_urls": extract_links(blurb_html),
        "blurb_html": blurb_html.strip(),
        "blurb_text": plain_text(blurb_html),
    }


def parse_era1(post):
    """No per-item author delimiter -- team_author is unknown, to be
    hand-labeled. No article_title either -- LLM fills it in later."""
    items = top_level_ol_items(post["body_html"])
    return [
        make_blurb(post, i + 1, "unknown", None, html)
        for i, html in enumerate(items)
    ]


def parse_era2(post):
    """<li> ending in an <em>Author</em> credit; no separate title."""
    items = top_level_ol_items(post["body_html"])
    blurbs = []
    for i, html in enumerate(items):
        author = extract_trailing_author(html) or "unknown"
        body = strip_trailing_author_credit(html.strip())
        blurbs.append(make_blurb(post, i + 1, author, None, body))
    return blurbs


def parse_era3(post):
    """<h4>Title ... <em>Author</em></h4><p>...</p><p>...</p> blocks.
    The <ol> at the top of body_html is a redundant table of contents
    mirroring these headings -- skip it entirely."""
    soup = BeautifulSoup(post["body_html"], "html.parser")
    all_h4 = soup.find_all("h4")
    h4_inner = {id(h): "".join(str(c) for c in h.contents) for h in all_h4}
    h4s = [h for h in all_h4 if extract_trailing_author(h4_inner[id(h)])]

    blurbs = []
    for i, h4 in enumerate(h4s):
        title_html = h4_inner[id(h4)]
        author = extract_trailing_author(title_html)
        title = plain_text(re.sub(r"<em>.{0,80}?</em>\s*$", "", title_html, count=1))
        title = re.sub(r"[\s\-–—,:]+$", "", title).strip()

        # collect sibling content up to the next <h4> (or end)
        body_parts = []
        for sib in h4.find_next_siblings():
            if sib.name == "h4":
                break
            body_parts.append(str(sib))
        body_html = "".join(body_parts)
        blurbs.append(make_blurb(post, i + 1, author, title, body_html))
    return blurbs


def parse_spotlight(post):
    author = None
    bylines = post.get("publishedBylines") or []
    if bylines:
        author = bylines[0].get("name")
    return [make_blurb(post, 1, author or "unknown", post["title"], post["body_html"])]


NAME_LEAD_RE = re.compile(r"^([A-Z][\w.\'’-]+(?: [A-Z][\w.\'’-]+){0,2})\s*:\s*(.*)$", re.S)


def parse_special_edition(post):
    """'FirstName LastName: text' paragraphs, one per team member. The
    leading "Name:" is left in blurb_html/blurb_text (its exact markup
    varies -- sometimes bolded, sometimes not -- not worth the fragility
    of stripping it byte-for-byte); team_author already carries the
    parsed name for display purposes."""
    soup = BeautifulSoup(post["body_html"], "html.parser")
    blurbs = []
    order = 0
    for p in soup.find_all("p"):
        text_html = "".join(str(c) for c in p.contents)
        text_plain = plain_text(text_html)
        m = NAME_LEAD_RE.match(text_plain)
        if not m:
            continue
        order += 1
        blurbs.append(make_blurb(post, order, m.group(1), None, text_html, article_title_generated=False))
    return blurbs


PARSERS = {
    "roundup_era1": parse_era1,
    "roundup_era2": parse_era2,
    "roundup_era3": parse_era3,
    "spotlight": parse_spotlight,
    "special_edition": parse_special_edition,
}


def main():
    classification = json.loads(CLASSIFICATION.read_text())
    all_blurbs = []
    problems = []

    for entry in classification:
        label = entry["label"]
        if label not in PARSERS:
            continue
        html = (RAW_DIR / f"{entry['slug']}.html").read_text()
        post = extract_post(html)
        post["_label"] = label
        try:
            blurbs = PARSERS[label](post)
        except Exception as e:
            problems.append(f"{entry['slug']}: parser error: {e}")
            continue

        if not blurbs:
            problems.append(f"{entry['slug']} ({label}): parser produced 0 blurbs")
        for b in blurbs:
            b["id"] = f"{entry['slug']}-{b['order_in_post']}"

            is_ol_era = b["format_era"] in ("roundup_era2", "roundup_era3")
            word_count = len(b["blurb_text"].split())
            if is_ol_era and b["team_author"] == "unknown":
                if word_count < 15 and not b["article_urls"]:
                    problems.append(f"{b['id']}: dropped -- no author, no link, only {word_count} words ({b['blurb_text']!r})")
                    continue
                problems.append(f"{b['id']}: KEPT but missing author attribution -- needs manual review ({b['blurb_text'][:80]!r})")

            if len(b["blurb_text"]) < 20:
                problems.append(f"{b['id']}: suspiciously short blurb_text ({b['blurb_text']!r})")
            all_blurbs.append(b)

    problems.extend(AUTHOR_MISMATCHES)

    OUT_PATH.write_text(json.dumps(all_blurbs, indent=2))
    print(f"Wrote {len(all_blurbs)} blurbs from {len(classification)} classified posts to {OUT_PATH}")
    if problems:
        print(f"\n{len(problems)} PROBLEMS flagged for review:")
        for p in problems:
            print(" -", p)


if __name__ == "__main__":
    main()
