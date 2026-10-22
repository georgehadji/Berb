---
type: object
cluster: pipeline-core
universe: live
status: verified
verified: 2026-10-22 @ f2b4be7
entity: berb/pipeline/contracts.py
---

# StageContract and CONTRACTS

Per-stage input files, required output files, definition of done, error code, retry cap and `depends_on` (`contracts.py:212`). `CONTRACTS: dict[Stage, StageContract]` (`contracts.py:223`) is the table everything reads.

## Why this shape

`CONTRACTS` is the single source for both execution order and output validation. Order is derived from `depends_on` by `resolve_stage_order()` ([[runner]]). Output validation is in `execute_stage` ([[executor]]): a DONE stage missing or with an empty `output_files` entry is turned into FAILED/retry (`executor.py:262-287`). Missing `input_files` fail the stage before it runs (`executor.py:168-181`).

## Shape

- Two copies of every contract exist. `CONTRACTS` in `contracts.py` (live), and a `contract=` plus `depends_on=` on each `@register_stage` decorator in `stage_impls/` (e.g. `_topic.py:29-40`). Both are hand-written.
- `rebuild_from_registry()` (`contracts.py:432`) would copy decorator contracts into `CONTRACTS`. It has no caller in `berb/` or `tests/`. So the decorator copy is not read.
- Also in this file: data carriers `ExecutionFeedback`, `SeedValidity`, `SplitEvidence`, `Assumption`, `ExperimentSummary`. They are artifact shapes between stages, not part of the contract table.

Citations: `contracts.py:212-223, 432-451`; `registry.py:74-80`; `executor.py:233` (only `reg.fn` is read from a registration).

## Connected to

- **owns:** `depends_on` graph, output-file validation rules.
- **joins:** [[stage]] (keys), [[runner]] (via `resolution.py`), [[executor]] (validation), [[stage-impls]] (decorators).
- **looks-like-but-is-not:** the contract on the `@register_stage` decorator. Editing it changes nothing at runtime.

## If you change this

- **Hits:** `output_files`: every stage that writes it and every later stage listing it in `input_files`; a mismatch fails the run at the next stage. `depends_on`: execution order and which stages run concurrently in one DAG level (`runner.py:104-147`).
- **Hits:** `tests/test_berb_contracts.py`, `tests/test_resolution.py`.
- **Does not hit:** the decorator's `contract=`/`depends_on=`. Update it too to keep the two copies aligned, but it has no effect alone.

## Surfaces

| Surface | Role |
|---|---|
| executor | reads inputs/outputs |
| `resolution.py` | reads `depends_on` |
| `runner._build_dag_levels` | reads `depends_on` |

## See

- Source: `berb/pipeline/contracts.py`
