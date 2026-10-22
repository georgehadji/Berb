---
type: object
cluster: literature
universe: live
status: verified
verified: 2026-10-22 @ fb7bd25
entity: berb/literature/novelty.py
---

# Novelty check

`check_novelty(topic, hypotheses_text, ...)` (`novelty.py:270`) scores how much the generated hypotheses overlap existing work. Called at the end of stage 8 `HYPOTHESIS_GEN` (`_synthesis.py:473-497`); output `novelty_report.json`.

## Why this shape

Non-blocking: the stage wraps it in `try/except` and only logs (`_synthesis.py:495-496`). The report advises (`proceed`, `differentiate`, `abort`, or `proceed_with_caution`), but a grep of `berb/` finds no reader of `novelty_report.json` or of its `recommendation`: it is written, logged, and listed by `cli.py:1030`. Even `abort` changes nothing.

## Shape

- Searches again through [[search-cascade]] (`search_papers_multi_query`, 15 per query) using queries built from topic and hypotheses, then keyword-scores titles and abstracts; threshold 0.25 (`novelty.py:276-347`). Also scores the already-collected `candidates.jsonl` rows.
- `search_coverage`: `insufficient` (0 retrieved and nothing seen), `partial` (<5), `full`. Insufficient coverage with no hits gives `assessment: insufficient_data` instead of a misleading perfect score (`novelty.py:388-407`).
- Optional Perplexity grounding: if it says "not novel" with confidence 0.6 or more, a `proceed` is downgraded to `differentiate` (`novelty.py:409-427`).

## Connected to

- **joins:** [[search-cascade]], [[literature-stages]] (candidates input), stage 8 in `_synthesis.py`.
- **looks-like-but-is-not:** `integrity/` claim checks; this is topic-level overlap, not claim verification.

## If you change this

- **Hits:** `tests/test_berb_novelty.py`; the log line at `_synthesis.py:491-495` reads `novelty_score`, `assessment`, `recommendation`. No other reader of the file exists today.
- **Does not hit:** stage success; a failure here never fails stage 8.

## See

- Source: `berb/literature/novelty.py`
