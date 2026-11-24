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


def test_price_table_wins_over_reported_cost() -> None:
    priced = CostTracker().record_from_llm_response("anthropic/claude-sonnet-4.5", 1_000_000, 0)

    again = CostTracker().record_from_llm_response(
        "anthropic/claude-sonnet-4.5", 1_000_000, 0, reported_cost=99.0
    )

    assert again.cost_usd == pytest.approx(priced.cost_usd)


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


def test_pipeline_start_resets_the_global_tracker(monkeypatch: pytest.MonkeyPatch) -> None:
    from berb.llm import cost_tracker as ct
    from berb.pipeline import runner

    tracker = CostTracker()
    _spend(tracker, 9.0)
    monkeypatch.setattr(ct, "_tracker", tracker)

    runner._reset_run_cost_tracker(pivot_depth=0)

    assert tracker.total_usd() == 0.0


def test_pivot_recursion_keeps_the_runs_spend(monkeypatch: pytest.MonkeyPatch) -> None:
    from berb.llm import cost_tracker as ct
    from berb.pipeline import runner

    tracker = CostTracker()
    _spend(tracker, 9.0)
    monkeypatch.setattr(ct, "_tracker", tracker)

    runner._reset_run_cost_tracker(pivot_depth=1)

    assert tracker.total_usd() == pytest.approx(9.0)


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
