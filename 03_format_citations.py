"""
GrantPubTracker
Step 3: Format Publication Citations

This script enriches verified publication records by retrieving PubMed Central
identifiers (PMCIDs) and formatting citations for grant reporting.

Why this step matters:
    NIH progress reports and center grant renewals often require publication
    lists with PubMed identifiers and, when available, PubMed Central IDs. This
    script converts verified publication records into a consistent citation
    format suitable for reporting and administrative review.

Input:
    CSV file containing verified publication records with PMID, Authors, Title,
    and Issue Info columns.

Output:
    CSV file containing the original records plus PMCID and Formatted Citation
    columns.

Configuration:
    User-specific settings are read from a .env file. See .env.example.
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
from Bio import Entrez


# ---------------------------------------------------------------------
# Environment / configuration helpers
# ---------------------------------------------------------------------


def load_env_file(env_path: str | Path = ".env") -> None:
    """
    Load simple KEY=VALUE pairs from a .env file into environment variables.

    Existing environment variables are not overwritten. This lets users provide
    local file paths and an NCBI Entrez email address without editing the source
    code directly.
    """
    env_path = Path(env_path)
    if not env_path.exists():
        return

    with env_path.open("r", encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


def get_required_env(name: str) -> str:
    """
    Return a required environment variable or raise a helpful error.
    """
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Add it to your .env file or set it in your shell."
        )
    return value


def get_config() -> Dict[str, str | float]:
    """
    Read script configuration from environment variables.
    """
    load_env_file()

    return {
        "entrez_email": get_required_env("ENTREZ_EMAIL"),
        "input_csv": get_required_env("CITATION_INPUT_CSV"),
        "output_csv": get_required_env("CITATION_OUTPUT_CSV"),
        "ncbi_delay_seconds": float(os.getenv("NCBI_DELAY_SECONDS", "0.5")),
    }


# ---------------------------------------------------------------------
# PubMed Central lookup and citation formatting
# ---------------------------------------------------------------------


def fetch_pmcid(pmid: str) -> Optional[str]:
    """
    Retrieve the PubMed Central identifier associated with a PMID.

    Parameters
    ----------
    pmid : str
        PubMed identifier.

    Returns
    -------
    str or None
        PMCID if the article has a PubMed Central record; otherwise None.
    """
    try:
        handle = Entrez.elink(
            dbfrom="pubmed",
            db="pmc",
            id=str(pmid),
            linkname="pubmed_pmc",
        )
        records = Entrez.read(handle)
        handle.close()

        linksets = records[0].get("LinkSetDb", [])
        for linkset in linksets:
            if linkset.get("DbTo") == "pmc" and linkset.get("Link"):
                return f"PMC{linkset['Link'][0]['Id']}"

        return None
    except Exception as exc:
        print(f"Error fetching PMCID for PMID {pmid}: {exc}")
        return None


def clean_issue_info(issue_info: object) -> str:
    """
    Clean journal issue text before citation formatting.

    PubMed issue strings may include DOI text, early-publication notes, or other
    metadata that should not always appear in the final grant-report citation.
    This function keeps the journal/year/volume/page portion when possible.
    """
    issue_text = str(issue_info).strip()
    match = re.search(r"(.*?)(?:doi:|DOI:|Epub|epub)", issue_text)

    if match:
        return match.group(1).strip().rstrip(".")

    return issue_text.rstrip(".")


def format_citation(row: pd.Series) -> str:
    """
    Create a formatted publication citation from one publication record.

    Parameters
    ----------
    row : pandas.Series
        Publication metadata row containing Authors, Title, Issue Info, PMID,
        and optionally PMCID.

    Returns
    -------
    str
        Formatted citation string.
    """
    authors = str(row.get("Authors", "")).replace(";", ",").strip()
    title = str(row.get("Title", "")).strip().rstrip(".")
    journal_info = clean_issue_info(row.get("Issue Info", ""))
    pmid = str(row.get("PMID", "")).strip()
    pmcid = row.get("PMCID", "")

    citation = f"{authors}. {title}. {journal_info}."
    citation += f" PubMed PMID: {pmid};"

    if pd.notna(pmcid) and str(pmcid).strip():
        citation += f" PMCID: {str(pmcid).strip()}."

    return citation


def add_pmcids(
    publications_df: pd.DataFrame,
    ncbi_delay_seconds: float = 0.5,
) -> pd.DataFrame:
    """
    Add PMCID values to a publication DataFrame using PMID lookup.
    """
    publications_df = publications_df.copy()
    publications_df["PMID"] = publications_df["PMID"].astype(str)

    pmid_to_pmcid: dict[str, Optional[str]] = {}
    for pmid in publications_df["PMID"].dropna().unique():
        pmcid = fetch_pmcid(pmid)
        pmid_to_pmcid[pmid] = pmcid
        print(f"PMID {pmid} -> PMCID {pmcid}")
        time.sleep(ncbi_delay_seconds)

    publications_df["PMCID"] = publications_df["PMID"].map(pmid_to_pmcid)
    return publications_df


def build_citation_file(
    input_csv: str | Path,
    output_csv: str | Path,
    ncbi_delay_seconds: float = 0.5,
) -> pd.DataFrame:
    """
    Enrich verified publication records and export formatted citations.
    """
    publications_df = pd.read_csv(input_csv)

    required_columns = {"PMID", "Authors", "Title", "Issue Info"}
    missing_columns = required_columns.difference(publications_df.columns)
    if missing_columns:
        raise ValueError(
            "Input CSV is missing required column(s): "
            + ", ".join(sorted(missing_columns))
        )

    publications_df = add_pmcids(
        publications_df,
        ncbi_delay_seconds=ncbi_delay_seconds,
    )
    publications_df["Formatted Citation"] = publications_df.apply(
        format_citation,
        axis=1,
    )
    publications_df.to_csv(output_csv, index=False)

    print(f"Done! Saved formatted citations to {output_csv}")
    return publications_df


# ---------------------------------------------------------------------
# Main script entry point
# ---------------------------------------------------------------------


def main() -> None:
    """
    Run the citation formatting workflow.
    """
    config = get_config()
    Entrez.email = str(config["entrez_email"])

    build_citation_file(
        input_csv=str(config["input_csv"]),
        output_csv=str(config["output_csv"]),
        ncbi_delay_seconds=float(config["ncbi_delay_seconds"]),
    )


if __name__ == "__main__":
    main()
