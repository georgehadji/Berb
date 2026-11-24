---
type: object
cluster: llm
universe: live
status: verified
verified: 2026-10-22 @ f2b4be7
entity: berb/llm/smart_client.py
---

# SmartLLMClient and NadirClawRouter

`SmartLLMClient` (`smart_client.py:48`) wraps a base client and, per config, routes each prompt to a cheap/mid/premium model via `NadirClawRouter` (`nadirclaw_router.py:432`), compacts context, and tracks tokens. NadirClaw is the only live router.

## Why this shape

The wrapper only intercepts `chat`. `chat` delegates to `_complete_sync`, which: classifies the last user message, picks a model, optimizes messages, calls `base_client.chat`, tracks tokens, estimates cost (`smart_client.py:152-321`). `complete()` is just a thread-offloaded async door returning the extra metadata (`smart_client.py:187`). The pipeline uses `chat`; pipeline `.chat(` calls pass no `model=`, so routing fires when enabled.

## Shape

- Created only if `nadirclaw.enabled` or `token_tracking.enabled` (`llm/__init__.py:185`). Router exists only when `nadirclaw.enabled` (`smart_client.py:89-111`).
- Explicit `model=` skips routing (tier "explicit") (`smart_client.py:235-238`).
- Tiers: simple/mid/complex from `ComplexityClassifier`, thresholds default (0.3, 0.7). Defaults come from `registry.resolve("fast" | "literature" | "writing")`, not literals; the complex tier deliberately avoids the "reasoning" model (`nadirclaw_router.py:33-40`, `455-465`).
- Router keeps an LRU-ish dict cache keyed by prompt for selections (`nadirclaw_router.py:581-612`).
- `ContextOptimizer` modes dedup system prompts, compact whitespace and JSON (`nadirclaw_router.py:233-430`). It rewrites messages sent to the model.
- `estimated_cost` here uses fixed rates (`smart_client.py:129-132`), unrelated to `CostTracker`. See [[cost-tracker]] for real spend.
- `preflight()` delegates to the base client (added 2026-10-22).
- Wrapping a pre-built `base_client` preserves multi-provider failover and ACP (`smart_client.py:78-86`).

## Connected to

- **owns:** routing decision, context compaction, optional `TokenTracker` (`utils/token_tracker.py`, writes a DB at `tracking_config.db_path`).
- **joins:** [[llm-factory]] (builds it), [[llm-client]] (delegate), `llm/registry.py` (tier defaults), [[model-cascade]] (may sit on top of it).
- **looks-like-but-is-not:** `reasoning/*.py` docstrings mention `SmartLLMClient` but do not import it at runtime (only in docstring examples); `extended_router.py` was deleted 2026-09-02.

## If you change this

- **Hits:** every stage call when routing/tracking is on; `tests/test_smart_client_seam.py`.
- **Hits:** `registry.py` task names `fast`, `literature`, `writing`: renaming them breaks the router at import time (module-level `resolve(...)`, `nadirclaw_router.py:38-40`).
- **Hits:** quality: `ContextOptimizer` modifies prompt text; a change there affects model input, not just cost.
- **Does not hit:** pricing or `cost_report.json`; those come from [[llm-client]] `_record_llm_cost`.

## Surfaces

| Surface | Role |
|---|---|
| config `nadirclaw.*`, `token_tracking.*` | switches |
| `get_tracking_summary()` | read by callers that hold the client (`smart_client.py:356`) |

## See

- Source: `berb/llm/smart_client.py`, `berb/llm/nadirclaw_router.py`
