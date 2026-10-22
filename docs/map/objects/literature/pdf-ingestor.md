---
type: object
cluster: literature
universe: live
status: verified
verified: 2026-10-22 @ fb7bd25
entity: berb/literature/pdf_ingestor.py
---

# PDF ingestion (user-uploaded papers)

`ingest_pdfs(paths, llm)` (`pdf_ingestor.py:371`) turns uploaded PDFs into candidate rows for stage 4 (`_literature.py:508-533`). Uploaded papers are "tier 0": always included.

## Why this shape

Three tiers so a missing LLM does not block ingestion: PDF metadata, then text heuristics for title, author and abstract, then LLM extraction only if title or abstract is still empty; last resort the filename as the title (`pdf_ingestor.py:300-332`). Each PDF is isolated: a bad file is logged and skipped.

## Shape

- Row keys match `candidates.jsonl`; `source: "upload"`, `year: 0`, `venue: "Uploaded PDF"`, `is_uploaded: true`, `url` is the local path (`pdf_ingestor.py:347-363`).
- `cite_key` is surname plus the CURRENT year plus first title word, not the paper's year (`pdf_ingestor.py:343-345`), so it differs from the `Paper.cite_key` rule ([[paper-model]]).
- Because `year` is 0 and there is no citation count, an uploaded paper is invisible to year filters and ranks last wherever `citation_count` matters.
- Fed from `config.research.uploaded_file_paths`; `berb run` and `berb literature` both accept uploads (`cli.py:276-279`, `980`).

## Connected to

- **joins:** [[literature-stages]] (stage 4 adds rows, skipping a title already present), `berb/web` PDF extraction (separate code, `tests/test_web_pdf_extractor.py`).
- **looks-like-but-is-not:** `full_text.py` (parked).

## If you change this

- **Hits:** stage 4 row format; `tests/test_berb_pdf_ingestor.py`.
- **Does not hit:** the BibTeX file: uploaded rows only reach `references.bib` through the stage 4 fallback block, which skips placeholders but not uploads (`_literature.py:668-714`); the interplay when real search also succeeded was not traced.

## See

- Source: `berb/literature/pdf_ingestor.py`
