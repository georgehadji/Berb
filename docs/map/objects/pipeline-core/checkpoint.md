---
type: object
cluster: pipeline-core
universe: live
status: verified
verified: 2026-10-22 @ f2b4be7
entity: berb/pipeline/checkpoint.py
---

# Checkpoint and heartbeat

Atomic "last completed stage" file (`checkpoint.json`) and a liveness file (`heartbeat.json`) in the run dir. `write_checkpoint`, `read_checkpoint`, `CheckpointManager`, `write_heartbeat` (`checkpoint.py:40,60,132,175`).

## Why this shape

Resume must never read a half-written file: write goes through temp file, fsync, atomic replace (`checkpoint.py:77-96`). `CheckpointManager` adds a lock because stages in one DAG level finish concurrently (`checkpoint.py:175-196`). `read_checkpoint` returns the NEXT stage in DAG order, not the stored one (`checkpoint.py:157-164`).

## Shape

- Written only when a stage is DONE (`runner.py:599-600`). A stage that ends BLOCKED_APPROVAL or FAILED writes no checkpoint, so `--resume` re-runs it.
- The checksum covers only `stage:name:run_id` (`checkpoint.py:74`). It catches a mangled file, not tampering: anyone can recompute it. Missing checksum is accepted as legacy (`checkpoint.py:104-106`).
- A bad or corrupt checkpoint returns `None`, i.e. the caller restarts from the default stage.
- `resume_from_checkpoint()` (`checkpoint.py:199`) has no caller outside tests; `cli.py:369-386` calls `read_checkpoint` directly.
- Heartbeat is written after every stage regardless of status (`runner.py:601`); `sentinel.sh` at repo root is the watchdog.

## Connected to

- **owns:** `checkpoint.json`, `heartbeat.json` formats.
- **joins:** [[runner]] (writes), `cli.py` (reads for `--resume`), `resolution.resolve_stage_order` ([[contract]]) for "next".
- **looks-like-but-is-not:** `event_log.json`, the `EventStore` in [[stage]]. It records transitions; resume does not read it.

## If you change this

- **Hits:** `--resume` in `cli.py:386`; any external watcher parsing `heartbeat.json`; `tests/test_berb_checkpoint.py`, `tests/test_checkpoint.py`, `tests/test_checkpoint_regression.py`.
- **Hits:** adding a field to the checkpoint: the checksum does not cover it.
- **Does not hit:** `execute_stage` and stage outputs.

## Surfaces

| Surface | Role |
|---|---|
| `berb run --resume` | reads |
| runner | writes |
| `sentinel.sh` | reads `heartbeat.json` (`sentinel.sh:26`) |

## See

- Source: `berb/pipeline/checkpoint.py`
