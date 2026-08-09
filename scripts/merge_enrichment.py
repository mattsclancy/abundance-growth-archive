"""
Merge enrichment batch/patch outputs into blurbs.json: adds topics,
article_authors, and fills in article_title (+ article_title_generated)
where it was null. Gap-filling only -- never overwrites a blurb that
already has topics set, so re-running this against the full history of
patch files (including old backfill batches) after a later tag
consolidation pass is always safe.
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
BLURBS = DATA_DIR / "blurbs.json"
BATCH_DIR = DATA_DIR / "enrichment_batches"


def main():
    blurbs = json.loads(BLURBS.read_text())
    by_id = {b["id"]: b for b in blurbs}

    enrichment = {}
    for f in sorted(BATCH_DIR.glob("*_out.json")):
        for rec in json.loads(f.read_text()):
            enrichment[rec["id"]] = rec

    unenriched = [b for b in blurbs if not b.get("topics")]
    still_missing = [b["id"] for b in unenriched if b["id"] not in enrichment]
    extra = [rid for rid in enrichment if rid not in by_id]
    if still_missing:
        print(f"WARNING: {len(still_missing)} blurbs still have no enrichment record: {still_missing}")
    if extra:
        print(f"WARNING: {len(extra)} enrichment records don't match any blurb id: {extra}")

    filled = 0
    for b in unenriched:
        rec = enrichment.get(b["id"])
        if not rec:
            continue
        b["topics"] = rec.get("topics", [])
        b["article_authors"] = rec.get("article_authors", [])
        if b["article_title"] is None and rec.get("generated_title"):
            b["article_title"] = rec["generated_title"]
            b["article_title_generated"] = True
        filled += 1

    BLURBS.write_text(json.dumps(blurbs, indent=2))

    no_title = [b["id"] for b in blurbs if not b.get("article_title")]
    print(f"Filled in enrichment for {filled} blurb(s). {len(blurbs)} total blurbs written.")
    print(f"Blurbs still missing article_title: {len(no_title)} {no_title}")


if __name__ == "__main__":
    main()
