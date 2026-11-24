---
type: object
cluster: literature
universe: live
status: verified
verified: 2026-10-22 @ fb7bd25
entity: berb/pipeline/stage_impls/_literature.py
---

# Literature stages (3-6): strategy, collect, screen, extract

Stages `SEARCH_STRATEGY`, `LITERATURE_COLLECT`, `LITERATURE_SCREEN`, `KNOWLEDGE_EXTRACT` in one module. Chain: `problem_tree.md` to `search_plan.yaml` + `queries.json` to `candidates.jsonl` (+ `references.bib`, `search_meta.json`) to `shortlist.jsonl` to `cards/` (contracts `contracts.py:240-285`).

Depth: stages 4 and 5 were read in full. Stages 3 and 6 were checked for contracts only.

## Stage 4 candidate ladder (`_literature.py:413-744`)

1. Academic search, up to 3 expansion rounds (`_MAX_EXPANSION_ROUNDS`), 40 results per query. A round that adds fewer than 3 new papers stops expansion (`_literature.py:98-99`, `490-498`). Uses [[search-cascade]]. `year_min` defaults to 2020 from `queries.json`.
2. Uploaded PDFs, always included ([[pdf-ingestor]]).
3. Seminal-paper library via `berb.data.load_seminal_papers`.
4. LLM-invented candidates, only if the list is still empty.
5. Optional web search augmentation (`config.web_search.enabled`).
6. Placeholder rows (`is_placeholder: true`, `example.org` URLs, at least 20) if still empty.

`search_meta.json` records `real_search` (True only if the academic search returned papers); it is what the next stage checks.

## Stage 5 screen (`_literature.py:753-955`)

- Fails immediately when `search_meta.real_search is False` (P0-04): a candidate corpus that was LLM-generated or placeholder is refused (`_literature.py:784-797`).
- Keyword pre-filter, at least 1 topic-keyword hit; if it drops everything it is skipped (`_literature.py:802-825`).
- LLM relevance/quality screen. Fewer than 15 returned, or no LLM: the shortlist is padded from candidates with made-up scores (`relevance_score` 0.75 minus 0.02 per row, reason "Template screened entry") (`_literature.py:855-885`). Those scores are not measurements.
- Advisory retraction and tortured-phrase screens run on the shortlist ([[advisory-screens]]); they never fail the stage.
- Stage 5 is a gate stage, so it blocks for approval unless auto-approve is set ([[stage]]).

## Known doc/behaviour mismatch

The P0-04 comment says the failure rolls back to `LITERATURE_COLLECT` via `GATE_ROLLBACK` (`_literature.py:782-783`). That table is only used by `advance()` ([[stage]]). In the runner a FAILED stage that is not noncritical ends the run (`runner.py:508-512`), so the run stops at stage 5 rather than retrying collection.

## Connected to

- **owns:** the candidate ladder and the `real_search` flag.
- **joins:** [[search-cascade]], [[pdf-ingestor]], [[advisory-screens]], [[executor]] (output validation), `berb/data` seminal library, `web/agent.py`.
- **looks-like-but-is-not:** `pipeline/optimization_integration/literature_integration.py` (parked).

## If you change this

- **Hits:** `candidates.jsonl` rows are read by stage 5, by `novelty` (`_synthesis.py:473`), and by stage 17 for citable keys (`_paper_writing.py:2185-2200`); changing row keys breaks all three.
- **Hits:** `references.bib` is the source for [[citation-verify]] in stages 17, 22 and 23.
- **Does not hit:** stage 6 consumers beyond `cards/` (not read).

## See

- Source: `berb/pipeline/stage_impls/_literature.py`; tests `tests/test_literature_expansion.py`, `tests/test_berb_literature.py`
