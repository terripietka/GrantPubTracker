# GrantPubTracker

Automating publication discovery, affiliation verification, and citation reporting for NIH-funded research programs.

---

## Overview

GrantPubTracker is an open-source Python application that automates the collection, validation, and formatting of publication data from PubMed for research administration and grant reporting.

Many NIH program center grants, core facilities, and shared research resources are required to document publications that resulted from grant-supported activities. While PubMed provides excellent search capabilities, identifying publications across dozens of investigators, verifying institutional affiliations, eliminating duplicates, and formatting citations for annual progress reports is often a manual and time-consuming process.

GrantPubTracker streamlines this workflow by retrieving publication metadata from the PubMed Entrez API, extracting detailed author affiliations, enriching records with PubMed Central identifiers (PMCIDs), and generating consistently formatted citation reports suitable for NIH reporting.

Although originally developed to support a large NIH-funded research center, the workflow has been generalized for use by research administrators, core facilities, shared instrumentation grants, and academic research programs.

---

## Why I Built This

One of the administrative responsibilities of many NIH-funded centers is documenting publications that benefited from grant-supported resources. Our center supported investigators across multiple departments and collaborating institutions, making publication tracking increasingly difficult as the number of supported researchers grew.

Searching PubMed individually for every investigator often produced ambiguous results. Author names are not unique, affiliations change over time, and duplicate publications frequently appeared across multiple searches.

To reduce the manual effort required for annual progress reports and competitive renewals, I developed an automated workflow that retrieves publications, verifies institutional affiliations, and produces consistently formatted citation reports.

---

## Features

- Search PubMed for publications by investigator
- Retrieve publication metadata using the NCBI Entrez API
- Extract detailed author and institutional affiliation information
- Validate author affiliations to improve publication attribution
- Remove duplicate publications across multiple investigators
- Retrieve PubMed Central (PMCID) identifiers
- Generate NIH-style formatted citations
- Export publication datasets for additional review and analysis
- Configurable through environment variables (`.env`)
- Modular workflow designed for future expansion

---

## Workflow

```text
Investigator Roster
        │
        ▼
Search PubMed
        │
        ▼
Retrieve Publication Metadata
        │
        ▼
Extract Author Affiliations
        │
        ▼
Verify Institutional Matches
        │
        ▼
Retrieve PMCIDs
        │
        ▼
Generate Formatted Citation Report
```

---

## Repository Structure

```text
GrantPubTracker/

├── 01_search_pubmed.py
├── 02_extract_affiliations.py
├── 03_format_citations.py
├── .env.example
├── requirements.txt
├── README.md
└── LICENSE
```

---

## Technologies

- Python
- pandas
- Biopython (Entrez API)
- XML parsing
- PubMed / NCBI Entrez
- Environment-based configuration (.env)

---

## Installation

Clone the repository:

```bash
git clone https://github.com/<your-username>/GrantPubTracker.git
cd GrantPubTracker
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Copy the example configuration:

```bash
cp .env.example .env
```

Edit `.env` to specify:

- NCBI email address
- Input and output file locations
- Affiliation matching criteria
- Optional processing parameters

Run each workflow step in sequence:

```bash
python 01_search_pubmed.py
python 02_extract_affiliations.py
python 03_format_citations.py
```

---

## Example Use Cases

- NIH Program Center Grants
- Shared Instrumentation Grants
- Core Facilities
- Clinical and Translational Science Awards (CTSAs)
- Annual Progress Reports
- Competitive Grant Renewals
- Institutional Bibliometric Reporting

---

## Planned Enhancements

Future development will focus on making GrantPubTracker easier to use by research administrators without requiring Python experience.

Planned features include:

- Standalone desktop application
- Optional graphical user interface (GUI)
- Optional web-based dashboard for institutional deployment
- Configurable institution and affiliation matching
- Additional citation style support
- Export directly to Microsoft Word, Excel, and PDF
- Improved duplicate detection
- ORCID integration
- NIH RePORTER integration
- Docker deployment

---

## Contributing

Contributions, suggestions, and feature requests are welcome. If you have ideas for improving publication attribution workflows or supporting additional reporting formats, please feel free to open an issue or submit a pull request.

---

## Disclaimer

This project is an independent open-source tool and is **not** affiliated with or endorsed by the National Institutes of Health (NIH), the National Library of Medicine (NLM), the National Center for Biotechnology Information (NCBI), or any specific research institution.

Publication data are retrieved using the NCBI Entrez Programming Utilities (E-utilities). Users are responsible for complying with the current NCBI usage policies and ensuring that publication attribution is reviewed before use in official grant reporting.

---

## Copyright

Copyright © 2026 Terri Pietka

Released under the MIT License. See the `LICENSE` file for details.
