---
type: object
cluster: llm
universe: live
status: verified
verified: 2026-10-22 @ f2b4be7
entity: berb/llm/__init__.py
---

# berb.llm public API (`__all__`)

The supported import surface, decided 2026-09-02 (root `CLAUDE.md`). Its modules are treated as entry points by `scripts/check_reachability.py`, so published-but-internally-unused code is not reported dead. Guarded by `tests/test_public_api_contract.py`.

## Why this shape

`__all__` (`__init__.py:46-77`) is a published contract, not a list of what the pipeline uses. It is mostly presets, OpenRouter adapter names and vision helpers.

## Shape

- In `__all__`: `LLMProvider`, `get_provider_from_model`, `validate_model_for_provider`, `PROVIDER_PRESETS`, vision names, OpenRouter adapter names, preset names (`MODELS`, `PRESETS`, `get_model`, `to_llm_config`, ...).
- NOT in `__all__`: `LLMClient`, `MultiProviderLLMClient`, `SmartLLMClient`, `create_llm_client` (a plain function at `__init__.py:153`). They work as imports but are outside the declared contract.
- `PROVIDER_PRESETS` is exported but defined inline, not via the lazy `_EXPORTS` table (`__init__.py:116`).
- Adding a package to `PUBLIC_API_PACKAGES` is a product decision, not a way to quieten the dead-code gate.

## Connected to

- **joins:** [[vision]], [[llm-factory]], `llm/presets.py`, `llm/openrouter_adapter.py`, `.reachability-allowlist`.
- **looks-like-but-is-not:** the factory. Callers use `create_llm_client` heavily, but it is outside the contract.

## If you change this

- **Hits:** external importers of `berb.llm`; `tests/test_public_api_contract.py` (every exported name must resolve); the reachability ratchet in CI.
- **Does not hit:** anything internal that imports `berb.llm.client` directly (many do; see `executor.py:20`).

## Surfaces

| Surface | Role |
|---|---|
| external code importing `berb.llm` | consumers (none recorded in this repo) |
| `scripts/check_reachability.py` | treats `__all__` modules as roots |

## See

- Source: `berb/llm/__init__.py`
