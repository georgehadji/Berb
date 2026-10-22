---
type: object
cluster: llm
universe: live
status: verified
verified: 2026-10-22 @ f2b4be7
entity: berb/llm/client.py
---

# LLMClient (and MultiProviderLLMClient)

The one real HTTP caller: `LLMClient.chat(...)` (`client.py:576`) with retry, model fallback chain, circuit breaker and optional rate limiter. `MultiProviderLLMClient` (`client.py:1253`) fails over across several providers' clients.

## Why this shape

Everything above it (smart client, cascade) is a wrapper exposing the same `chat`/`config` seam, so `chat` is the stable contract. Fallback is a model chain `[primary] + fallback_models` (`client.py:444`); an explicit `model=` skips the chain (`client.py:668`). `_raw_call` is the single choke point (`client.py:867`): both the OpenAI-wire path and the Anthropic-adapter path end in the same parse and `_record_llm_cost` (`client.py:1042`), so cost is recorded exactly once per attempt.

## Shape

- `chat` order: rate limit -> stage token cap -> prepend `system` -> per-model loop -> `_call_with_retry` (backoff, transient-400 detection, circuit breaker) (`client.py:632-704`, `747-`).
- Refuses an image sent to a catalogued text-only model before any spend (`client.py:681-682`); see [[vision]].
- `cached_prefix` folds into the system message with provider cache_control only for models that need it (`client.py:1070-1104`).
- `strip_thinking=True` strips `<think>` tags from the result (`client.py:686`).
- `from_rc_config` builds `LLMConfig`: base URL from config or `PROVIDER_PRESETS`; MetaClaw bridge swaps in a proxy URL; `rate_limit_enabled=False` is hardcoded (`client.py:499-563`). Anthropic and kimi-anthropic get an `AnthropicAdapter` on the ORIGINAL URL, not the proxy (`client.py:566-573`).
- Wire format: `chat_completions` or `responses`, chosen by `config.wire_api` (`client.py:478-492`).
- Cost: `ACPClient` (`llm/acp_client.py`) has no cost-recording call; ACP runs are absent from `cost_report.json`.

## Connected to

- **owns:** retry/backoff, circuit breaker state, request encoding per wire format.
- **joins:** [[cost-tracker]] (records), [[vision]] (gate and encoders), [[llm-factory]] (builds and wraps it), `llm/registry.py` (`model_pins_temperature`, `model_uses_max_completion_tokens`), `llm/anthropic_adapter.py`, `llm/prompt_cache.py`.
- **looks-like-but-is-not:** `llm/output_limits.py` defines its OWN `Stage(IntEnum)` (`output_limits.py:21`), separate from `berb.pipeline.stages.Stage`. `chat(stage=...)` is bridged only by int value (`output_limits.py:116-126`). The pipeline funnel passes `stage=` (`pipeline/_prompt_helpers.py:190`). Renumbering either enum silently changes token caps. Note the cap only applies when `max_tokens is None` (`client.py:659`), and that funnel passes `max_tokens=` explicitly, so the stage cap is bypassed whenever a stage sets one.

## If you change this

- **Hits:** every LLM call. Direct constructors bypassing the factory: `hyperagent/meta_agent.py:130`, `pipeline/metaclaw_post.py:51`. `chat` signature changes hit the wrappers ([[smart-client-router]], [[model-cascade]]) and `pipeline/_prompt_helpers.py:185`.
- **Hits:** tests `tests/test_berb_llm.py`, `test_llm_prompt_caching.py`, `test_llm_provider_utils.py`, `test_smart_client_seam.py`.
- **Does not hit:** model choice policy (that is `registry.py` and [[smart-client-router]]).
- **Watch:** failures are swallowed into "All models failed" (`client.py:704`); `RuntimeError` hides the cause type (use `__cause__`, see `preflight`).

## Surfaces

| Surface | Role |
|---|---|
| `execute_stage` via factory | builds and passes it to every stage |
| `berb run` preflight (`cli.py:287`) | calls `preflight()`; only `LLMClient`, `MultiProviderLLMClient`, `ACPClient` define it |

## See

- Source: `berb/llm/client.py`
