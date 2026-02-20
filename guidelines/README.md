# Guidelines Directory

Place clinical guideline documents here before running `setup_rag.py`.

## Supported formats
- `.pdf` — Requires `pymupdf` (`pip install pymupdf`)
- `.txt` — Plain text
- `.md` — Markdown

## Recommended sources (freely available)
- WHO Essential Medicines List: https://www.who.int/publications/i/item/WHO-MHP-HPS-EML-2023.02
- WHO Integrated Management of Adolescent and Adult Illness (IMAI): https://www.who.int
- NICE Clinical Knowledge Summaries: https://cks.nice.org.uk
- CDC Clinical Guidelines: https://www.cdc.gov/guidelines
- National TB Programme guidelines (country-specific)
- GOLD COPD Guidelines: https://goldcopd.org
- JNC Hypertension Guidelines

## After adding files
```bash
python scripts/setup_rag.py
```

The pipeline will chunk, embed, and index all documents automatically.
Indexing takes approximately 1–5 minutes depending on document volume.

## Important
All documents must be de-identified and appropriately licensed for local use.
Do not place patient records in this directory.
