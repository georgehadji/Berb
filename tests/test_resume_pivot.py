"""Resume and pivot correctness (wave 4: PC-5/SI-03, PC-6, PC-10, SI-04).

PC-5/SI-03  after a PIVOT, readers must take the live stage-NN over its
            archived stage-NN_vK copy.
PC-6        a finished run resumes as "complete", not from stage 1; resume
            starts at the first stage not done, not after the last one written.
PC-10       stage 14 reads stage 13's selection_bias.json, so they cannot share
            a DAG level.
SI-04       a negated or prefix keyword must not override the real decision.
See tasks/implicit_state_machines_plan.md wave 4.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from berb.pipeline import checkpoint as cp
from berb.pipeline._io_helpers import _find_prior_file, _read_prior_artifact
from berb.pipeline.resolution import resolve_stage_order
from berb.pipeline.stages import Stage

# --- PC-5 / SI-03 -------------------------------------------------------


@pytest.mark.parametrize(
    ("stage_dir", "filename"),
    [
        ("stage-08", "hypotheses.md"),
        ("stage-08", "hypothesis_state.json"),
        ("stage-13", "refinement_log.json"),
        ("stage-14", "analysis.md"),
    ],
)
def test_live_stage_dir_wins_over_its_archive(tmp_path: Path, stage_dir: str, filename: str):
    for name, text in (
        (stage_dir, "NEW"),
        (f"{stage_dir}_v1", "OLD1"),
        (f"{stage_dir}_v2", "OLD2"),
    ):
        (tmp_path / name).mkdir()
        (tmp_path / name / filename).write_text(text, encoding="utf-8")

    assert _read_prior_artifact(tmp_path, filename) == "NEW"


def test_newest_archive_wins_when_no_live_dir(tmp_path: Path):
    for name in ("stage-08_v2", "stage-08_v10"):
        (tmp_path / name).mkdir()
        (tmp_path / name / "hypotheses.md").write_text(name, encoding="utf-8")

    assert _read_prior_artifact(tmp_path, "hypotheses.md") == "stage-08_v10"


def test_higher_stage_number_still_wins(tmp_path: Path):
    for name in ("stage-08", "stage-09_v1"):
        (tmp_path / name).mkdir()
        (tmp_path / name / "x.md").write_text(name, encoding="utf-8")

    found = _find_prior_file(tmp_path, "x.md")
    assert found is not None and found.parent.name == "stage-09_v1"


def test_rollback_also_archives_stale_repair_attempts(tmp_path: Path):
    from berb.pipeline.iterative import _version_rollback_stages

    for name in ("stage-14", "stage-14_repair_v1"):
        (tmp_path / name).mkdir()
    _version_rollback_stages(tmp_path, Stage.HYPOTHESIS_GEN, attempt=1)

    assert not (tmp_path / "stage-14_repair_v1").exists()
    assert (tmp_path / "stage-14_v1").is_dir()


# --- PC-6 ---------------------------------------------------------------


def _write_all(run_dir: Path, stages) -> None:
    for stage in stages:
        cp.write_checkpoint(run_dir, stage, "run")


def test_finished_run_reads_as_complete(tmp_path: Path):
    _write_all(tmp_path, resolve_stage_order())

    state = cp.load_checkpoint(tmp_path)

    assert state is not None and state.complete
    assert state.next_stage is None


def test_resume_starts_at_the_first_stage_not_done(tmp_path: Path):
    order = list(resolve_stage_order())
    ten = order.index(Stage(10))
    # Stage 10 failed in a parallel level; stage 11 finished and wrote last.
    _write_all(tmp_path, order[:ten] + [order[ten + 1]])

    assert cp.read_checkpoint(tmp_path) == Stage(10)


def test_legacy_checkpoint_without_completed_set_still_resumes(tmp_path: Path):
    legacy = {"last_completed_stage": 5, "last_completed_name": "LITERATURE_SCREEN", "run_id": "r"}
    (tmp_path / "checkpoint.json").write_text(json.dumps(legacy), encoding="utf-8")

    assert cp.read_checkpoint(tmp_path) == Stage(6)


def test_unreadable_checkpoint_is_reported_not_treated_as_fresh(tmp_path: Path):
    (tmp_path / "checkpoint.json").write_text("{not json", encoding="utf-8")

    state = cp.load_checkpoint(tmp_path)

    assert state is not None and state.unreadable


def test_rollback_rewinds_completed_stages(tmp_path: Path):
    _write_all(tmp_path, resolve_stage_order()[:15])  # through RESEARCH_DECISION

    cp.forget_completed(
        tmp_path, range(int(Stage.HYPOTHESIS_GEN), int(Stage.RESEARCH_DECISION) + 1)
    )

    assert cp.read_checkpoint(tmp_path) == Stage.HYPOTHESIS_GEN


# --- PC-10 --------------------------------------------------------------


def test_result_analysis_runs_after_iterative_refine():
    from berb.pipeline.runner import _build_dag_levels

    levels = _build_dag_levels(tuple(resolve_stage_order()))
    level_of = {s: i for i, level in enumerate(levels) for s in level}

    assert level_of[Stage.RESULT_ANALYSIS] > level_of[Stage.ITERATIVE_REFINE]


def test_every_stage_input_is_produced_upstream():
    """A stage's declared input files must come from a transitive dependency."""
    from berb.pipeline.contracts import CONTRACTS

    def upstream(stage: Stage) -> set[Stage]:
        seen: set[Stage] = set()
        todo = list(CONTRACTS[stage].depends_on)
        while todo:
            s = todo.pop()
            if s not in seen:
                seen.add(s)
                todo.extend(CONTRACTS[s].depends_on)
        return seen

    producer = {f: s for s, c in CONTRACTS.items() for f in c.output_files}
    missing = [
        (stage.name, f, producer[f].name)
        for stage, c in CONTRACTS.items()
        for f in c.input_files
        if f in producer and producer[f] != stage and producer[f] not in upstream(stage)
    ]
    assert missing == []


# --- SI-04 --------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "## Decision\nPIVOT is not warranted; the results hold up.\n## Justification\nok",
        "## Decision\nPROCEED with caution.\nRefinements to the ablation are optional.",
        "## Decision\nWe see no reason to PIVOT.\n",
    ],
)
def test_negated_or_prefix_keyword_does_not_override_proceed(text: str):
    from berb.pipeline.stage_impls._analysis import _parse_decision

    assert _parse_decision(text) == "proceed"


def test_later_clause_decision_is_found():
    from berb.pipeline.stage_impls._analysis import _parse_decision

    text = "## Decision\nWe should not PROCEED; PIVOT to a new hypothesis."
    assert _parse_decision(text) == "pivot"
