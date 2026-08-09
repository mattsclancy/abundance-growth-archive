"""
Print every blurb still missing enrichment (topics == []), in the same
shape used for the original backfill batches, so whoever/whatever is
doing the enrichment (a scheduled agent, a human, a one-off script) has
a clean, self-contained input. Also writes it to
data/enrichment_batches/pending.json for convenience.
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
BLURBS = DATA_DIR / "blurbs.json"
TAXONOMY = DATA_DIR / "taxonomy.json"
OUT_PATH = DATA_DIR / "enrichment_batches" / "pending.json"


def main():
    blurbs = json.loads(BLURBS.read_text())
    taxonomy = json.loads(TAXONOMY.read_text())
    pending = [b for b in blurbs if not b.get("topics")]

    payload = {
        "core_tags": taxonomy["core_tags"],
        "blurbs": [
            {
                "id": b["id"],
                "post_title": b["post_title"],
                "format_era": b["format_era"],
                "existing_article_title": b["article_title"],
                "team_author": b["team_author"],
                "article_urls": b["article_urls"],
                "blurb_text": b["blurb_text"],
            }
            for b in pending
        ],
    }
    OUT_PATH.parent.mkdir(exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2))
    print(f"{len(pending)} blurb(s) need enrichment. Wrote input to {OUT_PATH}")
    for b in pending:
        print(" -", b["id"])


if __name__ == "__main__":
    main()
