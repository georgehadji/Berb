---
type: object
cluster: literature
universe: live
status: verified
verified: 2026-10-22 @ fb7bd25
entity: berb/literature/retraction.py
---

# Retraction and paper-mill screens

Two integrity checks on cited or shortlisted papers: retraction / expression-of-concern lookup (`retraction.py`) and tortured-phrase screening (`paper_mill.py`). Both come from `tasks/ars_integration_plan.md` (W2, W4).

## Why this shape

Advisory early, enforcing late. Stage 5 runs both on the shortlist and only writes findings files; nothing can fail the stage (`_literature.py:889-948`). Stage 23 re-runs the retraction lookup on citations with a resolved DOI and can fail the run, depending on `config.integrity.mode`: `draft` warns only, `submission` fails on critical issues, `strict` fails closed (`config.py:354-363`, `_citations.py:492-536`). Findings can be acknowledged with `integrity.retraction_ack`.

## Shape

- Retraction: CrossRef first, OpenAlex second (`retraction.py:51-52`), 20 s timeout, results cached 30 days (`retraction.py:42`). An empty DOI returns `UNKNOWN` with no network call, so arXiv-only papers are never screened.
- Paper mill: phrase list `berb/data/tortured_phrases.yaml`, size cap 1 MB, loaded once per stage (`paper_mill.py:29-36`, `77-93`). A hit is a risk marker, severity advisory.
- Artifacts: `retraction_findings.json`, `paper_mill_findings.json` at stage 5; `retraction_findings.json` and `anchor_findings.json` at stage 23.

## Connected to

- **joins:** [[literature-stages]] (stage 5), [[citation-verify]] (stage 23 DOI source is `matched_paper.doi`), `integrity/` (anchors, `Finding`), `config.integrity`.
- **looks-like-but-is-not:** `integrity/eval/hidden_eval.py` (parked).

## If you change this

- **Hits:** stage 23 can newly fail runs when severity or mode mapping changes (`_integrity_gates`); tests `tests/test_literature_retraction.py`, `test_literature_paper_mill.py`, `test_stage_citation_verify_retraction.py`.
- **Hits:** editing the phrase file changes stage 5 outputs only.
- **Does not hit:** verification verdicts or search.

## See

- Source: `berb/literature/retraction.py`, `berb/literature/paper_mill.py`
