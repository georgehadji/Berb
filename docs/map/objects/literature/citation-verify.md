---
type: object
cluster: literature
universe: live
status: verified
verified: 2026-10-22 @ fb7bd25
entity: berb/literature/verify.py
---

# Citation verification (`verify_citations`)

Checks every BibTeX entry against real APIs and labels it `verified`, `suspicious`, `hallucinated` or `skipped` (`verify.py:44-117`). Three call sites in one run: stage 17, stage 22, stage 23.

## Why this shape

LLM-written papers invent references; the pipeline must not ship them. Status comes from title similarity: at least 0.80 verified, 0.50 to 0.80 suspicious, below 0.50 or not found hallucinated (`verify.py:12-14`). Layers run in this order: DOI via CrossRef/DataCite (final), OpenAlex title search (a match is final; a miss is provisional), arXiv id, Semantic Scholar title search. Network failure returns `None` and falls through.

## Call sites

| Stage | What it does with the report |
|---|---|
| 17 `PAPER_DRAFT` | Pre-verify; drops hallucinated entries from the set of citable keys the draft prompt may use (`_paper_writing.py:2167-2200`). Does not pass `s2_api_key`. |
| 22 `EXPORT_PUBLISH` | Any hallucinated entry fails export with `E22_EXPORT_FAIL`; a verifier exception lets export proceed with no gate (`_export.py:993-1025`). |
| 23 `CITATION_VERIFY` | Full report; retraction and anchor gating by `config.integrity.mode`; LLM relevance score, drop below 0.5 and cap at 60; fall back to the original bib if over 50% would be stripped; prune uncited entries (`_citations.py:424-725`). |

## Fixed 2026-10-22 (uncommitted): an OpenAlex miss was final

`verify_by_openalex` returns `HALLUCINATED` when OpenAlex has no or poor matches, and the old caller treated any non-`None` result as final, so the arXiv-id and Semantic Scholar layers ran only if OpenAlex itself failed. A real preprint with a valid `eprint` but no OpenAlex hit was labelled hallucinated, cached, and failed stage 22. Now an OpenAlex `HALLUCINATED` is held as `openalex_miss` and the chain continues; a positive from the arXiv-id or S2 layer overrides it, and if none answers the miss stands (`verify.py:778-800`, `821-824`). A DOI verdict is still final. Tests: `tests/test_literature_failure_signals.py` (4 verify tests).

Cost: every OpenAlex miss now also costs one Semantic Scholar title search (about 1 s) when there is no `eprint`.

Cache caveat: verdicts cached before this fix persist (no TTL). Delete `~/.cache/berb/citation_verify/` to clear false `hallucinated` entries from earlier runs.

## Other facts

- Cache: `~/.cache/berb/citation_verify/`, key `sha256(title)[:16]`, no TTL, every non-`SKIPPED` result stored, including `hallucinated` (`verify.py:535-572`, `842-844`). Keyed by title only, per user, not per run. `cache.py` has a `citation_verify` TTL entry (`cache.py:32`) that nothing reads.
- Global 5 minute budget; the remainder is marked `SKIPPED` (`verify.py:691-718`).
- `berb verify-citations` (CLI) does NOT use this module: `cmd_verify_citations` uses `pipeline/citation_verification.CitationVerifier` on DOIs found by regex (`commands/claude_scholar.py:496-530`).

## Connected to

- **owns:** verdict rules and the verification cache.
- **joins:** [[paper-model]] (`matched_paper`), [[advisory-screens]] (stage 23 retraction gate), [[literature-stages]] (`references.bib` source), `pipeline/hallucination_detector.py` (documents this as the earlier pass), `evidence`/anchors in `integrity/`.
- **looks-like-but-is-not:** `pipeline/citation_verification.py` (CLI verifier).

## If you change this

- **Hits:** stages 17, 22, 23 behaviour and run failure; tests `tests/test_berb_citation_verify.py`, `test_stage_citation_verify_anchors.py`, `test_stage_citation_verify_retraction.py`.
- **Hits:** changing a verdict rule leaves old results in the cache; clear `~/.cache/berb/citation_verify` or stale verdicts persist.
- **Does not hit:** search ([[search-cascade]]).

## See

- Source: `berb/literature/verify.py`, `berb/pipeline/stage_impls/_citations.py`
