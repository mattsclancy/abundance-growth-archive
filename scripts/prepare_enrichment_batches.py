"""
Group blurbs by post into small batches (a few posts each) for parallel
LLM enrichment. Each batch file gives the agent everything it needs
(core tag list + blurb text/links) and nothing it doesn't.
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
BLURBS = DATA_DIR / "blurbs.json"
TAXONOMY = DATA_DIR / "taxonomy.json"
BATCH_DIR = DATA_DIR / "enrichment_batches"
POSTS_PER_BATCH = 4


def main():
    blurbs = json.loads(BLURBS.read_text())
    taxonomy = json.loads(TAXONOMY.read_text())

    by_post = {}
    for b in blurbs:
        by_post.setdefault(b["post_slug"], []).append(b)

    slugs = list(by_post.keys())
    BATCH_DIR.mkdir(exist_ok=True)
    for f in BATCH_DIR.glob("batch_*.json"):
        f.unlink()

    batch_num = 0
    for i in range(0, len(slugs), POSTS_PER_BATCH):
        batch_slugs = slugs[i:i + POSTS_PER_BATCH]
        batch_blurbs = []
        for slug in batch_slugs:
            for b in by_post[slug]:
                batch_blurbs.append({
                    "id": b["id"],
                    "post_title": b["post_title"],
                    "format_era": b["format_era"],
                    "existing_article_title": b["article_title"],
                    "team_author": b["team_author"],
                    "article_urls": b["article_urls"],
                    "blurb_text": b["blurb_text"],
                })
        batch_num += 1
        out = BATCH_DIR / f"batch_{batch_num:02d}.json"
        out.write_text(json.dumps({"core_tags": taxonomy["core_tags"], "blurbs": batch_blurbs}, indent=2))
        print(f"{out.name}: {len(batch_slugs)} posts, {len(batch_blurbs)} blurbs")

    print(f"\n{batch_num} batches written to {BATCH_DIR}")


if __name__ == "__main__":
    main()
