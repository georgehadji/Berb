"""ACPClient (LL-22): with ``llm.provider: acp`` every stage failed.

``_chat_with_prompt`` passes ``stage=`` on every call and ``ACPClient.chat``
rejected it; and ``__del__`` closed the shared named session whenever the
previous stage's client was collected.
"""

from __future__ import annotations

import gc
from unittest.mock import patch

import pytest

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


# W8: acpx transport. A fake ``acpx`` executable records argv and stdin, so
# these check the real command shapes and pipes without an agent.

_FAKE_ACPX = r"""
import json, os, sys
args = sys.argv[1:]
stdin = "" if "sessions" in args else sys.stdin.read()
with open(os.environ["FAKE_ACPX_LOG"], "a", encoding="utf-8") as f:
    f.write(json.dumps({"argv": args, "stdin": stdin}) + "\n")
if "sessions" in args:
    sys.exit(0)
once = os.environ.get("FAKE_ACPX_FAIL_ONCE", "")
if once and os.path.exists(once):
    os.remove(once)
    sys.stderr.write("no session")
    sys.exit(4)
code = int(os.environ.get("FAKE_ACPX_EXIT", "0"))
if code:
    sys.stderr.write("denied")
    sys.exit(code)
sys.stdout.write("answer:" + str(len(stdin)))
"""


def _fake_acpx(tmp_path, monkeypatch, **env: str):
    import json
    import os
    import stat
    import sys

    script = tmp_path / "fake_acpx.py"
    script.write_text(_FAKE_ACPX, encoding="utf-8")
    if sys.platform == "win32":
        exe = tmp_path / "acpx.cmd"
        exe.write_text(f'@"{sys.executable}" "{script}" %*\n', encoding="utf-8")
    else:
        exe = tmp_path / "acpx"
        exe.write_text(f"#!{sys.executable}\n" + _FAKE_ACPX, encoding="utf-8")
        exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    log = tmp_path / "calls.jsonl"
    monkeypatch.setenv("FAKE_ACPX_LOG", str(log))
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    def calls() -> list[dict]:
        if not os.path.exists(log):
            return []
        return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]

    return str(exe), calls


def _real_client(acpx: str, **kw) -> ACPClient:
    return ACPClient(ACPConfig(agent="codex", cwd=".", acpx_command=acpx, **kw))


def test_prompt_goes_on_stdin_with_quiet_output(tmp_path, monkeypatch) -> None:
    acpx, calls = _fake_acpx(tmp_path, monkeypatch)
    prompt = 'line one\nline two "quoted" & | <x>'

    answer = _real_client(acpx).chat([{"role": "user", "content": prompt}]).content

    assert answer == f"answer:{len(prompt)}"
    sent = [c for c in calls() if "sessions" not in c["argv"]]
    assert len(sent) == 1
    argv = sent[0]["argv"]
    assert sent[0]["stdin"] == prompt
    assert prompt not in argv
    assert argv[:3] == ["--approve-reads", "--format", "quiet"]
    assert argv[-4:] == ["-s", "berb", "--file", "-"]


def test_a_long_prompt_needs_no_temp_file(tmp_path, monkeypatch) -> None:
    acpx, calls = _fake_acpx(tmp_path, monkeypatch)
    prompt = "x" * 200_000

    assert _real_client(acpx).chat([{"role": "user", "content": prompt}]).content == (
        "answer:200000"
    )
    assert calls()[-1]["stdin"] == prompt


def test_permission_mode_is_passed_through(tmp_path, monkeypatch) -> None:
    acpx, calls = _fake_acpx(tmp_path, monkeypatch)

    _real_client(acpx, permission_mode="approve-all").chat([{"role": "user", "content": "hi"}])

    assert calls()[-1]["argv"][0] == "--approve-all"


def test_all_permissions_denied_says_which_setting_to_change(tmp_path, monkeypatch) -> None:
    acpx, _ = _fake_acpx(tmp_path, monkeypatch, FAKE_ACPX_EXIT="5")

    with pytest.raises(RuntimeError, match="llm.acp.permission_mode"):
        _real_client(acpx).chat([{"role": "user", "content": "hi"}])


def test_a_missing_session_is_recreated(tmp_path, monkeypatch) -> None:
    marker = tmp_path / "fail_once"
    marker.write_text("1")
    acpx, calls = _fake_acpx(tmp_path, monkeypatch, FAKE_ACPX_FAIL_ONCE=str(marker))

    assert _real_client(acpx).chat([{"role": "user", "content": "hi"}]).content == "answer:2"
    ensures = [c for c in calls() if "ensure" in c["argv"]]
    assert len(ensures) == 2


def test_an_old_acpx_says_to_upgrade(tmp_path, monkeypatch) -> None:
    acpx, _ = _fake_acpx(tmp_path, monkeypatch, FAKE_ACPX_EXIT="2")

    with pytest.raises(RuntimeError, match="upgrade acpx"):
        _real_client(acpx).chat([{"role": "user", "content": "hi"}])


def test_a_missing_acpx_binary_is_a_runtime_error(tmp_path) -> None:
    client = _real_client(str(tmp_path / "no-such-acpx"))
    client._session_ready = True

    with pytest.raises(RuntimeError, match="cannot run"):
        client.chat([{"role": "user", "content": "hi"}])


def test_prompts_from_several_threads_run_one_at_a_time() -> None:
    # The parallel writer calls chat() from threads; they share one session.
    import threading
    import time
    from concurrent.futures import ThreadPoolExecutor

    lock = threading.Lock()
    state = {"now": 0, "peak": 0}
    client = ACPClient(ACPConfig(agent="x", cwd=".", acpx_command="acpx"))
    client._session_ready = True

    def fake_cli(acpx: str, prompt: str) -> str:
        with lock:
            state["now"] += 1
            state["peak"] = max(state["peak"], state["now"])
        time.sleep(0.05)
        with lock:
            state["now"] -= 1
        return "ok"

    client._send_prompt_cli = fake_cli  # type: ignore[method-assign]
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda _: client.chat([{"role": "user", "content": "s"}]), range(3)))

    assert state["peak"] == 1


@pytest.mark.e2e
def test_real_acpx_keeps_context_across_prompts(tmp_path) -> None:
    """Opt-in: needs acpx, an agent CLI and its credentials."""
    import os
    import shutil

    if os.environ.get("BERB_ACP_E2E") != "1" or not shutil.which("acpx"):
        pytest.skip("set BERB_ACP_E2E=1 with acpx on PATH to run against a real agent")
    agent = os.environ.get("BERB_ACP_AGENT", "claude")
    client = ACPClient(
        ACPConfig(agent=agent, cwd=str(tmp_path), session_name="berb-e2e", timeout_sec=300)
    )
    try:
        client.chat([{"role": "user", "content": "Remember the word PELICAN. Reply OK."}])
        answer = client.chat([{"role": "user", "content": "Which word did I ask you to remember?"}])
    finally:
        client.close()

    assert "PELICAN" in answer.content.upper()
