# Abundance and Growth — What We're Reading Archive

A searchable, browsable archive of every blurb from the [Abundance and
Growth](https://www.abundanceandgrowth.org/t/links) weekly reading
roundup, split out into individual objects (one per blurb) with author,
topic, and cross-link navigation.

## How it works

1. `scripts/fetch_archive.py` — enumerates every post via `sitemap.xml`
   and caches each post's raw HTML to `data/raw/` (gitignored).
2. `scripts/classify.py` — classifies each post (normal roundup /
   spotlight / special edition / quarterly digest / job-market papers /
   other) using the post's `subtitle` field, which the team has
   consistently used for this since the newsletter started.
3. `scripts/parse.py` — parses each included post into individual blurb
   records per its format era, into `data/blurbs.json`.
4. `scripts/prepare_enrichment_batches.py` + LLM enrichment (see below)
   + `scripts/merge_enrichment.py` + `scripts/consolidate_tags.py` — adds
   topic tags, external "article author" extraction, and generates
   titles for blurbs whose original format didn't have one.
5. `scripts/compute_embeddings.py` + `scripts/build_related.py` — local
   sentence-transformers model computes a "related blurbs" list per
   blurb (no API key needed).
6. `scripts/build_site.py` — renders the static site (Jinja2 templates
   in `templates/`, output in `site/`).

## Local development

```
source venv/bin/activate
python scripts/build_site.py
cd site && python -m http.server 8765
```

## Data model

Each blurb (`data/blurbs.json`) has:
- `team_author` — one of the 7 team members, or `"unknown"` for the
  handful of earliest-format posts that didn't credit a per-item author
- `article_title`, `article_authors`, `article_urls` — about the
  external thing being discussed
- `topics` — 1-3 tags; the team's official focus areas are preferred,
  with descriptive ad-hoc tags for anything else (see
  `data/taxonomy.json` and `scripts/consolidate_tags.py`)

## Known manual follow-up

9 blurbs (all from the single earliest-format post,
`what-were-reading-january-8-2026`) have `team_author: "unknown"` and
need hand-labeling.
