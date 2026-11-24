---
type: object
cluster: pipeline-core
universe: live
status: verified
verified: 2026-10-22 @ f2b4be7
entity: berb/pipeline/runner.py
---

# execute_pipeline (runner)

The async orchestrator: `execute_pipeline(...)` (`runner.py:326`). Walks stages in DAG levels, handles gates, pivots and failure policy, then writes summary, cost report, lessons and packaged deliverables.

## Why this shape

Order comes from `resolve_stage_order(from_stage)` then `_build_dag_levels` (`runner.py:417`, `104-147`). Stages in one level run together via `asyncio.gather` (`runner.py:452`); each stage body runs in a thread through `asyncio.to_thread` (`runner.py:590`). Pivot is recursion: stage 15 decision `pivot`/`refine` re-enters `execute_pipeline` from a rollback target with `_pivot_depth + 1`, capped by `MAX_DECISION_PIVOTS` (`runner.py:378-384`, `486-506`).

## Shape (movement, in order)

1. Open `EventStore` (`event_log.json`), tracing, run logging, write `topic.txt` once (`runner.py:351-376`).
2. If `research.discovery.enabled`, `_pivot_depth == 0` and `to_stage is None`: run the discovery loop and skip stages 7-15 if it promoted a result (`runner.py:399-415`, `275-323`).
3. Per level: `_execute_single_stage` -> `_run_sync_stage_internal` -> [[executor]]; on DONE write [[checkpoint]]; always write heartbeat (`runner.py:599-601`).
4. After each result: stage 14 DONE with `experiment.repair.enabled` runs diagnosis+repair (`runner.py:478-483`); stage 15 DONE with a pivot/refine decision calls `_handle_pivot` and breaks (`runner.py:486-506`).
5. FAILED stops the run unless `skip_noncritical` and the stage is in `NONCRITICAL_STAGES`; BLOCKED_APPROVAL stops only with `stop_on_gate` (`runner.py:508-514`).
6. Epilogue: pipeline summary, `cost_report.json` (outermost call only), evolution lessons, MetaClaw post hook, `package_deliverables` (`runner.py:519-560`). Errors in lessons, MetaClaw and packaging are logged and swallowed.

Citations: as above.

## Connected to

- **owns:** event log writing, pivot recursion, level scheduling.
- **joins:** [[stage]], [[contract]] (`depends_on`), [[executor]], [[checkpoint]], discovery loop (`pipeline/discovery.py`), `pipeline/iterative.py`.
- **looks-like-but-is-not:** `pipeline/iterative.py`, which loops stages 16-22 by calling `execute_pipeline` itself (`iterative.py:334,342,387`).

## If you change this

- **Hits:** every caller of `execute_pipeline`: `cli.py:413` (`cmd_run`, i.e. `berb run`, incl. `--resume`) and `cli.py:1004` (`cmd_literature`, stages 1-8), `server/routes/pipeline.py:121`, `pipeline/iterative.py`, `pipeline/discovery.py:113`, and its own recursion at `runner.py:628,659,697`. Changing the signature or the return value hits all of them.
- **Hits:** `tests/test_berb_runner.py`.
- **Does not hit:** what a stage does or how outputs are validated; that is [[executor]] and [[contract]].
- **Watch:** `to_stage` and `_pivot_depth` exist for the discovery loop and pivots; they are internal-use parameters.

## Surfaces

| Surface | Role |
|---|---|
| `berb run` / `--resume` | calls it |
| `berb serve` pipeline route | calls it |
| iterative and discovery loops | call it per slice |

## See

- Source: `berb/pipeline/runner.py`
