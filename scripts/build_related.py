"""
Precompute the top-5 nearest-neighbor blurbs for each blurb (by
embedding cosine similarity, excluding blurbs from the same post --
those are already surfaced via "more from this issue"). Baked in at
build time so blurb pages don't need to ship all 203 vectors to every
visitor just to show 5 related links.
"""
import json
from pathlib import Path

import numpy as np

DATA_DIR = Path(__file__).parent.parent / "data"
EMBEDDINGS = DATA_DIR / "embeddings.json"
BLURBS = DATA_DIR / "blurbs.json"
OUT_PATH = DATA_DIR / "related.json"

TOP_K = 5


def main():
    emb = json.loads(EMBEDDINGS.read_text())
    blurbs = {b["id"]: b for b in json.loads(BLURBS.read_text())}
    ids = emb["ids"]
    vectors = np.array(emb["vectors"], dtype=np.float32) * emb["scale"] / 127.0
    norms = np.linalg.norm(vectors, axis=1) + 1e-8

    related = {}
    for i, bid in enumerate(ids):
        sims = vectors @ vectors[i] / (norms * norms[i])
        order = np.argsort(-sims)
        post_slug = blurbs[bid]["post_slug"]
        picks = []
        for j in order:
            if ids[j] == bid:
                continue
            if blurbs[ids[j]]["post_slug"] == post_slug:
                continue
            picks.append(ids[j])
            if len(picks) == TOP_K:
                break
        related[bid] = picks

    OUT_PATH.write_text(json.dumps(related, indent=2))
    print(f"Wrote related-blurb lists for {len(related)} blurbs to {OUT_PATH}")


if __name__ == "__main__":
    main()
