---
type: object
cluster: pipeline-core
universe: live
status: verified
verified: 2026-10-22 @ f2b4be7
entity: berb/pipeline/executor.py
---

# execute_stage (executor)

Runs ONE stage and returns a `StageResult`: `execute_stage(stage, *, run_dir, run_id, config, adapters, auto_approve_gates)` (`executor.py:152`). Synchronous; the runner wraps it in a thread.

## Why this shape

The executor is the seam between orchestration and stage code. It owns the checks that make a stage honest: input present, output present and non-empty, gate blocking. Stage impls only produce files. It also builds the LLM client and passes it in, so impls get `llm=None` when nothing is configured.

## Shape (movement)

1. Create `stage-NN/` under the run dir; load `CONTRACTS[stage]` (`executor.py:163-166`).
2. Missing `input_files` -> FAILED/retry before running (`executor.py:168-181`).
3. Build the client via `create_llm_client(config)`; non-ACP clients without `base_url` and `api_key` become `llm=None` (`executor.py:201-217`).
4. Look up the impl in the registry (`executor.py:227`); pass `prompts=` only if its signature accepts it (`executor.py:241-251`). Any exception becomes FAILED/retry (`executor.py:252-260`).
5. If DONE, check every `output_files` entry exists and is non-empty (dirs: non-empty); else FAILED/retry (`executor.py:262-287`).
6. Optional MetaClaw PRM gate at stages 5, 9, 15, 20: score -1.0 turns DONE into FAILED; errors here are non-blocking (`executor.py:289-345`).
7. Gate stages: with `auto_approve_gates` record approval, else set BLOCKED_APPROVAL (`executor.py:347-365`).
8. Write `stage_meta` and `stage_health.json`; return (`executor.py:370-389`).

## Connected to

- **owns:** output validation, gate blocking, LLM-client guard, per-stage health file.
- **joins:** [[contract]] (inputs/outputs), [[stage]] (gate table), [[stage-impls]] (registry lookup), [[runner]] (only caller, `runner.py:590`).
- **looks-like-but-is-not:** the importing block at the top. Importing `stage_impls` modules is what fires the `@register_stage` decorators (`executor.py:148` comment); removing an import unregisters that stage and it fails with "No stage implementation registered".

## If you change this

- **Hits:** every stage result and every run. Callers of `execute_stage`: `runner.py:590`, plus `tests/test_berb_executor.py`.
- **Hits:** private names re-exported for old callers (`# noqa: F401` block, `executor.py:52-146`); e.g. `packaging.py` imports `_extract_paper_title` from here. Check importers before removing a re-export.
- **Does not hit:** stage order, pivots, checkpoints; those are [[runner]]/[[checkpoint]].

## See

- Source: `berb/pipeline/executor.py`
