"""ACPClient (LL-22): with ``llm.provider: acp`` every stage failed.

``_chat_with_prompt`` passes ``stage=`` on every call and ``ACPClient.chat``
rejected it; and ``__del__`` closed the shared named session whenever the
previous stage's client was collected.
"""

from __future__ import annotations

import gc
from unittest.mock import patch

from berb.llm.acp_client import ACPClient, ACPConfig


def _client() -> ACPClient:
    client = ACPClient(ACPConfig(agent="x", cwd="."))
    client._send_prompt = lambda prompt: "ok"  # type: ignore[method-assign]
    return client


def test_chat_accepts_the_stage_keyword() -> None:
    from berb.pipeline._prompt_helpers import _chat_with_prompt

    assert _chat_with_prompt(_client(), "s", "u").content == "ok"


def test_dropping_a_client_does_not_close_the_shared_session() -> None:
    client = _client()
    client._session_ready = True
    client._acpx = "acpx"

    with patch("berb.llm.acp_client.subprocess.run") as run:
        del client
        gc.collect()

    assert not any("close" in call.args[0] for call in run.call_args_list)


def test_atexit_closes_a_session_whose_client_was_collected() -> None:
    key = ("acpx", "/w", "x", "berb")
    ACPClient._open_sessions.add(key)
    ACPClient._live_instances.clear()

    with patch("berb.llm.acp_client.subprocess.run") as run:
        ACPClient._atexit_cleanup()

    assert any(call.args[0][-2:] == ["close", "berb"] for call in run.call_args_list)
    assert not ACPClient._open_sessions
