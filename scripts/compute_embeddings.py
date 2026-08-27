"""
Compute a sentence embedding for every blurb using a small local model
(no API key, no cost). Output: data/embeddings.json, a flat array of
{id, vector} in the same order as blurbs.json, with vectors quantized
to int8 to keep the file small enough to ship to a static site.
"""
import json
from pathlib import Path

import numpy as np

DATA_DIR = Path(__file__).parent.parent / "data"
BLURBS = DATA_DIR / "blurbs.json"
OUT_PATH = DATA_DIR / "embeddings.json"

MODEL_NAME = "all-MiniLM-L6-v2"


def quantize(vectors):
    """int8 quantization: scale each vector's floats into [-127, 127]
    based on a global max-abs value, so cosine similarity is preserved
    well enough for nearest-neighbor search at this corpus size."""
    scale = float(np.abs(vectors).max())
    q = np.round(vectors / scale * 127).astype(np.int8)
    return q, scale


def main():
    """Returns True on success, False if the embedding step could not
    run (e.g. sentence-transformers/torch failed to install in a fresh
    sandbox) -- this step is a nice-to-have (related-blurb links), not
    required for the core job of getting new content published, so a
    failure here must never block the rest of the pipeline."""
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        print(f"SKIPPING embeddings: sentence-transformers unavailable ({e}). "
              f"related.json will not be updated for new blurbs this run.")
        return False

    blurbs = json.loads(BLURBS.read_text())
    texts = [f"{b.get('article_title') or ''}. {b['blurb_text']}".strip() for b in blurbs]

    print(f"Loading {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    print(f"Encoding {len(texts)} blurbs...")
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)

    q, scale = quantize(vectors)
    out = {
        "model": MODEL_NAME,
        "dim": int(q.shape[1]),
        "scale": scale,
        "ids": [b["id"] for b in blurbs],
        "vectors": q.tolist(),
    }
    OUT_PATH.write_text(json.dumps(out))
    print(f"Wrote {len(blurbs)} embeddings ({q.shape[1]} dims, int8) to {OUT_PATH}")
    print(f"File size: {OUT_PATH.stat().st_size / 1024:.0f} KB")
    return True


if __name__ == "__main__":
    main()
