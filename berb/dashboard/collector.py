"""Run data collector — scans artifacts/ for pipeline state."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from berb.pipeline._io_helpers import _is_archived_stage_path
from berb.pipeline.run_status import _parse_time, read_run_status

logger = logging.getLogger(__name__)


@dataclass
class RunSnapshot:
    """Point-in-time snapshot of a pipeline run."""

    run_id: str
    path: str
    status: str = "unknown"
    current_stage: int = 0
    current_stage_name: str = ""
    total_stages: int = 23
    start_time: str = ""
    elapsed_sec: float = 0.0
    is_active: bool = False
    topic: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)
    stages_completed: list[str] = field(default_factory=list)
    stage_statuses: dict[str, str] = field(default_factory=dict)
    last_log_lines: list[str] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "path": self.path,
            "status": self.status,
            "current_stage": self.current_stage,
            "current_stage_name": self.current_stage_name,
            "total_stages": self.total_stages,
            "start_time": self.start_time,
            "elapsed_sec": round(self.elapsed_sec, 1),
            "is_active": self.is_active,
            "topic": self.topic,
            "metrics": self.metrics,
            "stages_completed": self.stages_completed,
            "stage_statuses": self.stage_statuses,
            "error": self.error,
        }


class DashboardCollector:
    """Collect run state from artifacts/ directory."""

    def __init__(
        self,
        artifacts_dir: str = "artifacts",
        max_log_lines: int = 200,
    ) -> None:
        self._artifacts = Path(artifacts_dir)
        self._max_log_lines = max_log_lines

    def collect_all(self) -> list[RunSnapshot]:
        """Scan all rc-* directories and return snapshots."""
        if not self._artifacts.exists():
            return []

        runs: list[RunSnapshot] = []
        for d in sorted(self._artifacts.iterdir(), reverse=True):
            if d.is_dir() and d.name.startswith("rc-"):
                try:
                    snap = self._collect_run(d)
                    runs.append(snap)
                except Exception as exc:
                    logger.debug("Failed to collect %s: %s", d, exc)
        return runs

    def collect_run(self, run_dir: str | Path) -> RunSnapshot:
        """Collect a single run."""
        return self._collect_run(Path(run_dir))

    def _collect_run(self, run_dir: Path) -> RunSnapshot:
        view = read_run_status(run_dir)
        snap = RunSnapshot(
            run_id=run_dir.name,
            path=str(run_dir),
            status=view.status.value,
            current_stage=view.current_stage or 0,
            current_stage_name=view.current_stage_name,
            start_time=view.start_time,
            is_active=view.is_live,
            topic=view.topic,
            error=view.last_error or "",
            stage_statuses={str(k): v for k, v in view.stage_statuses.items()},
        )
        start = _parse_time(view.start_time)
        if start is not None:
            snap.elapsed_sec = (datetime.now(UTC) - start).total_seconds()

        # --- stage directories ---
        snap.stages_completed = sorted(
            d.name
            for d in run_dir.iterdir()
            if d.is_dir() and d.name.startswith("stage-") and not _is_archived_stage_path(d)
        )

        # --- experiment metrics (results.json) ---
        for results_path in run_dir.rglob("results.json"):
            if _is_archived_stage_path(results_path):
                continue
            try:
                with results_path.open() as f:
                    snap.metrics = json.load(f)
                break
            except Exception:
                pass

        # --- last log lines ---
        log_path = run_dir / "pipeline.log"
        if log_path.exists():
            try:
                lines = log_path.read_text(errors="replace").splitlines()
                snap.last_log_lines = lines[-self._max_log_lines :]
            except Exception:
                pass

        return snap
