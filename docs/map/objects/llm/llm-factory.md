---
type: object
cluster: llm
universe: live
status: verified
verified: 2026-10-22 @ f2b4be7
entity: berb/llm/__init__.py
---

# create_llm_client (the factory and its wrapper stack)

`create_llm_client(config)` (`llm/__init__.py:153`) picks the base client and optionally wraps it. It is what makes config flags (`llm.provider`, `llm.fallback_providers`, `nadirclaw`, `token_tracking`, `cascade`) take effect.

## Why this shape

Each feature is a wrapper with the same `chat`/`config` seam, so the order is the behaviour:

```
base:    acp -> ACPClient | fallback_providers -> MultiProviderLLMClient | else LLMClient
wrap 1:  SmartLLMClient   if nadirclaw.enabled OR token_tracking.enabled
wrap 2:  CascadingLLMClient  if cascade.enabled AND cascade.steps non-empty
```

(`__init__.py:171-203`, `206-234`). The cascade sits outside the smart client, so each rung's explicit `model=` bypasses NadirClaw routing (see [[model-cascade]]).

## Shape

- Imports are lazy and PEP 562 re-exports are resolved on first access, to avoid pulling httpx into light importers (`__init__.py:9-44`).
- `PROVIDER_PRESETS` (`__init__.py:116`): base URLs for openai, openrouter, deepseek, xai, perplexity, anthropic, kimi-anthropic, novita, minimax, openai-compatible.
- Callers: `pipeline/executor.py:201` (every stage), `cli.py:285`, `pipeline/experiment_repair.py:348`.
- Bypassers (build `LLMClient` directly, so no failover, routing, cascade or SmartLLMClient tracking): `hyperagent/meta_agent.py:130`, `pipeline/metaclaw_post.py:51`.
- **Fixed 2026-10-22 (uncommitted):** `cmd_run` calls `client.preflight()` on the factory's result (`cli.py:282-287`) but `SmartLLMClient` and `CascadingLLMClient` had none, so `berb run` with `nadirclaw`, `token_tracking` or `cascade` enabled would raise `AttributeError` unless `--skip-preflight`. Both now delegate to the wrapped client. Rule: every wrapper must expose `chat`, `config` AND `preflight`. Tests: `tests/test_smart_client_seam.py` (`test_every_factory_wrapper_has_preflight`), `tests/test_model_cascade.py`.
- The executor keeps a client only if it has `base_url` and `api_key`, except ACP; otherwise stages get `llm=None` (`executor.py:201-217`).

## Connected to

- **owns:** wrap order and which config flag enables which layer.
- **joins:** [[llm-client]], [[smart-client-router]], [[model-cascade]], `ACPClient`, `berb/config.py` sections `llm`, `nadirclaw`, `token_tracking`, `cascade`.
- **looks-like-but-is-not:** the public API (`__all__`). `create_llm_client`, `LLMClient`, `SmartLLMClient` are NOT in `__all__`; see [[public-api]].

## If you change this

- **Hits:** every stage's LLM behaviour (via `executor.py:201`); the config schema sections above; `tests/test_smart_client_seam.py`, `tests/test_model_cascade.py`.
- **Hits:** adding a wrapper: it must expose `chat`, `config` and `preflight`, because the executor reads `candidate.config.base_url/api_key` (`executor.py:211-217`) and `_prompt_helpers.py:177` mutates `llm.config.timeout_sec`.
- **Does not hit:** the two bypassers above; update them separately if the change must reach them.

## Surfaces

| Surface | Role |
|---|---|
| `berb run` stages | indirect, through the executor |
| `berb run` (`cli.py:285`) | direct, for the preflight check |

## See

- Source: `berb/llm/__init__.py`
