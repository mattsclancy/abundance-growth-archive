"""
Shared helpers for pulling the clean, unrendered post object out of a
Substack page's hydration payload (window._preloads = JSON.parse("...")).
This is far more reliable than scraping the rendered DOM, which adds
anchor-icon markup, auto-generated tables of contents, comment widgets,
etc. that aren't part of what the author actually wrote.
"""
import json
import re

from bs4 import BeautifulSoup, NavigableString

PRELOADS_RE = re.compile(
    r'window\._preloads\s*=\s*JSON\.parse\("(.*?)"\)</script>', re.S
)


def extract_post(html):
    """Return the clean `post` dict (title, post_date, body_html, ...)."""
    m = PRELOADS_RE.search(html)
    if not m:
        raise ValueError("could not find window._preloads blob in page")
    inner_json_text = json.loads('"' + m.group(1) + '"')
    preloads = json.loads(inner_json_text)
    return preloads["post"]


TRAILING_EM_RE = re.compile(r"<em>(.{2,80}?)</em>(\s*</[a-zA-Z0-9]+>)*\s*$", re.S)
TAG_RE = re.compile(r"<[^>]+>")
LEADING_DASH_RE = re.compile(r"^[\s\-–—,]+")


TEAM_ROSTER = [
    "Matt Clancy",
    "Alex Armlovich",
    "Dylan Matthews",
    "Jordan Dworkin",
    "Willow Latham-Proenca",
    "Saloni Dattani",
    "Nisha Austin",
]


def normalize_team_author(name):
    """Map a raw extracted name to the fixed 7-person roster (handles
    stray joke/variant bylines like 'Matt Clancy, Former Daycare
    Worker'). Returns (canonical_name_or_original, matched: bool)."""
    if not name or name == "unknown":
        return name, True
    for canonical in TEAM_ROSTER:
        if canonical.lower() in name.lower():
            return canonical, True
    return name, False


def _drop_trailing_media_blocks(html):
    """Some blurbs end with an embedded image after the author credit
    (credit -- image), rather than the credit being the very last thing.
    Strip trailing <div>/<figure> blocks (image containers, captions)
    so the tail-anchored author check looks at the last real prose."""
    soup = BeautifulSoup(html, "html.parser")
    contents = list(soup.contents)
    while contents and getattr(contents[-1], "name", None) in ("div", "figure"):
        contents.pop()
    return "".join(str(c) for c in contents)


def extract_trailing_author(block_html):
    """If block_html ends in an <em>...</em> credit (optionally wrapping
    nested tags like <strong>/<span>, with any dash style before it, and
    optionally followed by a trailing image block), return the plain
    author name text, else None."""
    stripped = _drop_trailing_media_blocks(block_html).strip()
    m = TRAILING_EM_RE.search(stripped)
    if not m:
        return None
    name = TAG_RE.sub("", m.group(1)).strip()
    name = LEADING_DASH_RE.sub("", name).strip()
    return name or None


TRAILING_DASH_RE = re.compile(r"[\s\-–—,]+$")


def strip_trailing_author_credit(html):
    """Remove the trailing <em>Author</em> credit (and the dash/space
    before it) from era2-style blurb HTML, leaving the surrounding tag
    structure (e.g. the wrapping <p>) intact. No-op if there's no
    trailing credit to find."""
    if extract_trailing_author(html) is None:
        return html
    soup = BeautifulSoup(html, "html.parser")
    ems = soup.find_all("em")
    if not ems:
        return html
    last_em = ems[-1]
    prev = last_em.previous_sibling
    last_em.extract()
    if prev and isinstance(prev, NavigableString):
        prev.replace_with(TRAILING_DASH_RE.sub("", str(prev)))
    return "".join(str(c) for c in soup.contents)
