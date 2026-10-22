---
type: object
cluster: pipeline-core
universe: live
status: verified
verified: 2026-10-22 @ f2b4be7
entity: berb/pipeline/stages.py
---

# Stage (enum, status, gate tables)

The 23 pipeline stages as `Stage(IntEnum)` (`stages.py:26`), plus status values and the gate/rollback/noncritical tables. Product word "stage"; code name `Stage`.

## Why this shape

The enum number is identity only. It is also the display number (`stage-NN/` dirs) and the tie-break for DAG order. Execution order is NOT the enum order: it comes from `StageContract.depends_on` (see [[contract]]). The `STAGE_SEQUENCE`/`NEXT_STAGE` tables were removed (`stages.py:97-99`). Code that does `Stage(int(stage) + 1)` assumes number order anyway: `advance()` (`stages.py:270`) and `default_rollback_stage` (`stages.py:233`).

## Shape

- `Stage` 1..23; `StageStatus` and `TransitionEvent` StrEnums (`stages.py:69,81`).
- `GATE_STAGES` = 5, 9, 20 (`stages.py:105`); `gate_required()` also honours `config.security.hitl_required_stages` (`stages.py:219`).
- `DECISION_ROLLBACK`: pivot -> HYPOTHESIS_GEN (8), refine -> ITERATIVE_REFINE (13); `MAX_DECISION_PIVOTS = 2` (`stages.py:124-129`).
- `NONCRITICAL_STAGES` = 20, 21; CITATION_VERIFY (23) is deliberately critical (`stages.py:135-141`).
- `PHASE_MAP` / `phase_of()` (`stages.py:147,183`): phase labels A..H, used for cost attribution (`runner.py:198`).
- Event sourcing: `StageTransitionEvent`, `PipelineState`, `EventStore` (`stages.py:350-572`). `EventStore` writes `event_log.json` per run.

Citations: `berb/pipeline/stages.py` as above.

## Connected to

- **owned-by:** nothing; imported by everything below.
- **joins:** [[contract]] (order and I/O), [[runner]] (events, pivot, gates), [[executor]] (gate block).
- **looks-like-but-is-not:** the `advance()` state machine. Only `executor.py:223` calls it, with the result discarded; `GATE_ROLLBACK`, `TRANSITION_MAP` and `default_rollback_stage` are reached only through `advance()` or by tests (`tests/test_berb_stages.py`). The runner decides status, rollback and pivots inline. Real rollback uses `DECISION_ROLLBACK`, not `GATE_ROLLBACK`.

## If you change this

- **Hits:** adding or renumbering a stage: the `CONTRACTS` entry in `contracts.py`, a `@register_stage` impl, `PHASE_MAP`, `len(Stage)` as `total_stages` (`runner.py:387`), `tests/test_berb_stages.py`, the hardcoded `< 23` in `advance()`.
- **Hits:** editing `GATE_STAGES` or `NONCRITICAL_STAGES` changes live behaviour (executor gate block `executor.py:347`, runner skip `runner.py:509`).
- **Does not hit:** editing `GATE_ROLLBACK` or `TRANSITION_MAP` changes no run behaviour; only `advance()` and its tests read them.

## Surfaces

| Surface | Role |
|---|---|
| runner, executor | read gate and noncritical tables |
| `berb run --from-stage` (`cli.py`) | resolves a stage name to this enum |

## See

- Source: `berb/pipeline/stages.py`
