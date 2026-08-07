"""
Compute a sentence embedding for every blurb using a small local model
(no API key, no cost). Output: data/embeddings.json, a flat array of
{id, vector} in the same order as blurbs.json, with vectors quantized
to int8 to keep the file small enough to ship to a static site.
"""
import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

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


if __name__ == "__main__":
    main()
