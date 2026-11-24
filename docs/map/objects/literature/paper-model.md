---
type: object
cluster: literature
universe: live
status: verified
verified: 2026-10-22 @ fb7bd25
entity: berb/literature/models.py
---

# Paper and Author

Frozen dataclasses for one search hit: `Paper` (`models.py:33`) and `Author` (`models.py:16`). Carries ids, venue, citation count, `source`, and builds `cite_key` and BibTeX.

## Why this shape

One union record for all sources, so search, dedup, BibTeX and verification share a type. Pipeline artifacts are plain dicts: stage 4 turns a `Paper` into JSON with `to_dict()` and BibTeX with `to_bibtex()` (`_literature.py:478-481`); later stages read `candidates.jsonl`, never `Paper`.

## Shape

- Fields: `paper_id`, `title`, `authors`, `year`, `abstract`, `venue`, `citation_count`, `doi`, `arxiv_id`, `url`, `source`, `_bibtex_override` (`models.py:33-54`).
- `cite_key` is `lastname<year><keyword>`: ASCII-folded first-author surname, year or `0000`, first title word over 3 letters that is not a stopword; `anon` if no authors (`models.py:57-75`). Two papers can collide on the same key; the collision handling is not carded here.
- `source` is a free string; the comment lists only `semantic_scholar` and `arxiv`, but `openalex`, `upload`, `seminal_library` and Perplexity also appear in the pipeline.

## Connected to

- **owns:** the cite-key rule that BibTeX, the paper text and [[citation-verify]] all rely on.
- **joins:** [[search-cascade]], [[citation-verify]] (`CitationResult.matched_paper`), `web/scholar.py` (`Paper`, `Author`), `benchmarks/performance_suite.py`.
- **looks-like-but-is-not:** `citation_graph.Paper`, a second, different `Paper` class; the public API exports it as `CitationGraphPaper` to avoid the clash ([[public-api]]). Also `PaperCitationProfile` exists in two modules; one is exported as `SectionPaperCitationProfile`.

## If you change this

- **Hits:** `cite_key` format: every `references.bib`, `\cite{}` key and the per-stage artifacts of existing runs; `to_dict` keys feed `candidates.jsonl` consumers; `search._dicts_to_papers` rebuilds `Paper` from cache and must accept the same fields (`search.py:107-140`).
- **Hits:** adding a field: cache round trip (`asdict` out, manual rebuild in) drops it silently unless `_dicts_to_papers` is updated.
- **Does not hit:** dict rows that never pass through `Paper` (uploaded PDFs, seminal library, web scholar entries).

## See

- Source: `berb/literature/models.py`
