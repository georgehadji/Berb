---
type: object
cluster: literature
universe: live
status: verified
verified: 2026-10-22 @ fb7bd25
entity: berb/literature/__init__.py
---

# berb.literature public API and the modules behind it

`from berb.literature import ...` is a supported contract (decided 2026-09-02, root `CLAUDE.md`). `scripts/check_reachability.py` treats the modules behind `__all__` as entry points; `tests/test_public_api_contract.py` asserts every name resolves. Exports are lazy (PEP 562), so importing the package does not load arxiv, httpx or the LLM client (`__init__.py:9-11`, `98`).

## Why this shape

Much of `__all__` is not used by the pipeline. It is a published surface, so internally unused code is not reported dead. That makes "exported" and "wired" different questions.

## Which modules are actually wired

| Module | Wired by | Evidence |
|---|---|---|
| `search`, `models`, `verify`, `retraction`, `paper_mill`, `pdf_ingestor`, `novelty`, `cache`, `_rate_limiter` | pipeline stages | see the other cards |
| `perplexity_search` | lazily by `search.py:379` | |
| `arxiv_client`, `semantic_scholar`, `openalex_client` | `search.py`, `trends/feeds.py` | |
| `zotero_integration` | `commands/claude_scholar.py` | importer only; CLI wiring not checked |
| `citation_classifier`, `evidence_map`, `citation_graph`, `section_analysis`, `structured_notes`, `recency_filter`, `multimodal_search` | nothing in `berb/` outside `literature/` | no importer found by grep of `from berb.literature...`; live only by contract |
| `fs_processor`, `fs_query` | `pipeline/optimization_integration/literature_integration.py` (package parked, `.reachability-allowlist:104`) and `benchmarks/performance_suite.py` | |
| `grey_search`, `searxng_client`, `full_text`, `specification`, `trends` | no one | parked, revisit 2026-12-01, strike 1 (`.reachability-allowlist:132-136`) |

## Collisions inside the contract

- Two `Paper` classes (`models.Paper`, `citation_graph.Paper`); the second is exported as `CitationGraphPaper` (`__init__.py:61`).
- Two `PaperCitationProfile` classes (`citation_classifier`, `section_analysis`); the second is exported as `SectionPaperCitationProfile` (`__init__.py:71`).
- `berb.writing.citation_engine` is parked separately (`.reachability-allowlist:110`); `literature/models.py` is the wired BibTeX path.

## If you change this

- **Hits:** external importers; `tests/test_public_api_contract.py`; the reachability ratchet.
- **Hits:** deleting a module in the "contract only" row needs a product decision, not just a green gate.
- **Does not hit:** pipeline behaviour for any module outside the first rows.

## See

- Source: `berb/literature/__init__.py`, `.reachability-allowlist`
