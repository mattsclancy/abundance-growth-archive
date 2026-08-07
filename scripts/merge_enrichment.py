"""
Merge the 8 enrichment batch outputs into blurbs.json: adds topics,
article_authors, and fills in article_title (+ article_title_generated)
where it was null.
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
    for f in sorted(BATCH_DIR.glob("batch_*_out.json")):
        for rec in json.loads(f.read_text()):
            enrichment[rec["id"]] = rec

    missing = [b["id"] for b in blurbs if b["id"] not in enrichment]
    extra = [rid for rid in enrichment if rid not in by_id]
    if missing:
        print(f"WARNING: {len(missing)} blurbs have no enrichment record: {missing}")
    if extra:
        print(f"WARNING: {len(extra)} enrichment records don't match any blurb id: {extra}")

    for b in blurbs:
        rec = enrichment.get(b["id"])
        if not rec:
            continue
        b["topics"] = rec.get("topics", [])
        b["article_authors"] = rec.get("article_authors", [])
        if b["article_title"] is None and rec.get("generated_title"):
            b["article_title"] = rec["generated_title"]
            b["article_title_generated"] = True

    BLURBS.write_text(json.dumps(blurbs, indent=2))

    no_topics = [b["id"] for b in blurbs if not b.get("topics")]
    no_title = [b["id"] for b in blurbs if not b.get("article_title")]
    print(f"Merged. {len(blurbs)} blurbs written.")
    print(f"Blurbs with no topics: {len(no_topics)} {no_topics}")
    print(f"Blurbs still missing article_title: {len(no_title)} {no_title}")


if __name__ == "__main__":
    main()
