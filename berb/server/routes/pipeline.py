"""Pipeline control API routes."""

from __future__ import annotations

import asyncio
import json
import logging
import re as _re
import threading
from datetime import UTC
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

_RUN_ID_RE = _re.compile(r"^rc-\d{8}-\d{6}-[a-f0-9]+$")


def _validated_run_dir(run_id: str) -> Path:
    """Validate run_id format and return the run directory path."""
    if not _RUN_ID_RE.match(run_id):
        raise HTTPException(status_code=400, detail=f"Invalid run_id format: {run_id}")
    run_dir = Path("artifacts") / run_id
    # Ensure resolved path is under artifacts/
    if not run_dir.resolve().is_relative_to(Path("artifacts").resolve()):
        raise HTTPException(status_code=400, detail=f"Invalid run_id: {run_id}")
    return run_dir


router = APIRouter(prefix="/api", tags=["pipeline"])


class PipelineStartRequest(BaseModel):
    """Request body for starting a pipeline run."""

    topic: str | None = None
    config_overrides: dict[str, Any] | None = None
    auto_approve: bool | None = None
    """None defers to ``project.mode`` (only ``full-auto`` approves gates)."""
    uploaded_file_paths: list[str] = []
    """Path(s) to uploaded PDFs/data files to include in the pipeline."""


class PipelineStartResponse(BaseModel):
    """Response after starting a pipeline."""

    run_id: str
    status: str
    output_dir: str


# In-memory tracking of the active run (single-tenant MVP)
_active_run: dict[str, Any] | None = None
_run_task: asyncio.Task[Any] | None = None


def _get_app_state() -> dict[str, Any]:
    """Get shared application state (set by app.py)."""
    from berb.server.app import _app_state

    return _app_state


@router.post("/pipeline/start", response_model=PipelineStartResponse)
async def start_pipeline(req: PipelineStartRequest) -> PipelineStartResponse:
    """Start a new pipeline run."""
    global _active_run, _run_task

    if _active_run and _active_run.get("status") in ("running", "stopping"):
        raise HTTPException(status_code=409, detail="A pipeline is already running")

    state = _get_app_state()
    config = state["config"]

    if req.topic:
        import dataclasses

        new_research = dataclasses.replace(config.research, topic=req.topic)
        config = dataclasses.replace(config, research=new_research)

    if req.uploaded_file_paths:
        import dataclasses

        new_research = dataclasses.replace(
            config.research,
            uploaded_file_paths=tuple(req.uploaded_file_paths),
        )
        config = dataclasses.replace(config, research=new_research)
        logger.info(
            "Pipeline start: including %d uploaded file(s)",
            len(req.uploaded_file_paths),
        )

    import hashlib
    from datetime import datetime

    ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    topic_hash = hashlib.sha256(config.research.topic.encode()).hexdigest()[:6]
    run_id = f"rc-{ts}-{topic_hash}"
    run_dir = _validated_run_dir(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    run: dict[str, Any] = {
        "run_id": run_id,
        "status": "running",
        "output_dir": str(run_dir),
        "topic": config.research.topic,
    }
    _active_run = run
    stop_event = threading.Event()
    run["_stop_event"] = stop_event

    async def _run_in_background() -> None:
        try:
            from berb.adapters import AdapterBundle
            from berb.pipeline import runner

            kb_root = Path(config.knowledge_base.root) if config.knowledge_base.root else None
            if kb_root:
                kb_root.mkdir(parents=True, exist_ok=True)

            auto_approve, stop_on_gate = runner.gate_policy(config.project.mode, req.auto_approve)
            results = await runner.execute_pipeline(
                run_dir=run_dir,
                run_id=run_id,
                config=config,
                adapters=AdapterBundle(),
                auto_approve_gates=auto_approve,
                stop_on_gate=stop_on_gate,
                skip_noncritical=True,
                kb_root=kb_root,
                reset_cost_tracker=True,
                stop_event=stop_event,
            )
            statuses = [r.status.value for r in results]
            run["stages_done"] = statuses.count("done")
            run["stages_failed"] = statuses.count("failed")
            # The runner's summary says whether the stop cut the run short; a
            # stop that lands after the last stage leaves it completed.
            if runner._summary_final_status(run_dir) == "stopped":
                run["status"] = "stopped"
            elif "blocked_approval" in statuses:
                run["status"] = "blocked_approval"
                # The web has no approval surface yet (D2), so say how to go on.
                run["hint"] = (
                    "Gate awaiting approval. To approve and continue: "
                    f"berb run --resume --output {run_dir} --auto-approve"
                )
            else:
                run["status"] = "completed" if run["stages_failed"] == 0 else "failed"
        except Exception as exc:
            logger.exception("Pipeline run failed")
            run["status"] = "failed"
            run["error"] = str(exc)

    _run_task = asyncio.create_task(_run_in_background())

    return PipelineStartResponse(
        run_id=run_id,
        status="running",
        output_dir=str(run_dir),
    )


@router.post("/pipeline/stop")
async def stop_pipeline() -> dict[str, str]:
    """Ask the running pipeline to stop after its current stage.

    Cooperative, not a cancel: a stage runs in a worker thread that
    cancelling the task would leave running, and a new start would then race
    it (SF-2). Status reads ``stopping`` until the stage ends, then ``stopped``.
    """
    if not _run_task or not _active_run:
        raise HTTPException(status_code=404, detail="No pipeline is running")
    if _active_run.get("status") != "running":
        raise HTTPException(
            status_code=409, detail=f"Pipeline is not running ({_active_run.get('status')})"
        )

    _active_run["_stop_event"].set()
    _active_run["status"] = "stopping"
    return {"status": "stopping"}


@router.get("/pipeline/status")
async def pipeline_status() -> dict[str, Any]:
    """Get current pipeline run status.

    The legacy ``status`` key keeps its vocabulary (D3); ``run_status`` is the
    on-disk read model shared with the dashboard, MCP and chat (W2).
    """
    if not _active_run:
        return {"status": "idle"}
    from berb.pipeline.run_status import read_run_status

    body = {k: v for k, v in _active_run.items() if not k.startswith("_")}
    body["run_status"] = read_run_status(Path(_active_run["output_dir"])).to_dict()
    return body


@router.get("/pipeline/stages")
async def pipeline_stages() -> dict[str, Any]:
    """Get the 23-stage pipeline definition."""
    from berb.pipeline.stages import Stage

    stages = []
    for s in Stage:
        stages.append(
            {
                "number": int(s),
                "name": s.name,
                "label": getattr(s, "label", s.name.replace("_", " ").title()),
                "phase": getattr(s, "phase", ""),
            }
        )
    return {"stages": stages}


@router.get("/runs")
async def list_runs() -> dict[str, Any]:
    """List historical pipeline runs from artifacts/ directory."""
    artifacts = Path("artifacts")
    runs: list[dict[str, Any]] = []
    if artifacts.exists():
        for d in sorted(artifacts.iterdir(), reverse=True):
            if d.is_dir() and d.name.startswith("rc-"):
                info: dict[str, Any] = {"run_id": d.name, "path": str(d)}
                # Try reading checkpoint
                ckpt = d / "checkpoint.json"
                if ckpt.exists():
                    try:
                        with ckpt.open() as f:
                            info["checkpoint"] = json.load(f)
                    except Exception:
                        pass
                runs.append(info)
    return {"runs": runs[:50]}  # limit to 50 most recent


@router.get("/runs/{run_id}")
async def get_run(run_id: str) -> dict[str, Any]:
    """Get details for a specific run."""
    run_dir = _validated_run_dir(run_id)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    info: dict[str, Any] = {"run_id": run_id, "path": str(run_dir)}

    ckpt = run_dir / "checkpoint.json"
    if ckpt.exists():
        try:
            with ckpt.open() as f:
                info["checkpoint"] = json.load(f)
        except Exception:
            pass

    # List stage directories
    from berb.pipeline._io_helpers import _is_archived_stage_path

    stage_dirs = sorted(
        d.name
        for d in run_dir.iterdir()
        if d.is_dir() and d.name.startswith("stage-") and not _is_archived_stage_path(d)
    )
    info["stages_completed"] = stage_dirs

    # Check for paper
    for pattern in ["paper.md", "paper.tex", "paper.pdf"]:
        found = list(run_dir.rglob(pattern))
        if found:
            info[f"has_{pattern.split('.')[1]}"] = True

    return info


@router.get("/runs/{run_id}/status")
async def get_run_status(run_id: str) -> dict[str, Any]:
    """The run-status read model for one run (W2), for the monitor view."""
    from berb.pipeline.run_status import read_run_status

    run_dir = _validated_run_dir(run_id)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return read_run_status(run_dir).to_dict()


@router.get("/runs/{run_id}/metrics")
async def get_run_metrics(run_id: str) -> dict[str, Any]:
    """Get experiment metrics for a run."""
    run_dir = _validated_run_dir(run_id)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    metrics: dict[str, Any] = {}
    results_file = run_dir / "results.json"
    if results_file.exists():
        try:
            with results_file.open() as f:
                metrics = json.load(f)
        except Exception:
            pass

    return {"run_id": run_id, "metrics": metrics}
