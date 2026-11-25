"""Checkpoint and heartbeat — atomic state persistence for pipeline recovery.

P0 2026-04-02: Added Event Sourcing for debugging, audit trails, and state recovery.
P1 FIX: Added SHA-256 checksum + fsync() for durability.

# Author: Georgios-Chrysovalantis Chatzivantsidis
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from berb.pipeline.stages import Stage
from berb.utils.atomic import replace_with_retry

logger = logging.getLogger(__name__)


# ============================================================================
# Helpers
# ============================================================================


def _utcnow_iso() -> str:
    """Return current UTC time as ISO-8601 string (seconds precision)."""
    return datetime.now(UTC).isoformat(timespec="seconds")


# ============================================================================
# Heartbeat
# ============================================================================


def write_heartbeat(run_dir: Path, stage: Stage, run_id: str) -> None:
    """Write heartbeat file for sentinel watchdog monitoring."""
    heartbeat = {
        "run_id": run_id,
        "pid": os.getpid(),
        "last_stage": int(stage),
        "last_stage_name": stage.name,
        "timestamp": _utcnow_iso(),
    }
    (run_dir / "heartbeat.json").write_text(
        json.dumps(heartbeat, indent=2),
        encoding="utf-8",
    )


# ============================================================================
# Checkpoint
# ============================================================================


@dataclass(frozen=True)
class CheckpointState:
    """What a run directory's checkpoint says about resuming it (PC-6).

    ``next_stage`` is the first stage, in DAG order, that this run has not
    completed; None when the run is complete or the checkpoint is unreadable.
    """

    completed: frozenset[Stage]
    next_stage: Stage | None
    complete: bool
    unreadable: bool = False


def _checksum(stage_num: object, stage_name: object, run_id: object) -> str:
    # Unchanged since before completed_stages existed, so older builds still
    # validate (and fall back to last_completed_stage on) a newer checkpoint.
    data = f"{stage_num}:{stage_name}:{run_id}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def _completed_from(data: dict) -> set[int]:
    """Completed stage numbers recorded in a parsed checkpoint."""
    if isinstance(data.get("completed_stages"), list):
        return {int(n) for n in data["completed_stages"]}
    # Legacy format: only a high-water mark, read as "everything up to it".
    from berb.pipeline.resolution import resolve_stage_order

    last = data.get("last_completed_stage")
    if last is None:
        return set()
    order = list(resolve_stage_order())
    last_stage = Stage(last)
    if last_stage not in order:
        return set()
    return {int(s) for s in order[: order.index(last_stage) + 1]}


def _load_completed(run_dir: Path) -> set[int]:
    state = load_checkpoint(run_dir)
    return {int(s) for s in state.completed} if state else set()


def write_checkpoint(run_dir: Path, stage: Stage, run_id: str) -> None:
    """Record *stage* as completed, atomically (temp file + rename).

    Keeps the set of completed stages, not just the last one written: in a
    parallel DAG level a later stage can finish after an earlier one failed,
    and a high-water mark would make resume skip the failed stage (PC-6).
    Includes a SHA-256 checksum and fsync() for durability.
    """
    _write_checkpoint_file(run_dir, _load_completed(run_dir) | {int(stage)}, stage, run_id)


def forget_completed(run_dir: Path, stage_nums: Iterable[int]) -> None:
    """Mark *stage_nums* as not completed, e.g. after a PIVOT archives them (PC-5)."""
    state = load_checkpoint(run_dir)
    if state is None or state.unreadable:
        return
    done = {int(s) for s in state.completed} - {int(n) for n in stage_nums}
    if not done:
        (run_dir / "checkpoint.json").unlink(missing_ok=True)
        return
    _write_checkpoint_file(run_dir, done, Stage(max(done)), _read_run_id(run_dir))


def _read_run_id(run_dir: Path) -> str:
    try:
        data = json.loads((run_dir / "checkpoint.json").read_text(encoding="utf-8"))
        return str(data.get("run_id", ""))
    except (OSError, json.JSONDecodeError):
        return ""


def _write_checkpoint_file(run_dir: Path, done: set[int], stage: Stage, run_id: str) -> None:
    completed = sorted(done)
    checkpoint: dict[str, object] = {
        "last_completed_stage": int(stage),
        "last_completed_name": stage.name,
        "completed_stages": completed,
        "run_id": run_id,
        "timestamp": _utcnow_iso(),
    }
    checkpoint["checksum"] = _checksum(int(stage), stage.name, run_id)

    target = run_dir / "checkpoint.json"
    fd, tmp_path = tempfile.mkstemp(dir=run_dir, suffix=".tmp", prefix="checkpoint_")
    os.close(fd)
    try:
        with open(tmp_path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(checkpoint, indent=2))
            fh.flush()
            os.fsync(fh.fileno())

        replace_with_retry(Path(tmp_path), target)

        if hasattr(os, "O_DIRECTORY"):
            dir_fd = os.open(run_dir, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
    except BaseException:
        Path(tmp_path).unlink(missing_ok=True)
        raise


def validate_checkpoint_checksum(data: dict) -> bool:
    """Validate checkpoint checksum.

    Returns True if checksum is valid or missing (for backward compat).
    """
    if "checksum" not in data:
        logger.debug("Checkpoint has no checksum (legacy format), accepting")
        return True

    expected = data["checksum"]
    stage = data.get("last_completed_stage")
    stage_name = data.get("last_completed_name")
    run_id = data.get("run_id")

    if None in (stage, stage_name, run_id):
        logger.warning("Checkpoint missing required fields for checksum validation")
        return False

    actual = _checksum(stage, stage_name, run_id)

    if actual != expected:
        logger.error(
            "Checkpoint checksum mismatch! Expected %s, got %s. "
            "Checkpoint may be corrupted or tampered with.",
            expected,
            actual,
        )
        return False

    return True


def load_checkpoint(run_dir: Path) -> CheckpointState | None:
    """Read a run's checkpoint. None means there is no checkpoint file.

    Resume starts at the first stage in DAG order that is not completed,
    ignoring stages before the earliest completed one (a run started with
    ``--from-stage`` never ran those here). A finished run reads as
    ``complete`` rather than as "no checkpoint", which made ``--resume``
    restart at stage 1 and overwrite the paper (PC-6).
    """
    from berb.pipeline.resolution import resolve_stage_order

    cp_path = run_dir / "checkpoint.json"
    if not cp_path.exists():
        return None
    try:
        data = json.loads(cp_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not validate_checkpoint_checksum(data):
            raise ValueError("checksum validation failed")
        done = _completed_from(data)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as e:
        logger.error("Checkpoint at %s is unreadable (%s)", cp_path, e)
        return CheckpointState(frozenset(), None, complete=False, unreadable=True)

    order = list(resolve_stage_order())
    first_done = next((i for i, s in enumerate(order) if int(s) in done), len(order))
    next_stage = next((s for s in order[first_done:] if int(s) not in done), None)
    completed = frozenset(s for s in order if int(s) in done)
    return CheckpointState(completed, next_stage, complete=bool(done) and next_stage is None)


def read_checkpoint(run_dir: Path) -> Stage | None:
    """Return the next stage to execute, or None (no checkpoint, unreadable, or complete).

    Use :func:`load_checkpoint` to tell those three apart.
    """
    state = load_checkpoint(run_dir)
    return state.next_stage if state else None


# ============================================================================
# Concurrency-safe checkpoint manager (Phase 3 — DAG parallelism)
# ============================================================================


class CheckpointManager:
    """Serializes concurrent checkpoint writes for the parallel DAG executor.

    The current ``write_checkpoint`` uses an atomic temp+rename pattern,
    which is safe for sequential writes. When parallel stages complete
    simultaneously (Phase 3 Step 7), this manager ensures only one write
    at a time updates the checkpoint file.
    """

    def __init__(self) -> None:
        import threading

        self._lock = threading.Lock()

    def write(self, run_dir: Path, stage: Stage, run_id: str) -> None:
        """Thread-safe checkpoint write."""
        with self._lock:
            write_checkpoint(run_dir, stage, run_id)

    def read(self, run_dir: Path) -> Stage | None:
        """Thread-safe checkpoint read (readers don't conflict on write lock)."""
        return read_checkpoint(run_dir)


def resume_from_checkpoint(run_dir: Path, default_stage: Stage = Stage.TOPIC_INIT) -> Stage:
    """Resolve the stage to resume from using checkpoint metadata."""
    next_stage = read_checkpoint(run_dir)
    return next_stage if next_stage is not None else default_stage
