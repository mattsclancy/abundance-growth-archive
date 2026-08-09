"""
Weekly ingestion, step 1: pull in any new posts and get them ready for
enrichment. Run this, then read data/enrichment_batches/pending.json
and produce topics/article_authors/generated_title for each entry
(same rules as the original backfill), write that as a patch file into
data/enrichment_batches/, then run ingest_step2.py.

Safe to run anytime -- every step here is incremental/idempotent, so a
run with nothing new to do is a harmless no-op.
"""
import fetch_archive
import classify
import parse
import list_unenriched

if __name__ == "__main__":
    print("=== fetch_archive ===")
    fetch_archive.fetch_all()
    print("\n=== classify ===")
    classify.main()
    print("\n=== parse ===")
    parse.main()
    print("\n=== list_unenriched ===")
    list_unenriched.main()
