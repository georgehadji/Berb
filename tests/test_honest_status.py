"""Server and CLI honesty (wave 5: SF-1/W2, SF-2, SF-13, SF-27, BR-31).

SF-1/W2  one run-status read model: the dashboard, MCP and chat read what the
         runner actually writes, not keys that were never written.
SF-2     /pipeline/start honours project.mode and stop_on_gate; a gate-blocked
         run is not "completed"; /stop on a finished run is 409; stop is
         cooperative, so a new start waits for the running stage to end.
SF-13    `berb literature` does not crash on the frozen config; the unbuilt
         workflow commands exit non-zero instead of pretending.
SF-27    `berb wizard` with a blank topic does not overwrite the output file.
BR-31    `berb trends` feeds read Paper objects and the real S2 search.
See tasks/implicit_state_machines_plan.md (W2) and tasks/state_machines_p2_results.md.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from berb.pipeline.checkpoint import write_checkpoint, write_heartbeat
from berb.pipeline.run_status import RunStatus, read_run_status
from berb.pipeline.stages import (
    EventStore,
    Stage,
    StageStatus,
    StageTransitionEvent,
    TransitionEvent,
)
from berb.pipeline.summary import write_pipeline_summary

_CONFIG = {
    "project": {"name": "t"},
    "research": {"topic": "t"},
    "runtime": {"timezone": "UTC"},
    "notifications": {"channel": "console"},
    "knowledge_base": {"root": "kb"},
    "llm": {"provider": "openai-compatible", "base_url": "http://x", "api_key_env": "T"},
}


def _config(**project: str):
    from berb.config import RCConfig

    return RCConfig.from_dict({**_CONFIG, "project": {"name": "t", **project}}, check_paths=False)


# --- fixtures: run directories as the runner writes them ---------------------


def _event(run_id: str, stage: Stage, to: StageStatus, **meta: Any) -> StageTransitionEvent:
    return StageTransitionEvent(
        run_id=run_id,
        from_stage=stage,
        to_stage=stage,
        from_status=StageStatus.PENDING if to == StageStatus.RUNNING else StageStatus.RUNNING,
        to_status=to,
        event=TransitionEvent.START if to == StageStatus.RUNNING else TransitionEvent.SUCCEED,
        metadata=meta,
    )


_SUFFIX = {"pending": "aaaaaa", "running": "bbbbbb", "done": "cccccc", "failed": "dddddd"}


def _make_run(root: Path, state: str) -> Path:
    run_id = f"rc-20260315-120000-{_SUFFIX.get(state, 'eeeeee')}"
    run_dir = root / run_id
    run_dir.mkdir(parents=True)
    if state == "pending":
        return run_dir
    (run_dir / "topic.txt").write_text("graph transformers", encoding="utf-8")
    store = EventStore(run_id=run_id, storage_path=str(run_dir / "event_log.json"))
    for stage in (Stage.TOPIC_INIT, Stage.PROBLEM_DECOMPOSE):
        store.append(_event(run_id, stage, StageStatus.RUNNING))
        store.append(_event(run_id, stage, StageStatus.DONE))
        write_checkpoint(run_dir, stage, run_id)
        write_heartbeat(run_dir, stage, run_id)
    last = Stage.SEARCH_STRATEGY
    store.append(_event(run_id, last, StageStatus.RUNNING))
    final = {
        "running": None,
        "done": StageStatus.DONE,
        "failed": StageStatus.FAILED,
        "blocked_approval": StageStatus.BLOCKED_APPROVAL,
    }[state]
    if final is not None:
        store.append(_event(run_id, last, final, error="boom" if state == "failed" else None))
        write_pipeline_summary(
            run_dir,
            {
                "run_id": run_id,
                "final_stage": int(last),
                "final_status": final.value,
                "generated": "2099-01-01T00:00:00+00:00",
            },
        )
    return run_dir


STATES = ["pending", "running", "done", "failed", "blocked_approval"]


@pytest.mark.parametrize("state", STATES)
def test_read_run_status_reports_the_real_state(tmp_path: Path, state: str):
    view = read_run_status(_make_run(tmp_path, state))

    assert view.status == RunStatus(state)
    if state != "pending":
        assert view.current_stage == int(Stage.SEARCH_STRATEGY)
        assert view.current_stage_name == "SEARCH_STRATEGY"
        assert view.topic == "graph transformers"
    assert view.is_live == (state == "running")


def test_failed_run_carries_its_error(tmp_path: Path):
    assert read_run_status(_make_run(tmp_path, "failed")).last_error == "boom"


def test_resumed_run_is_running_not_its_old_summary(tmp_path: Path):
    run_dir = _make_run(tmp_path, "done")
    (run_dir / "pipeline_summary.json").write_text(
        json.dumps({"final_status": "done", "generated": "2000-01-01T00:00:00+00:00"})
    )
    store = EventStore(run_id=run_dir.name, storage_path=str(run_dir / "event_log.json"))
    store.append(_event(run_dir.name, Stage.LITERATURE_COLLECT, StageStatus.RUNNING))

    assert read_run_status(run_dir).status == RunStatus.RUNNING


def test_stopped_summary_reads_as_stopped(tmp_path: Path):
    run_dir = _make_run(tmp_path, "done")
    summary = json.loads((run_dir / "pipeline_summary.json").read_text())
    summary["final_status"] = "stopped"
    (run_dir / "pipeline_summary.json").write_text(json.dumps(summary))

    assert read_run_status(run_dir).status == RunStatus.STOPPED


@pytest.mark.parametrize("state", STATES)
def test_every_surface_agrees(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, state: str):
    """Dashboard collector, MCP and chat show the read model's status."""
    from berb.dashboard.collector import DashboardCollector
    from berb.mcp.server import BerbMCPServer
    from berb.server.dialog import router

    run_dir = _make_run(tmp_path / "artifacts", state)
    expected = read_run_status(run_dir)

    snap = DashboardCollector(artifacts_dir=str(tmp_path / "artifacts")).collect_run(run_dir)
    assert (snap.status, snap.current_stage, snap.is_active) == (
        expected.status.value,
        expected.current_stage or 0,
        expected.is_live,
    )

    monkeypatch.chdir(tmp_path)
    mcp = asyncio.run(BerbMCPServer()._handle_get_status({"run_id": run_dir.name}))
    assert mcp["run_status"] == expected.status.value

    chat = asyncio.run(router._handle_status("status?", None))  # type: ignore[arg-type]
    assert expected.status.value in chat


# --- SF-2: the HTTP pipeline routes ------------------------------------------


@pytest.fixture
def api(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from berb.server.app import create_app
    from berb.server.routes import pipeline as routes

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(routes, "_active_run", None)
    monkeypatch.setattr(routes, "_run_task", None)
    return create_app(_config(mode="semi-auto")), routes


def _result(stage: Stage, status: StageStatus):
    from berb.pipeline._helpers import StageResult

    return StageResult(stage=stage, status=status, artifacts=())


async def _call(app: Any, method: str, path: str, **kw: Any):
    from httpx import ASGITransport, AsyncClient

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        return await getattr(ac, method)(path, **kw)


async def test_start_without_auto_approve_follows_project_mode(api, monkeypatch):
    app, routes = api
    seen: dict[str, Any] = {}

    async def fake_execute(**kw: Any):
        seen.update(kw)
        return [_result(Stage.LITERATURE_SCREEN, StageStatus.BLOCKED_APPROVAL)]

    monkeypatch.setattr("berb.pipeline.runner.execute_pipeline", fake_execute)
    resp = await _call(app, "post", "/api/pipeline/start", json={"topic": "x"})
    assert resp.status_code == 200
    await routes._run_task

    assert seen["auto_approve_gates"] is False
    assert seen["stop_on_gate"] is True
    status = (await _call(app, "get", "/api/pipeline/status")).json()
    assert status["status"] == "blocked_approval"
    assert "--resume" in status["hint"] and "--auto-approve" in status["hint"]


async def test_stop_on_a_finished_run_is_409_and_keeps_its_status(api, monkeypatch):
    app, routes = api

    async def fake_execute(**kw: Any):
        return [_result(Stage.TOPIC_INIT, StageStatus.DONE)]

    monkeypatch.setattr("berb.pipeline.runner.execute_pipeline", fake_execute)
    await _call(app, "post", "/api/pipeline/start", json={"topic": "x", "auto_approve": True})
    await routes._run_task

    assert (await _call(app, "post", "/api/pipeline/stop")).status_code == 409
    assert (await _call(app, "get", "/api/pipeline/status")).json()["status"] == "completed"


async def test_stop_is_cooperative_and_blocks_a_new_start_until_it_ends(api, monkeypatch):
    app, routes = api

    async def fake_execute(**kw: Any):
        while not kw["stop_event"].is_set():
            await asyncio.sleep(0.005)
        # Like the runner: a stop before the last level records "stopped".
        write_pipeline_summary(kw["run_dir"], {"final_status": "stopped"})
        return [_result(Stage.TOPIC_INIT, StageStatus.DONE)]

    monkeypatch.setattr("berb.pipeline.runner.execute_pipeline", fake_execute)
    await _call(app, "post", "/api/pipeline/start", json={"topic": "x"})

    stop = await _call(app, "post", "/api/pipeline/stop")
    assert stop.json()["status"] == "stopping"
    again = await _call(app, "post", "/api/pipeline/start", json={"topic": "y"})
    assert again.status_code == 409

    await routes._run_task
    assert (await _call(app, "get", "/api/pipeline/status")).json()["status"] == "stopped"


async def test_status_route_adds_the_run_status_view(api, monkeypatch):
    app, routes = api

    async def fake_execute(**kw: Any):
        return [_result(Stage.TOPIC_INIT, StageStatus.DONE)]

    monkeypatch.setattr("berb.pipeline.runner.execute_pipeline", fake_execute)
    await _call(app, "post", "/api/pipeline/start", json={"topic": "x", "auto_approve": True})
    await routes._run_task

    body = (await _call(app, "get", "/api/pipeline/status")).json()
    assert body["status"] == "completed"
    assert "stage_statuses" in body["run_status"]


async def test_runner_honours_a_stop_event_between_levels(tmp_path: Path, monkeypatch):
    import threading

    from berb.adapters import AdapterBundle
    from berb.pipeline import runner

    stop = threading.Event()
    ran: list[Stage] = []

    def fake_stage(stage: Stage, **kw: Any):
        ran.append(stage)
        stop.set()
        return _result(stage, StageStatus.DONE)

    monkeypatch.setattr(runner, "execute_stage", fake_stage)
    await runner.execute_pipeline(
        run_dir=tmp_path,
        run_id="rc-stop",
        config=_config(),
        adapters=AdapterBundle(),
        stop_event=stop,
    )

    assert ran == [Stage.TOPIC_INIT]
    summary = json.loads((tmp_path / "pipeline_summary.json").read_text())
    assert summary["final_status"] == "stopped"
    assert read_run_status(tmp_path).status == RunStatus.STOPPED


# --- SF-13 / SF-27: CLI commands that pretend --------------------------------


@pytest.mark.parametrize("command", ["write", "experiment", "review", "rebuttal"])
def test_unbuilt_workflow_commands_exit_nonzero(command: str, capsys):
    from berb import cli

    args = argparse.Namespace(
        config=None,
        topic="t",
        data=None,
        figures=None,
        manuscript="m.pdf",
        reviews="r.txt",
        venue=None,
        plan=None,
        code=None,
    )
    assert getattr(cli, f"cmd_{command}")(args) != 0
    assert "not implemented" in capsys.readouterr().err


def test_literature_command_sets_topic_and_stops_after_stage_8(tmp_path, monkeypatch):
    from berb import cli

    seen: dict[str, Any] = {}

    async def fake_execute(**kw: Any):
        seen.update(kw)
        return []

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("berb.config.load_config", lambda *_a, **_k: _config())
    monkeypatch.setattr("berb.adapters.create_adapters", lambda *_a, **_k: None)
    monkeypatch.setattr("berb.pipeline.runner.execute_pipeline", fake_execute)
    monkeypatch.setattr(cli, "_resolve_upload_args", lambda _a: [])
    args = argparse.Namespace(config="c.yaml", topic="new topic")

    assert cli.cmd_literature(args) == 0
    assert seen["config"].research.topic == "new topic"
    assert seen["to_stage"] == Stage.HYPOTHESIS_GEN


def test_wizard_blank_topic_keeps_the_output_file(tmp_path, monkeypatch):
    from berb import cli
    from berb.wizard import quickstart

    out = tmp_path / "config.yaml"
    out.write_text("research:\n  topic: keep me\n", encoding="utf-8")
    monkeypatch.setattr(quickstart.QuickStartWizard, "run_interactive", lambda self: {})

    assert cli.cmd_wizard(argparse.Namespace(output=str(out))) != 0
    assert "keep me" in out.read_text(encoding="utf-8")


# --- BR-31: trends feeds -----------------------------------------------------


def test_trend_feeds_read_paper_objects(monkeypatch):
    from berb.literature.models import Author, Paper
    from berb.trends.feeds import FeedManager

    def papers(source: str):
        return lambda *a, **k: [
            Paper(
                paper_id=source,
                title=f"A {source} paper",
                authors=(Author(name="Ada"),),
                year=2026,
                abstract="abs",
                url="http://p",
                citation_count=3,
                arxiv_id="2601.00001",
            )
        ]

    monkeypatch.setattr("berb.literature.arxiv_client.search_arxiv", papers("arxiv"))
    monkeypatch.setattr("berb.literature.semantic_scholar.search_semantic_scholar", papers("s2"))
    monkeypatch.setattr("berb.literature.openalex_client.search_openalex", papers("oa"))

    fm = FeedManager(sources=("arxiv", "semantic_scholar", "openalex"))
    found = fm.fetch_recent_papers(["ml"], max_papers=10)

    assert {p["source"] for p in found} == {"arxiv", "semantic_scholar", "openalex"}
    assert all(p["authors"] == ["Ada"] for p in found)


async def test_run_status_endpoint_serves_the_read_model(api, tmp_path):
    app, _ = api
    run_dir = _make_run(tmp_path / "artifacts", "blocked_approval")

    body = (await _call(app, "get", f"/api/runs/{run_dir.name}/status")).json()

    assert body["status"] == "blocked_approval"
    assert body["stage_statuses"]["3"] == "blocked_approval"


# --- review fixes --------------------------------------------------------------


def _dead_pid() -> int:
    import subprocess
    import sys

    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait()
    return proc.pid


def _set_heartbeat_pid(run_dir: Path, pid: int) -> None:
    hb = json.loads((run_dir / "heartbeat.json").read_text())
    hb["pid"] = pid
    (run_dir / "heartbeat.json").write_text(json.dumps(hb))


def test_run_interrupted_mid_stage_reads_as_stopped(tmp_path: Path):
    run_dir = _make_run(tmp_path, "running")
    _set_heartbeat_pid(run_dir, _dead_pid())

    view = read_run_status(run_dir)

    assert view.status == RunStatus.STOPPED
    assert not view.is_live


def test_stage_running_in_a_live_process_reads_as_running(tmp_path: Path):
    import os

    run_dir = _make_run(tmp_path, "running")
    _set_heartbeat_pid(run_dir, os.getpid())

    assert read_run_status(run_dir).status == RunStatus.RUNNING


def test_unreadable_event_log_does_not_raise(tmp_path: Path):
    run_dir = _make_run(tmp_path, "done")
    (run_dir / "event_log.json").unlink()
    (run_dir / "event_log.json").mkdir()  # read_text raises an OSError

    assert read_run_status(run_dir).status == RunStatus.DONE


def test_legacy_checkpoint_stage_out_of_range_does_not_raise(tmp_path: Path):
    run_dir = tmp_path / "rc-20260315-120000-ffffff"
    run_dir.mkdir()
    (run_dir / "checkpoint.json").write_text(json.dumps({"last_completed_stage": 99}))

    view = read_run_status(run_dir)

    assert view.current_stage is None and view.current_stage_name == ""


async def test_stop_after_the_last_stage_leaves_the_run_completed(tmp_path: Path, monkeypatch):
    import threading

    from berb.adapters import AdapterBundle
    from berb.pipeline import runner

    stop = threading.Event()

    def fake_stage(stage: Stage, **kw: Any):
        if stage == Stage.CITATION_VERIFY:
            stop.set()
        return _result(stage, StageStatus.DONE)

    monkeypatch.setattr(runner, "execute_stage", fake_stage)
    await runner.execute_pipeline(
        run_dir=tmp_path,
        run_id="rc-late",
        config=_config(),
        adapters=AdapterBundle(),
        stop_event=stop,
    )

    summary = json.loads((tmp_path / "pipeline_summary.json").read_text())
    assert summary["final_status"] == "done"


def test_discovery_slices_receive_the_stop_event(tmp_path: Path, monkeypatch):
    import threading

    from berb.pipeline import discovery

    seen: dict[str, Any] = {}

    async def fake_execute(**kw: Any):
        seen.update(kw)
        return []

    monkeypatch.setattr("berb.pipeline.runner.execute_pipeline", fake_execute)
    stop = threading.Event()
    run = discovery.make_stage_slice_executor(
        run_dir=tmp_path, run_id="rc-d", config=_config(), adapters=None, stop_event=stop
    )
    asyncio.run(run("task", 1))

    assert seen["stop_event"] is stop


async def test_broadcaster_reports_stage_done_and_status_change_in_one_poll(tmp_path: Path):
    from berb.dashboard.broadcaster import DashboardBroadcaster
    from berb.dashboard.collector import DashboardCollector
    from berb.server.websocket.events import EventType

    sent: list[Any] = []

    class _Manager:
        async def broadcast(self, event: Any) -> None:
            sent.append(event.type)

    artifacts = tmp_path / "artifacts"
    run_dir = _make_run(artifacts, "running")
    _set_heartbeat_pid(run_dir, __import__("os").getpid())
    b = DashboardBroadcaster(_Manager(), DashboardCollector(artifacts_dir=str(artifacts)))  # type: ignore[arg-type]
    await b.tick()
    sent.clear()

    store = EventStore(run_id=run_dir.name, storage_path=str(run_dir / "event_log.json"))
    store.append(_event(run_dir.name, Stage.SEARCH_STRATEGY, StageStatus.FAILED, error="x"))
    await b.tick()

    assert EventType.STAGE_COMPLETE not in sent  # it failed, it did not complete
    assert EventType.RUN_STATUS_CHANGED in sent


def test_stages_completed_skips_rollback_archives(tmp_path: Path):
    from berb.dashboard.collector import DashboardCollector

    run_dir = _make_run(tmp_path, "done")
    for name in ("stage-08", "stage-08_v1", "stage-08_v2"):
        (run_dir / name).mkdir()

    snap = DashboardCollector(artifacts_dir=str(tmp_path)).collect_run(run_dir)

    assert snap.stages_completed == ["stage-08"]
