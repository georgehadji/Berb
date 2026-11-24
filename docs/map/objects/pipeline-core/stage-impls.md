---
type: object
cluster: pipeline-core
universe: live
status: verified
verified: 2026-10-22 @ f2b4be7
entity: berb/pipeline/stage_impls/
---

# Stage implementations and the registry

The 23 stage functions, one `@register_stage` each, spread over 13 modules in `berb/pipeline/stage_impls/`, plus the registry in `berb/pipeline/registry.py` that maps `Stage -> function`.

## Why this shape

Registration is by import side effect. `executor.py` imports every `_execute_*` name, which runs the decorators (`executor.py:72-146`). `get_registration(stage).fn` is then all the executor reads (`executor.py:227-233`). A stage module not imported there has no impl.

## Shape

- Modules: `_topic` (1-2), `_literature` (3-6), `_synthesis` (7-8), `_experiment_design` (9), `_code_generation` (10), `_execution` (11-13), `_analysis` (14-15), `_paper_writing` (16-17), `_review` (18-20), `_archive` (21), `_export` (22), `_citations` (23). Count: 25 `register_stage(` hits in `berb/`, 2 of them in `registry.py`; 23 are decorators.
- Impl signature: `(stage_dir, run_dir, config, adapters, *, llm=None[, prompts])` returning `StageResult` (`_topic.py:41-47`).
- Stage-shared helpers live in `pipeline/_helpers.py` and sibling `_*_helpers.py`, not in `stage_impls/`.
- Registry `depends_on` and `contract` are carried but not read at runtime; see [[contract]].

Citations: `stage_impls/_topic.py:29-47`; `registry.py:52-92`.

## Connected to

- **owns:** per-stage behaviour and prompts use.
- **joins:** [[executor]] (imports and calls), [[contract]] (must produce the declared `output_files`), `prompts.default.yaml` via `PromptManager`.
- **looks-like-but-is-not:** `pipeline/code_agent.py`, `experiment_repair.py`, `opencode_bridge.py`: helpers that stage 10 and 13 call, living beside the runner rather than in `stage_impls/`.

## If you change this

- **Hits:** the stage's declared `output_files` and the `input_files` of later stages ([[contract]]); `tests/test_berb_executor.py` and stage-specific tests; the `# noqa: F401` re-exports in `executor.py` that other modules import.
- **Does not hit:** order, gates and rollback; those sit in [[stage]], [[contract]], [[runner]].
- **Watch:** adding a stage means a new `Stage` member, a `CONTRACTS` entry, an import in `executor.py`, and the decorator. Missing the import fails only at run time.

## See

- Source: `berb/pipeline/stage_impls/`, `berb/pipeline/registry.py`
