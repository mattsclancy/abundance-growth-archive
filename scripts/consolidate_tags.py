"""
One-time consolidation pass over the ad-hoc tags the enrichment agents
coined: merges near-synonyms into shared categories (reviewed by hand
against the actual blurb content, not just tag-name similarity), and
leaves genuinely one-off topics alone. Re-run whenever a new batch of
ad-hoc tags accumulates during ongoing ingestion.
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
BLURBS = DATA_DIR / "blurbs.json"

TAG_MERGE_MAP = {
    "Institutional History": "History & Biography",
    "Science History & Media": "History & Biography",
    "Technology & Economic History": "History & Biography",

    "Prediction Markets": "Markets & Mechanism Design",
    "Market Shaping": "Markets & Mechanism Design",

    "Climate & Wildfires": "Environment & Climate",
    "Wildfire Policy": "Environment & Climate",
    "Environmental Policy": "Environment & Climate",
    "Regulatory Uncertainty": "Environment & Climate",

    "Biomedical Research": "Biotech & Pharma",
    "Biotech & Pharma Finance": "Biotech & Pharma",
    "Biotech & Medicine": "Biotech & Pharma",
    "Biotech Industry": "Biotech & Pharma",

    "Executive Power & Independent Agencies": "State Capacity",
    "Congress & Legislation": "State Capacity",
    "State & Local Abundance Agendas": "State Capacity",

    "US-Europe Growth Gap": "International Comparisons",
    "EU Institutions & Careers": "International Comparisons",

    "Metascience & Research Integrity": "Philanthropy & Metascience",
    "Metascience": "Philanthropy & Metascience",
    "State-Level Science Funding": "Philanthropy & Metascience",

    "Poverty & Social Policy": "Health & Social Policy",
    "Childcare Policy": "Health & Social Policy",
    "Health Care Policy": "Health & Social Policy",

    "Well-Being & Social Trends": "Progress Studies",
    "Belief in Progress": "Progress Studies",
    "Reflections on Abundance": "Progress Studies",
    "Public Opinion & Measurement": "Progress Studies",

    "Policy Communication": "Science & Policy Communication",
    "Science Communication": "Science & Policy Communication",

    "Immigration Policy": "High-Skilled Immigration",
}


def main():
    blurbs = json.loads(BLURBS.read_text())
    for b in blurbs:
        renamed = [TAG_MERGE_MAP.get(t, t) for t in b["topics"]]
        # dedupe while preserving order
        seen = set()
        deduped = []
        for t in renamed:
            if t not in seen:
                seen.add(t)
                deduped.append(t)
        b["topics"] = deduped
    BLURBS.write_text(json.dumps(blurbs, indent=2))
    print(f"Consolidated tags across {len(blurbs)} blurbs.")


if __name__ == "__main__":
    main()
