"""
Search PubMed for publications by investigator and verify institutional affiliation.

This script was converted from the original PubMed search Jupyter notebook.
It reads an investigator roster CSV, searches PubMed by author and publication
start date, checks whether the target affiliation appears in the PubMed record,
deduplicates publications by PMID, and exports a CSV of matching results.

Expected input CSV columns:
    - author: author name in PubMed format, preferably "Last, Initials"
    - start_date: publication search start date in MM/DD/YYYY format

Outputs:
    - pubmed_results_grouped_with_MeSH2.csv
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from time import sleep
from typing import Iterable

import pandas as pd
from Bio import Entrez, Medline


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

ENTREZ_EMAIL = "tpietka@wustl.edu"

INPUT_CSV = Path(r"c:\Users\Terri\Documents\PubMed Search\author2.csv")
OUTPUT_CSV = Path(r"c:\Users\Terri\Documents\PubMed Search\pubmed_results_grouped_with_MeSH2.csv")

END_DATE = "2025/04/01"
TARGET_AFFILIATION = "Washington University"
MESH_TERMS = ["Obesity", "Nutrition", "Diet"]

PUBMED_RETMAX = 1000
REQUEST_SLEEP_SECONDS = 1.0


# -----------------------------------------------------------------------------
# PubMed helpers
# -----------------------------------------------------------------------------

def search_pubmed(author: str, start_date: str, end_date: str) -> list[str]:
    """Search PubMed for an author between two publication dates."""
    query = (
        f'{author}[Author] AND '
        f'("{start_date}"[Date - Publication] : "{end_date}"[Date - Publication])'
    )
    print(f"Running query: {query}")

    with Entrez.esearch(db="pubmed", term=query, retmax=PUBMED_RETMAX) as handle:
        record = Entrez.read(handle)

    return record["IdList"]


def fetch_details(pubmed_ids: Iterable[str]) -> list[dict]:
    """Fetch MEDLINE records for a list of PubMed IDs."""
    pubmed_ids = list(pubmed_ids)
    if not pubmed_ids:
        return []

    ids = ",".join(pubmed_ids)
    with Entrez.efetch(db="pubmed", id=ids, rettype="medline", retmode="text") as handle:
        records = list(Medline.parse(handle))

    return records


# -----------------------------------------------------------------------------
# Matching and parsing helpers
# -----------------------------------------------------------------------------

def format_pubmed_date(date_value: str) -> str:
    """Convert MM/DD/YYYY dates to PubMed YYYY/MM/DD format."""
    return datetime.strptime(str(date_value), "%m/%d/%Y").strftime("%Y/%m/%d")


def parse_author_name(author: str) -> tuple[str, str]:
    """
    Parse an author name into last name and initials.

    Preferred input format is "Last, Initials". A fallback is included for
    space-delimited names.
    """
    author = str(author).strip()

    if "," in author:
        author_last, author_initial = [part.strip().lower() for part in author.split(",", 1)]
    else:
        parts = author.split()
        author_last = " ".join(parts[:-1]).lower()
        author_initial = parts[-1].lower() if parts else ""

    return author_last, author_initial


def author_matches_record(author: str, record_authors: list[str]) -> bool:
    """Return True when an input author loosely matches a PubMed author list."""
    author_last, author_initial = parse_author_name(author)
    normalized_record_authors = [a.lower().replace(".", "") for a in record_authors]

    return any(
        a.startswith(f"{author_last} {author_initial}")
        for a in normalized_record_authors
    )


def get_affiliations(record: dict) -> str:
    """Extract and normalize affiliations from a MEDLINE record."""
    affiliations = record.get("AD", "")
    if isinstance(affiliations, list):
        affiliations = " ".join(affiliations)
    return str(affiliations)


def get_matched_mesh_terms(record_mesh_terms: list[str], mesh_terms: list[str]) -> list[str]:
    """Return configured MeSH terms that appear in the PubMed record."""
    return [
        term
        for term in mesh_terms
        if any(term.lower() in mesh_term.lower() for mesh_term in record_mesh_terms)
    ]


# -----------------------------------------------------------------------------
# Main workflow
# -----------------------------------------------------------------------------

def run_pubmed_search(
    input_csv: Path,
    output_csv: Path,
    end_date: str,
    target_affiliation: str,
    mesh_terms: list[str],
) -> pd.DataFrame:
    """Run the full PubMed search and export a deduplicated results CSV."""
    Entrez.email = ENTREZ_EMAIL

    author_df = pd.read_csv(input_csv)
    pmid_to_result: dict[str, dict] = {}

    for _, row in author_df.iterrows():
        author = row["author"]
        start_date = format_pubmed_date(row["start_date"])

        pubmed_ids = search_pubmed(author, start_date, end_date)
        sleep(REQUEST_SLEEP_SECONDS)

        records = fetch_details(pubmed_ids)

        for record in records:
            affiliations = get_affiliations(record)
            pmid = record.get("PMID", "")
            record_authors = record.get("AU", [])

            is_author_match = author_matches_record(author, record_authors)
            is_affiliation_match = target_affiliation.lower() in affiliations.lower()

            if is_author_match and is_affiliation_match:
                record_mesh_terms = record.get("MH", [])
                matched_mesh = get_matched_mesh_terms(record_mesh_terms, mesh_terms)

                if pmid not in pmid_to_result:
                    pmid_to_result[pmid] = {
                        "Pub Date": record.get("DP", ""),
                        "PMID": pmid,
                        "Matched Authors": [author],
                        "Matched MeSH Terms": matched_mesh,
                        "All MeSH Terms": record_mesh_terms if record_mesh_terms else [],
                        "Journal": record.get("JT", ""),
                        "Issue Info": record.get("SO", ""),
                        "Publication Type": "; ".join(record.get("PT", [])),
                        "Title": record.get("TI", ""),
                        "Authors": "; ".join(record_authors),
                        # "Abstract": record.get("AB", ""),
                    }
                else:
                    if author not in pmid_to_result[pmid]["Matched Authors"]:
                        pmid_to_result[pmid]["Matched Authors"].append(author)

                    for term in matched_mesh:
                        if term not in pmid_to_result[pmid]["Matched MeSH Terms"]:
                            pmid_to_result[pmid]["Matched MeSH Terms"].append(term)

        sleep(REQUEST_SLEEP_SECONDS)

    results_df = pd.DataFrame([
        {
            **result,
            "Matched Authors": "; ".join(result["Matched Authors"]),
            "Matched MeSH Terms": "; ".join(result["Matched MeSH Terms"]),
            "All MeSH Terms": "; ".join(result["All MeSH Terms"]),
        }
        for result in pmid_to_result.values()
    ])

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_csv, index=False)

    print(f"Saved {len(results_df)} unique results to {output_csv}")
    return results_df


def main() -> None:
    run_pubmed_search(
        input_csv=INPUT_CSV,
        output_csv=OUTPUT_CSV,
        end_date=END_DATE,
        target_affiliation=TARGET_AFFILIATION,
        mesh_terms=MESH_TERMS,
    )


if __name__ == "__main__":
    main()
