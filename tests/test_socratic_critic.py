"""berb/reasoning/socratic.py: a failed falsification critic is not a pass (BR-14)."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from berb.reasoning.socratic import CriticUnavailableError, FalsificationCritic


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
