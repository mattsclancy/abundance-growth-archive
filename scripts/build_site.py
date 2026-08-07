"""
Render the full static site from data/blurbs.json + data/related.json
into site/. Pure Jinja2 templating, no JS build step -- the client-side
filtering in static/app.js operates on data-* attributes already baked
into the rendered HTML, so there's no separate data.json to keep in sync.
"""
import shutil
from collections import Counter
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from site_common import SITE_DIR, load_blurbs, load_related, by_post, facet_index, slugify

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
ROOT = "/"


def render_all():
    blurbs = load_blurbs()
    related = load_related()
    posts = by_post(blurbs)
    by_id = {b["id"]: b for b in blurbs}

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    env.filters["slugify"] = slugify

    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir(parents=True)
    (SITE_DIR / "static").mkdir()
    for f in (Path(__file__).parent.parent / "site_static_src").glob("*"):
        shutil.copy(f, SITE_DIR / "static" / f.name)

    def write(rel_path, template_name, **ctx):
        out = SITE_DIR / rel_path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(env.get_template(template_name).render(root=ROOT, **ctx))

    # ---- home ----
    team_author_counts = Counter(b["team_author"] for b in blurbs if b["team_author"] != "unknown")
    topic_counts = Counter(t for b in blurbs for t in b["topics"])
    dates = sorted(b["post_date"][:10] for b in blurbs)
    write(
        "index.html", "index.html",
        blurbs=sorted(blurbs, key=lambda b: (b["post_date"], b["order_in_post"]), reverse=True),
        team_authors=sorted(team_author_counts.items()),
        topics=sorted(topic_counts.items(), key=lambda kv: -kv[1]),
        issue_count=len(posts),
        earliest=dates[0], latest=dates[-1],
    )

    # ---- blurb detail pages ----
    for b in blurbs:
        siblings = [s for s in posts[b["post_slug"]] if s["id"] != b["id"]]
        rel_ids = related.get(b["id"], [])
        write(
            f"blurb/{b['id']}/index.html", "blurb.html",
            b=b, siblings=siblings, related=[by_id[r] for r in rel_ids if r in by_id],
        )

    # ---- team author pages ----
    author_facet = facet_index(blurbs, "team_author")
    for name, items in author_facet.items():
        write(
            f"author/{slugify(name)}/index.html", "listing.html",
            heading=name, subhead=f"{len(items)} blurbs",
            blurbs=sorted(items, key=lambda b: b["post_date"], reverse=True),
            back_href="authors/", back_label="All team members",
        )
    write(
        "authors/index.html", "directory.html", heading="Team",
        items=sorted(
            [(name, f"author/{slugify(name)}/", len(items)) for name, items in author_facet.items()]
        ),
    )

    # ---- article author ("writer") pages ----
    writer_facet = facet_index(blurbs, "article_authors", multi=True)
    for name, items in writer_facet.items():
        write(
            f"writer/{slugify(name)}/index.html", "listing.html",
            heading=name, subhead=f"{len(items)} blurb{'s' if len(items) != 1 else ''} citing this writer/publication",
            blurbs=sorted(items, key=lambda b: b["post_date"], reverse=True),
            back_href="writers/", back_label="All writers",
        )
    write(
        "writers/index.html", "directory.html", heading="Writers cited",
        items=sorted(
            [(name, f"writer/{slugify(name)}/", len(items)) for name, items in writer_facet.items()],
            key=lambda t: t[0].lower(),
        ),
    )

    # ---- topic pages ----
    topic_facet = facet_index(blurbs, "topics", multi=True)
    for name, items in topic_facet.items():
        write(
            f"topic/{slugify(name)}/index.html", "listing.html",
            heading=name, subhead=f"{len(items)} blurbs",
            blurbs=sorted(items, key=lambda b: b["post_date"], reverse=True),
            back_href="topics/", back_label="All topics",
        )
    write(
        "topics/index.html", "directory.html", heading="Topics",
        items=sorted(
            [(name, f"topic/{slugify(name)}/", len(items)) for name, items in topic_facet.items()],
            key=lambda t: -t[2],
        ),
    )

    # ---- issue (single post) pages ----
    for slug, items in posts.items():
        write(
            f"issue/{slug}/index.html", "listing.html",
            heading=items[0]["post_title"], subhead=items[0]["post_date"][:10],
            blurbs=items,
            back_href="issues/", back_label="All issues",
        )
    write(
        "issues/index.html", "directory.html", heading="Issues",
        items=sorted(
            [(items[0]["post_title"], f"issue/{slug}/", len(items)) for slug, items in posts.items()],
            key=lambda t: t[1], reverse=True,
        ),
    )

    print(f"Built {len(blurbs)} blurb pages, {len(author_facet)} author pages, "
          f"{len(writer_facet)} writer pages, {len(topic_facet)} topic pages, "
          f"{len(posts)} issue pages into {SITE_DIR}")


if __name__ == "__main__":
    render_all()
