"""One run-status read model (W2).

The dashboard, MCP, chat and HTTP surfaces each used to invent a status from
keys nobody wrote. :func:`read_run_status` derives it from what the runner
does write: ``event_log.json`` (per-stage transitions), ``pipeline_summary.json``
(written when ``execute_pipeline`` returns), ``checkpoint.json`` (fallback for
runs with no event log) and ``heartbeat.json``.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from berb.pipeline.stages import EventStore, RunStatus, Stage, StageStatus

# Between stages (or during post-stage-14 repair) no stage is RUNNING, so a
# heartbeat this recent, from a process that still exists, reads as running.
# shortcut: a reused pid reads as alive; record process start time if that bites.
_HEARTBEAT_LIVE_SEC = 600

_ACTIVE = {StageStatus.RUNNING.value, StageStatus.RETRYING.value}
_AT_REST = {
    StageStatus.BLOCKED_APPROVAL.value: RunStatus.BLOCKED_APPROVAL,
    StageStatus.PAUSED.value: RunStatus.PAUSED,
    StageStatus.FAILED.value: RunStatus.FAILED,
}


@dataclass(frozen=True)
class RunStatusView:
    run_id: str
    status: RunStatus
    current_stage: int | None = None
    current_stage_name: str = ""
    stage_statuses: dict[int, str] = field(default_factory=dict)
    topic: str = ""
    start_time: str = ""
    last_heartbeat: str = ""
    last_error: str | None = None
    pivot_count: int = 0

    @property
    def is_live(self) -> bool:
        return self.status == RunStatus.RUNNING

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status.value,
            "is_live": self.is_live,
            "current_stage": self.current_stage,
            "current_stage_name": self.current_stage_name,
            "stage_statuses": {str(k): v for k, v in self.stage_statuses.items()},
            "topic": self.topic,
            "start_time": self.start_time,
            "last_heartbeat": self.last_heartbeat,
            "last_error": self.last_error,
            "pivot_count": self.pivot_count,
        }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _parse_time(value: object) -> datetime | None:
    if isinstance(value, int | float):
        return datetime.fromtimestamp(value, UTC)
    if isinstance(value, str) and value:
        try:
            ts = datetime.fromisoformat(value)
        except ValueError:
            return None
        return ts if ts.tzinfo else ts.replace(tzinfo=UTC)
    return None


def _pid_alive(pid: int) -> bool:
    """Whether process *pid* exists. Never signals it.

    ``os.kill(pid, 0)`` is a probe on POSIX but terminates the process on
    Windows, so Windows asks the kernel for its exit code instead.
    """
    if os.name == "nt":
        import ctypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
        handle = kernel32.OpenProcess(0x1000, False, pid)  # QUERY_LIMITED_INFORMATION
        if not handle:
            return ctypes.get_last_error() == 5  # type: ignore[attr-defined]  # access denied: exists
        try:
            code = ctypes.c_ulong()
            ok = kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
            return bool(ok) and code.value == 259  # STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def read_run_status(run_dir: Path) -> RunStatusView:
    """Derive one run's status from the files its runner wrote."""
    run_dir = Path(run_dir)
    log = run_dir / "event_log.json"
    store = EventStore(run_id=run_dir.name, storage_path=str(log)) if log.exists() else None
    events = store.get_events() if store else []
    replay = store.replay() if store else None

    stage_statuses: dict[int, str] = {}
    for ev in events:
        stage_statuses[int(ev.to_stage)] = ev.to_status.value
    if not events:
        from berb.pipeline.checkpoint import load_checkpoint

        state = load_checkpoint(run_dir)
        for s in state.completed if state else ():
            stage_statuses[int(s)] = StageStatus.DONE.value

    running = [int(ev.to_stage) for ev in events if stage_statuses[int(ev.to_stage)] in _ACTIVE]
    current: int | None
    if running:
        current = running[-1]
    elif events:
        current = int(events[-1].to_stage)
    else:
        current = _read_json(run_dir / "checkpoint.json").get("last_completed_stage")
    if not isinstance(current, int) or current not in Stage._value2member_map_:
        current = None  # a legacy or corrupt checkpoint's stage number

    heartbeat = _read_json(run_dir / "heartbeat.json")
    hb_time = _parse_time(heartbeat.get("timestamp"))
    pid = heartbeat.get("pid")
    # A stage left RUNNING by a process that is gone was interrupted, not live.
    process_gone = isinstance(pid, int) and not _pid_alive(pid)
    summary = _read_json(run_dir / "pipeline_summary.json")
    generated = _parse_time(summary.get("generated"))
    # A summary older than the last event belongs to an earlier, resumed run.
    summary_is_current = bool(summary) and (
        not events
        or generated is None
        or events[-1].timestamp.astimezone(UTC).replace(microsecond=0) <= generated
    )
    final = summary.get("final_status")

    status: RunStatus
    if running and process_gone:
        status = RunStatus.STOPPED
    elif running:
        status = RunStatus.RUNNING
    elif summary_is_current and final in {s.value for s in RunStatus}:
        status = RunStatus(final)
    elif not stage_statuses:
        status = RunStatus.PENDING
    elif current is not None and stage_statuses.get(current) in _AT_REST:
        status = _AT_REST[stage_statuses[current]]
    elif (
        not process_gone
        and hb_time
        and (datetime.now(UTC) - hb_time).total_seconds() < _HEARTBEAT_LIVE_SEC
    ):
        status = RunStatus.RUNNING
    else:
        status = RunStatus.STOPPED

    topic_file = run_dir / "topic.txt"
    return RunStatusView(
        run_id=run_dir.name,
        status=status,
        current_stage=current,
        current_stage_name=Stage(current).name if current else "",
        stage_statuses=stage_statuses,
        topic=topic_file.read_text(encoding="utf-8").strip() if topic_file.exists() else "",
        start_time=events[0].timestamp.isoformat() if events else "",
        last_heartbeat=hb_time.isoformat() if hb_time else "",
        last_error=replay.last_error if replay else None,
        pivot_count=replay.pivot_count if replay else 0,
    )
