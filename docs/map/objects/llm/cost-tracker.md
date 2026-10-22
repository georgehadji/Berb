---
type: object
cluster: llm
universe: live
status: verified
verified: 2026-10-22 @ f2b4be7
entity: berb/llm/cost_tracker.py
---

# CostTracker (real spend accounting)

Process-wide singleton (`get_cost_tracker`, `cost_tracker.py:306`) that records one `CostEvent` per LLM call and reports totals by stage, phase, purpose and node (`cost_tracker.py:111-275`). Output: `cost_report.json` in the run dir (`runner.py:531-538`).

## Why this shape

Attribution travels by `contextvars`, not arguments: the runner wraps each stage in `stage_attribution(stage_num, phase_of(stage))` (`runner.py:198`), and `_record_llm_cost` reads `current_attribution()` at the single choke point `LLMClient._raw_call` (`client.py:1042-1066`). ContextVars survive `asyncio.to_thread`, so stage bodies in worker threads inherit the right stage (`cost_tracker.py` comment above line 57).

## Shape

- Recording failures are swallowed (`client.py:1067-1068`): a broken tracker never fails a call.
- Pricing lookup: `llm/pricing.py`; a missing price yields `cost_usd=0.0` rather than an error (`pricing.py:254` comment), so unpriced models under-report silently.
- Not recorded: ACP calls (no recording in `acp_client.py`).
- Singleton is recreated if closed (`cost_tracker.py:311`).
- `logging_setup.py:36,82` reads `current_attribution()` to stamp stage on log records.
- Other readers: `experiment/search/runner.py:152`, `pipeline/stage_impls/_execution.py:419-454`.

## Connected to

- **owns:** the cost numbers that matter.
- **joins:** [[llm-client]] (writes), `pipeline/runner.py` (attribution and report), `llm/pricing.py`.
- **looks-like-but-is-not:** (1) `SmartLLMClient._estimate_cost`, a fixed-rate per-response guess (`smart_client.py:129-132`); (2) `metrics/reasoning_cost_tracker.py`, a different `get_cost_tracker` used by `deep_query_client.py:432`.

## If you change this

- **Hits:** `cost_report.json` consumers; `logging_setup.py`; budget/cost fields wherever `by_stage()` is read; tests for the tracker and pricing.
- **Hits:** adding a provider client: it must call `_record_llm_cost` or its spend is invisible.
- **Does not hit:** routing decisions; nothing reads the tracker to choose a model.

## Surfaces

| Surface | Role |
|---|---|
| `cost_report.json` | per-run output (outermost call only) |
| `berb/metrics/__init__.py` | re-exports a different tracker, same function name |

## See

- Source: `berb/llm/cost_tracker.py`
