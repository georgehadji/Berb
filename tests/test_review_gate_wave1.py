"""Wave 1 of tasks/implicit_state_machines_plan.md: a failed check is not a pass.

RI-1  failed reviewer calls must not be averaged in as real 5.0 votes.
RI-3  a reviewer reply missing a field must not discard the whole ensemble.
BR-14 a failed falsification critic must not read as "hypothesis passed".
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from berb.reasoning.socratic import CriticUnavailableError, FalsificationCritic
from berb.review.ensemble import AutomatedReviewerEnsemble, Decision, Review

_FULL = {
    "scores": {
        "novelty": 3,
        "significance": 3,
        "technical_quality": 3,
        "experimental_rigor": 3,
        "clarity": 3,
        "reproducibility": 3,
    },
    "overall_score": 3.0,
    "decision": "reject",
    "strengths": ["a"],
    "weaknesses": ["b"],
    "questions_for_authors": ["c"],
    "confidence": 4,
    "detailed_feedback": "real feedback",
}


class _Chat:
    """Stub LLM: `chat` returns each queued reply; an Exception is raised."""

    def __init__(self, *replies):
        self._replies = list(replies)
        self.calls = 0

    def chat(self, *_a, **_kw):
        reply = self._replies[min(self.calls, len(self._replies) - 1)]
        self.calls += 1
        if isinstance(reply, Exception):
            raise reply
        return SimpleNamespace(content=reply if isinstance(reply, str) else json.dumps(reply))


def _real(ens: AutomatedReviewerEnsemble, persona_idx: int, **over) -> Review:
    return ens._parse_review_content(ens._personas[persona_idx], json.dumps({**_FULL, **over}))


# --- RI-1 ---------------------------------------------------------------


async def test_all_reviewers_failed_is_reported_as_no_real_reviews():
    ens = AutomatedReviewerEnsemble(None)
    reviews = await ens.review_paper("x.md", paper_text="t")
    meta = ens.area_chair_decision(reviews)

    assert not any(r.available for r in reviews)
    assert meta.n_real == 0
    assert meta.confidence == 0.0
    assert "strong agreement" not in meta.meta_review_text
    assert "no reviewer" in meta.meta_review_text.lower()


def test_one_real_reject_is_not_diluted_by_placeholders():
    ens = AutomatedReviewerEnsemble(None)
    placeholders = [ens._parse_review_content(p, "") for p in ens._personas[1:]]
    reviews = [_real(ens, 0), *placeholders]

    meta = ens.area_chair_decision(reviews)

    assert meta.n_real == 1
    assert meta.average_score == 3.0
    assert meta.consensus_decision is Decision.REJECT


def test_placeholders_do_not_inflate_agreement():
    ens = AutomatedReviewerEnsemble(None)
    reviews = [
        _real(ens, 0, overall_score=7.0, decision="accept"),
        _real(ens, 1, overall_score=7.0, decision="accept"),
        *[ens._parse_review_content(p, "") for p in ens._personas[2:]],
    ]
    meta = ens.area_chair_decision(reviews)

    assert meta.n_real == 2
    assert meta.average_score == 7.0
    assert any("unavailable" in line.lower() for line in meta.meta_review_text.splitlines())


# --- RI-3 ---------------------------------------------------------------


async def test_reply_missing_optional_fields_still_yields_real_reviews():
    reply = {k: v for k, v in _FULL.items() if k != "questions_for_authors"}
    ens = AutomatedReviewerEnsemble(_Chat(reply))

    reviews = await ens.review_paper("x.md", paper_text="t")

    assert len(reviews) == len(ens._personas)
    assert all(r.available for r in reviews)
    assert all(r.questions_for_authors == [] for r in reviews)


def test_non_numeric_score_and_confidence_degrade_per_field():
    ens = AutomatedReviewerEnsemble(None)
    review = _real(ens, 0, overall_score="n/a", confidence="high")

    assert review.available
    assert review.overall_score == 3.0  # mean of the six dimension scores
    assert 1 <= review.confidence <= 5


def test_unusable_reply_is_marked_unavailable_not_raised():
    ens = AutomatedReviewerEnsemble(None)
    review = ens._parse_review_content(ens._personas[0], json.dumps({"scores": "oops"}))

    assert review.available is False


# --- BR-14 --------------------------------------------------------------


async def test_critic_raises_when_llm_call_fails():
    critic = FalsificationCritic(llm_client=_Chat(RuntimeError("outage")))
    with pytest.raises(CriticUnavailableError):
        await critic.scrutinize("some hypothesis")


async def test_critic_raises_on_non_list_reply():
    critic = FalsificationCritic(llm_client=_Chat({"issues": []}))
    with pytest.raises(CriticUnavailableError):
        await critic.scrutinize("some hypothesis")


async def test_critic_raises_when_no_client():
    with pytest.raises(CriticUnavailableError):
        await FalsificationCritic().scrutinize("some hypothesis")


async def test_critic_empty_list_is_still_a_pass():
    critic = FalsificationCritic(llm_client=_Chat("[]"))
    assert await critic.scrutinize("some hypothesis") == []
