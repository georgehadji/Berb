"""Money accounting: spend is scoped, and an unpriced model is not free (LL-5, LL-8, EX-02).

LL-5   the process-global tracker must not carry one run's spend into the next.
LL-8   a model with no pricing entry must be reported, and provider-reported
       cost must be used instead of a silent $0.
EX-02  the search budget caps spend made by the search, not by the whole process.
See tasks/implicit_state_machines_plan.md wave 3.
"""

from __future__ import annotations

import logging

import pytest

from berb.experiment.search.policy import SearchConfig
from berb.experiment.search.runner import BudgetGovernor
from berb.llm.cost_tracker import CostEvent, CostTracker

_UNPRICED = "totally-unpriced-model-9000"


def _spend(tracker: CostTracker, usd: float) -> None:
    from datetime import UTC, datetime

    tracker.record(CostEvent(timestamp=datetime.now(UTC), model="m", cost_usd=usd))


# --- LL-8 ---------------------------------------------------------------


def test_unpriced_model_is_listed_in_the_report() -> None:
    tracker = CostTracker()

    tracker.record_from_llm_response(_UNPRICED, 1000, 1000)

    assert tracker.to_report()["unpriced_models"] == {_UNPRICED: 1}


def test_priced_model_is_not_listed_as_unpriced() -> None:
    tracker = CostTracker()

    tracker.record_from_llm_response("anthropic/claude-sonnet-4.5", 1000, 1000)

    assert tracker.to_report()["unpriced_models"] == {}


def test_provider_reported_cost_is_used_when_pricing_is_unknown() -> None:
    tracker = CostTracker()

    event = tracker.record_from_llm_response(_UNPRICED, 1000, 1000, reported_cost=0.42)

    assert event.cost_usd == pytest.approx(0.42)
    assert tracker.total_usd() == pytest.approx(0.42)
    assert tracker.to_report()["unpriced_models"] == {}  # it did get a real number


def test_reported_cost_wins_over_the_price_table() -> None:
    """usage.cost is exact (cache discounts included); the table is list price."""
    event = CostTracker().record_from_llm_response(
        "anthropic/claude-sonnet-4.5", 1_000_000, 0, reported_cost=0.25
    )

    assert event.cost_usd == pytest.approx(0.25)


def test_price_table_is_used_without_a_reported_cost() -> None:
    event = CostTracker().record_from_llm_response(
        "anthropic/claude-sonnet-4.5", 1_000_000, 0, reported_cost=0.0
    )

    assert event.cost_usd == pytest.approx(3.0)


def test_unpriced_call_warns_once_per_model(caplog: pytest.LogCaptureFixture) -> None:
    tracker = CostTracker()

    with caplog.at_level(logging.WARNING, logger="berb.llm.cost_tracker"):
        for _ in range(3):
            tracker.record_from_llm_response(_UNPRICED, 10, 10)

    assert sum("pricing_unknown" in r.getMessage() for r in caplog.records) == 1
    assert tracker.to_report()["unpriced_models"] == {_UNPRICED: 3}


def test_reset_clears_unpriced_models() -> None:
    tracker = CostTracker()
    tracker.record_from_llm_response(_UNPRICED, 10, 10)

    tracker.reset()

    assert tracker.to_report()["unpriced_models"] == {}


def test_llm_client_forwards_provider_reported_cost(monkeypatch: pytest.MonkeyPatch) -> None:
    import berb.llm.cost_tracker as ct
    from berb.llm.client import LLMClient, LLMResponse

    tracker = CostTracker()
    monkeypatch.setattr(ct, "_tracker", tracker)
    resp = LLMResponse(
        content="x", model=_UNPRICED, prompt_tokens=10, completion_tokens=10, cost=0.07
    )

    LLMClient._record_llm_cost(object.__new__(LLMClient), resp)

    assert tracker.total_usd() == pytest.approx(0.07)


# --- EX-02 --------------------------------------------------------------


def test_budget_ignores_spend_made_before_the_search_started() -> None:
    tracker = CostTracker()
    _spend(tracker, 6.0)  # earlier stages already used more than the $5 default

    governor = BudgetGovernor(SearchConfig(budget_usd=5.0), tracker)

    assert governor.check(nodes_completed=0) is None


def test_budget_still_trips_on_the_searchs_own_spend() -> None:
    tracker = CostTracker()
    _spend(tracker, 6.0)
    governor = BudgetGovernor(SearchConfig(budget_usd=5.0), tracker)

    _spend(tracker, 5.5)

    reason = governor.check(nodes_completed=0)
    assert reason is not None and "cost budget exceeded" in reason


def test_governor_reports_spend_since_baseline() -> None:
    tracker = CostTracker()
    _spend(tracker, 6.0)
    governor = BudgetGovernor(SearchConfig(budget_usd=5.0), tracker)

    _spend(tracker, 1.25)

    assert governor.spent_usd() == pytest.approx(1.25)


# --- LL-5 ---------------------------------------------------------------


class _StopAfterResetError(Exception):
    pass


async def _enter_pipeline(tmp_path, monkeypatch, **kw) -> None:
    """Run execute_pipeline just past its cost-tracker reset, then stop."""
    from berb.pipeline import runner

    def stop() -> None:
        raise _StopAfterResetError

    monkeypatch.setattr(runner, "configure_run_logging", stop)  # first call after the reset
    with pytest.raises(_StopAfterResetError):
        await runner.execute_pipeline(
            run_dir=tmp_path, run_id="r", config=None, adapters=None, **kw
        )


@pytest.fixture
def spent_tracker(monkeypatch: pytest.MonkeyPatch) -> CostTracker:
    from berb.llm import cost_tracker as ct

    tracker = CostTracker()
    _spend(tracker, 9.0)
    monkeypatch.setattr(ct, "_tracker", tracker)
    return tracker


async def test_run_entry_resets_the_global_tracker(tmp_path, monkeypatch, spent_tracker) -> None:
    await _enter_pipeline(tmp_path, monkeypatch, reset_cost_tracker=True)

    assert spent_tracker.total_usd() == 0.0


async def test_nested_entry_keeps_the_runs_spend(tmp_path, monkeypatch, spent_tracker) -> None:
    await _enter_pipeline(tmp_path, monkeypatch)

    assert spent_tracker.total_usd() == pytest.approx(9.0)


def _capture_execute_pipeline(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    import berb.pipeline.runner as runner_mod

    calls: list[dict] = []

    async def fake(**kw):
        calls.append(kw)
        return []

    monkeypatch.setattr(runner_mod, "execute_pipeline", fake)
    return calls


async def test_discovery_slice_does_not_reset_the_run(tmp_path, monkeypatch) -> None:
    from berb.pipeline.discovery import make_stage_slice_executor

    calls = _capture_execute_pipeline(monkeypatch)
    execute = make_stage_slice_executor(run_dir=tmp_path, run_id="r", config=None, adapters=None)

    await execute("a direction", 1)

    assert calls and not calls[0].get("reset_cost_tracker", False)


async def test_iterative_rerun_does_not_reset_the_run(tmp_path, monkeypatch) -> None:
    from berb.pipeline.iterative import execute_iterative_pipeline

    calls = _capture_execute_pipeline(monkeypatch)

    await execute_iterative_pipeline(
        run_dir=tmp_path, run_id="r", config=None, adapters=None, max_iterations=2
    )

    assert len(calls) == 2
    assert not any(c.get("reset_cost_tracker", False) for c in calls)


# --- per-node attribution -----------------------------------------------


async def test_concurrent_nodes_are_charged_only_their_own_calls() -> None:
    import asyncio

    from berb.llm.cost_tracker import node_attribution

    tracker = CostTracker()

    async def node(node_id: str, calls: int) -> None:
        with node_attribution(node_id):
            for _ in range(calls):
                await asyncio.sleep(0)  # interleave with the sibling
                tracker.record_from_llm_response(
                    _UNPRICED, 1, 1, node_id=node_id, reported_cost=1.0
                )

    await asyncio.gather(node("a", 1), node("b", 3))

    assert tracker.node_usd("a") == pytest.approx(1.0)
    assert tracker.node_usd("b") == pytest.approx(3.0)


def test_llm_client_charges_the_ambient_node(monkeypatch: pytest.MonkeyPatch) -> None:
    import berb.llm.cost_tracker as ct
    from berb.llm.client import LLMClient, LLMResponse

    tracker = CostTracker()
    monkeypatch.setattr(ct, "_tracker", tracker)
    resp = LLMResponse(content="x", model=_UNPRICED, prompt_tokens=1, completion_tokens=1, cost=0.5)

    with ct.node_attribution("n1"):
        LLMClient._record_llm_cost(object.__new__(LLMClient), resp)

    assert tracker.node_usd("n1") == pytest.approx(0.5)


# --- Perplexity ---------------------------------------------------------


def test_perplexity_spend_reaches_the_run_tracker(monkeypatch: pytest.MonkeyPatch) -> None:
    from types import SimpleNamespace

    import berb.llm.cost_tracker as ct
    import berb.metrics.reasoning_cost_tracker as rct
    from berb.llm.deep_query_client import DeepQueryClient

    tracker = CostTracker()
    monkeypatch.setattr(ct, "_tracker", tracker)
    monkeypatch.setattr(
        rct,
        "get_cost_tracker",
        lambda: SimpleNamespace(track=lambda **kw: SimpleNamespace(cost_usd=0.06)),
    )
    client = object.__new__(DeepQueryClient)
    client._run_id = "r"

    client._track_cost("sonar-pro", {"prompt_tokens": 10, "completion_tokens": 10}, 5)

    assert tracker.total_usd() == pytest.approx(0.06)  # search add-on included


def test_chat_completions_parser_reads_usage_cost() -> None:
    from berb.llm.client import LLMClient

    data = {
        "choices": [{"message": {"content": "x"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "cost": 0.031},
    }

    resp = LLMClient._parse_chat_completions_response(object.__new__(LLMClient), data, "m")

    assert resp.cost == pytest.approx(0.031)


@pytest.mark.parametrize("bad", [None, "n/a", -1, float("nan")])
def test_chat_completions_parser_ignores_unusable_cost(bad) -> None:
    from berb.llm.client import LLMClient

    data = {
        "choices": [{"message": {"content": "x"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "cost": bad},
    }

    resp = LLMClient._parse_chat_completions_response(object.__new__(LLMClient), data, "m")

    assert resp.cost == 0.0


async def test_search_nodes_record_their_own_cost_and_journal_total_is_exact(tmp_path) -> None:
    import asyncio

    from berb.experiment.search.policy import BestFirstDiversePolicy
    from berb.experiment.search.runner import SearchRunner
    from berb.llm.cost_tracker import current_node

    tracker = CostTracker()

    def generator(**_kw):
        # Stands in for LLMClient._record_llm_cost, which reads the ambient node.
        tracker.record_from_llm_response(_UNPRICED, 1, 1, node_id=current_node(), reported_cost=1.0)
        return [{"files": {}, "plan": "p", "origin": "draft"}]

    runner = SearchRunner(
        config=SearchConfig(enabled=True),
        policy=BestFirstDiversePolicy(seed=0),
        sandbox_factory=lambda: None,
        generator=generator,
        cost_tracker=tracker,
        metric_key="acc",
    )

    nodes = await asyncio.gather(*(runner._expand_one(None, "t", "p", {}) for _ in range(3)))

    assert [n.cost_usd for n in nodes] == [1.0, 1.0, 1.0]
    assert runner._journal.to_summary()["total_cost_usd"] == pytest.approx(3.0)
