"""
Weekly ingestion, step 2: run this after writing an enrichment patch
file (see ingest_step1.py / list_unenriched.py) covering every blurb
that was pending. Merges it in, consolidates tags, recomputes
embeddings + related-blurb links, and rebuilds the static site.

Does NOT commit/push -- do that separately once you've sanity-checked
the build (see the repo README for the git steps).
"""
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
    print("\n=== compute_embeddings ===")
    compute_embeddings.main()
    print("\n=== build_related ===")
    build_related.main()
    print("\n=== build_site ===")
    build_site.render_all()
