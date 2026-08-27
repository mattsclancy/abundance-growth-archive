"""
Weekly ingestion, step 2: run this after writing an enrichment patch
file (see ingest_step1.py / list_unenriched.py) covering every blurb
that was pending. Merges it in, consolidates tags, recomputes
embeddings + related-blurb links, and rebuilds the static site.

merge_enrichment/consolidate_tags/build_site are REQUIRED -- if any of
those raise, this script fails loudly (non-zero exit) and the caller
must not commit/push. compute_embeddings/build_related are
best-effort: getting new content published matters more than the
"related blurbs" nice-to-have, so a failure there (e.g.
sentence-transformers failed to install this run) is logged and
skipped rather than blocking everything else.

Does NOT commit/push -- do that separately once you've sanity-checked
the build (see the repo README for the git steps).
"""
import sys

import merge_enrichment
import consolidate_tags
import compute_embeddings
import build_related
import build_site

if __name__ == "__main__":
    print("=== merge_enrichment ===")
    merge_enrichment.main()

    print("\n=== consolidate_tags ===")
    consolidate_tags.main()

    print("\n=== compute_embeddings (best-effort) ===")
    embeddings_ok = compute_embeddings.main()

    print("\n=== build_related (best-effort) ===")
    if embeddings_ok:
        build_related.main()
    else:
        print("SKIPPING: embeddings step did not succeed this run.")

    print("\n=== build_site ===")
    build_site.render_all()

    if not embeddings_ok:
        print("\nNOTE: embeddings/related-blurb links were NOT updated this run "
              "(sentence-transformers unavailable). Everything else -- new blurbs, "
              "tags, titles, the rebuilt site -- is still correct and safe to commit. "
              "Mention this in your summary so it can be backfilled later.", file=sys.stderr)
