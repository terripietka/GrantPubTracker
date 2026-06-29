"""
GrantPubTracker
Step 2: Extract Author Affiliations

This script retrieves full PubMed XML records for publications identified in
Step 1 and extracts author-level affiliation information.

Why this step matters:
    PubMed search results can identify publications associated with an author,
    but publication attribution for grant reporting often requires a closer
    review of institutional affiliations. This script creates a detailed
    author-affiliation file that can be used to verify whether a publication
    should be attributed to the target center, institution, or research program.

Input:
    CSV file containing a PMID column.

Output:
    CSV file containing PMID, author name fields, and affiliation text.

Configuration:
    User-specific settings are read from a .env file. See .env.example.
"""

from __future__ import annotations

import os
from pathlib import Path
from time import sleep
from typing import Dict

import pandas as pd
from Bio import Entrez


# ---------------------------------------------------------------------
# Environment / configuration helpers
# ---------------------------------------------------------------------


def load_env_file(env_path: str | Path = ".env") -> None:
    """
    Load simple KEY=VALUE pairs from a .env file into environment variables.

    This avoids requiring python-dotenv for a small project, while still keeping
    user-specific paths and NCBI contact information out of the script.
    Existing environment variables are not overwritten.
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
        "input_csv": get_required_env("AFFILIATION_INPUT_CSV"),
        "output_csv": get_required_env("AFFILIATION_OUTPUT_CSV"),
        "ncbi_delay_seconds": float(os.getenv("NCBI_DELAY_SECONDS", "0.5")),
    }


# ---------------------------------------------------------------------
# PubMed affiliation extraction
# ---------------------------------------------------------------------


def extract_author_affiliations(pmid: str) -> list[dict[str, str]]:
    """
    Retrieve PubMed XML for one PMID and extract author affiliations.

    Parameters
    ----------
    pmid : str
        PubMed identifier for the publication.

    Returns
    -------
    list of dict
        One row per author, including PMID, author name fields, and affiliation
        text. If an author has multiple affiliations, they are joined into one
        semicolon-delimited field.
    """
    detailed_records: list[dict[str, str]] = []

    handle = Entrez.efetch(db="pubmed", id=str(pmid), rettype="xml")
    records = Entrez.read(handle)
    handle.close()

    article = records["PubmedArticle"][0]
    authors = article["MedlineCitation"]["Article"].get("AuthorList", [])

    for author in authors:
        # Group or consortium authors may not have individual name fields.
        if "LastName" not in author:
            continue

        affiliations = author.get("AffiliationInfo", [])
        affiliation_texts = [
            affiliation["Affiliation"]
            for affiliation in affiliations
            if "Affiliation" in affiliation
        ]

        detailed_records.append(
            {
                "PMID": str(pmid),
                "LastName": author.get("LastName", ""),
                "Initials": author.get("Initials", ""),
                "ForeName": author.get("ForeName", ""),
                "Affiliations": "; ".join(affiliation_texts)
                if affiliation_texts
                else "None",
            }
        )

    return detailed_records


def build_affiliation_file(
    input_csv: str | Path,
    output_csv: str | Path,
    ncbi_delay_seconds: float = 0.5,
) -> pd.DataFrame:
    """
    Extract author-affiliation records for all unique PMIDs in an input CSV.

    Parameters
    ----------
    input_csv : str or Path
        CSV file generated from the PubMed search workflow. Must contain a PMID
        column.
    output_csv : str or Path
        Destination path for the author-affiliation output file.
    ncbi_delay_seconds : float
        Pause between PubMed requests to respect NCBI servers.

    Returns
    -------
    pandas.DataFrame
        Detailed author-affiliation records.
    """
    publications_df = pd.read_csv(input_csv)

    if "PMID" not in publications_df.columns:
        raise ValueError("Input CSV must contain a 'PMID' column.")

    all_records: list[dict[str, str]] = []
    unique_pmids = publications_df["PMID"].dropna().astype(str).unique()

    for pmid in unique_pmids:
        print(f"Fetching author affiliations for PMID {pmid}")

        try:
            all_records.extend(extract_author_affiliations(pmid))
        except Exception as exc:
            print(f"Warning: Could not parse authors for PMID {pmid}: {exc}")

        sleep(ncbi_delay_seconds)

    detailed_df = pd.DataFrame(all_records)
    detailed_df.to_csv(output_csv, index=False)

    print(f"Saved detailed author affiliations for {len(detailed_df)} records.")
    print(f"Output file: {output_csv}")

    return detailed_df


# ---------------------------------------------------------------------
# Main script entry point
# ---------------------------------------------------------------------


def main() -> None:
    """
    Run the affiliation extraction workflow.
    """
    config = get_config()
    Entrez.email = str(config["entrez_email"])

    build_affiliation_file(
        input_csv=str(config["input_csv"]),
        output_csv=str(config["output_csv"]),
        ncbi_delay_seconds=float(config["ncbi_delay_seconds"]),
    )


if __name__ == "__main__":
    main()
