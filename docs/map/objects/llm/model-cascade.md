---
type: object
cluster: llm
universe: live
status: verified
verified: 2026-10-22 @ f2b4be7
entity: berb/llm/model_cascade.py
---

# CascadingLLMClient (model cascade)

Tries a cheap model first and escalates only if a quality evaluator scores the answer below that rung's threshold (`model_cascade.py:92`). Off by default; enabled by `config.cascade.enabled` with at least one step (`llm/__init__.py:213-215`).

## Why this shape

Its value rests entirely on the evaluator. The default evaluator is a generic-failure heuristic (`model_cascade.py:261`), not a judge. `get_stats()["cascade_exits"]` (zero-based step index -> count) is the calibration measurement: everything at step 0 means too lenient; nothing before the last step means too harsh and you pay twice (`model_cascade.py:236-255`).

## Shape

- Per call: drop any caller `model=` (it would defeat the cascade), then for each rung call `base_client.chat(model=step.model, max_tokens=step.max_tokens, temperature=step.temperature)`; accept on `score >= min_score`; a rung that raises moves on (`model_cascade.py:169-205`).
- If no rung is accepted: return the last response; else the `fallback_model`; else `RuntimeError` (`model_cascade.py:215-234`).
- `quick_eval_enabled=False` accepts the first successful rung (`model_cascade.py:191-193`).
- The last rung should have `min_score=0.0` as an always-accept backstop (`model_cascade.py:67-71`).
- Synchronous; stats guarded by a `threading.Lock` (`model_cascade.py:133`).
- **Fixed 2026-10-22 (uncommitted):** `chat` used to pass `max_tokens`/`temperature` explicitly AND via `**kwargs`, so any caller passing `max_tokens` (the pipeline funnel always does, `pipeline/_prompt_helpers.py:187`) made every rung raise `TypeError`. Now both are popped from kwargs first; a rung's `temperature` always wins, a rung's `max_tokens` wins only when set, else the caller's applies; the fallback model gets the caller's values. Tests: `tests/test_model_cascade.py` (`test_caller_max_tokens_does_not_collide_with_the_rung` and four siblings).
- Restored 2026-09-02 from `9d026a1`, minus cache, cost table and async `chat` (module docstring).
- `get_cascade_for_stage` and `_two_rung` helpers exist (`model_cascade.py:348-368`); `create_llm_client` does not use them (it builds steps from config).

## Connected to

- **joins:** [[llm-factory]] (wraps; `preflight()` delegates to the wrapped client), [[smart-client-router]] (rung `model=` bypasses its routing), `llm/registry.py` (`price_sorted_chain`).
- **looks-like-but-is-not:** the `fallback_models` chain inside [[llm-client]]; that handles errors, this handles quality.

## If you change this

- **Hits:** `config.cascade` schema (`config.py` near line 929), `llm/__init__.py:206-234`, `tests/test_model_cascade.py`.
- **Hits:** cost and quality of every call when enabled, and `cost_report.json` (each rung is a recorded call).
- **Does not hit:** anything when `cascade.enabled` is false (the default).
- **Watch:** the caller's `temperature` is ignored on rungs; the rung's `temperature` (default 0.7) always applies.

## Surfaces

| Surface | Role |
|---|---|
| config `cascade.*` | switch and steps |
| `get_stats()` | measurement; no caller found in `berb/` (grep), so nothing surfaces it unless you call it |

## See

- Source: `berb/llm/model_cascade.py`
