from __future__ import annotations

import json
import logging

import httpx
import pytest

from berb.adapters import (
    AdapterBundle,
    BrowserPage,
    ConsoleMessageAdapter,
    FetchResponse,
    HttpWebFetchAdapter,
    RecordingBrowserAdapter,
    RecordingCronAdapter,
    RecordingMessageAdapter,
    RecordingSessionsAdapter,
    RecordingWebFetchAdapter,
    WebhookMessageAdapter,
    create_adapters,
)


def test_adapter_bundle_defaults_are_recording_types():
    bundle = AdapterBundle()
    assert isinstance(bundle.cron, RecordingCronAdapter)
    assert isinstance(bundle.message, RecordingMessageAdapter)
    assert isinstance(bundle.sessions, RecordingSessionsAdapter)
    assert isinstance(bundle.web_fetch, RecordingWebFetchAdapter)
    assert isinstance(bundle.browser, RecordingBrowserAdapter)


def test_recording_cron_adapter_records_call_and_returns_id():
    adapter = RecordingCronAdapter()
    result = adapter.schedule_resume("run-1", 7, "gate opened")
    assert result == "cron-1"
    assert adapter.calls == [("run-1", 7, "gate opened")]


def test_recording_message_adapter_notify_records_call():
    adapter = RecordingMessageAdapter()
    result = adapter.notify("ops", "stage update", "stage 3 done")
    assert result == "message-1"
    assert adapter.calls == [("ops", "stage update", "stage 3 done")]


def test_recording_sessions_adapter_spawn_records_calls():
    adapter = RecordingSessionsAdapter()
    result = adapter.spawn("worker", ("python", "train.py"))
    assert result == "session-1"
    assert adapter.calls == [("worker", ("python", "train.py"))]


def test_recording_webfetch_fetch_returns_success_response():
    adapter = RecordingWebFetchAdapter()
    response = adapter.fetch("https://example.com")
    assert isinstance(response, FetchResponse)
    assert response.url == "https://example.com"
    assert response.status_code == 200
    assert "stub fetch" in response.text


def test_recording_browser_open_returns_browser_page():
    adapter = RecordingBrowserAdapter()
    page = adapter.open("https://example.com")
    assert isinstance(page, BrowserPage)
    assert page.url == "https://example.com"
    assert "Stub browser page" in page.title


def test_fetch_response_dataclass_fields():
    response = FetchResponse(url="u", status_code=201, text="ok")
    assert response.url == "u"
    assert response.status_code == 201
    assert response.text == "ok"


def test_browser_page_dataclass_fields():
    page = BrowserPage(url="https://a", title="A")
    assert page.url == "https://a"
    assert page.title == "A"


def test_all_adapters_start_with_empty_call_lists():
    cron = RecordingCronAdapter()
    message = RecordingMessageAdapter()
    sessions = RecordingSessionsAdapter()
    web_fetch = RecordingWebFetchAdapter()
    browser = RecordingBrowserAdapter()
    assert cron.calls == []
    assert message.calls == []
    assert sessions.calls == []
    assert web_fetch.calls == []
    assert browser.calls == []


# BR-26: with use_web_fetch on, stub fetch adapters marked every literature
# source "verified" / 200 without making a request.

_SEARCH_CFG = {
    "project": {"name": "t"},
    "research": {"topic": "graph neural networks"},
    "runtime": {"timezone": "UTC"},
    "notifications": {"channel": "console"},
    "knowledge_base": {"root": "kb"},
    "llm": {"provider": "openai-compatible", "base_url": "http://x", "api_key_env": "T"},
    "openclaw_bridge": {"use_web_fetch": True},
}


def _search_sources(tmp_path, adapters) -> list[dict]:
    import copy
    import json

    from berb.config import RCConfig
    from berb.pipeline.stage_impls._literature import _execute_search_strategy

    cfg = RCConfig.from_dict(copy.deepcopy(_SEARCH_CFG), check_paths=False)
    stage_dir = tmp_path / "stage-03"
    stage_dir.mkdir(parents=True)
    _execute_search_strategy(stage_dir, tmp_path, cfg, adapters)
    return json.loads((stage_dir / "sources.json").read_text(encoding="utf-8"))["sources"]


def test_stub_web_fetch_does_not_mark_sources_verified(tmp_path):
    sources = _search_sources(tmp_path, AdapterBundle())

    assert sources
    assert all(s["status"] == "unverified" for s in sources), sources
    assert all("http_status" not in s for s in sources), sources


@pytest.mark.parametrize(
    ("code", "status"),
    [(200, "reachable"), (400, "reachable"), (404, "unreachable"), (503, "unreachable")],
)
def test_real_web_fetch_records_reachability(tmp_path, code, status):
    # A parameterless request to an API endpoint answers 400 although the
    # service is up (Semantic Scholar search does), so 400 is reachable.
    class _Real:
        def fetch(self, url: str) -> FetchResponse:
            return FetchResponse(url=url, status_code=code, text="")

    sources = _search_sources(tmp_path, AdapterBundle(web_fetch=_Real()))

    assert all(s["status"] == status and s["http_status"] == code for s in sources)


# W8: the factory builds real adapters, and the entry points use it.

_PUBLIC = "http://93.184.215.14"  # literal public IP: no DNS lookup in tests


def _cfg(**overrides):
    import copy

    from berb.config import RCConfig

    data = copy.deepcopy(_SEARCH_CFG)
    for section, values in overrides.items():
        data.setdefault(section, {}).update(values)
    return RCConfig.from_dict(data, check_paths=False)


def test_from_config_builds_real_adapters():
    bundle = create_adapters(_cfg())

    assert isinstance(bundle.message, ConsoleMessageAdapter)
    assert isinstance(bundle.web_fetch, HttpWebFetchAdapter)


def test_from_config_builds_a_webhook_for_the_webhook_channel():
    bundle = create_adapters(
        _cfg(notifications={"channel": "webhook", "target": f"{_PUBLIC}/hook"})
    )

    assert isinstance(bundle.message, WebhookMessageAdapter)
    assert bundle.message.url == f"{_PUBLIC}/hook"


def _fetcher(handler) -> HttpWebFetchAdapter:
    return HttpWebFetchAdapter(transport=httpx.MockTransport(handler))


def test_http_fetch_returns_the_real_status():
    response = _fetcher(lambda req: httpx.Response(400)).fetch(f"{_PUBLIC}/api")

    assert response.fetched is True
    assert response.status_code == 400


def test_http_fetch_falls_back_to_get_when_head_is_refused():
    methods: list[str] = []

    def handler(req: httpx.Request) -> httpx.Response:
        methods.append(req.method)
        return httpx.Response(405 if req.method == "HEAD" else 200)

    assert _fetcher(handler).fetch(f"{_PUBLIC}/api").status_code == 200
    assert methods == ["HEAD", "GET"]


@pytest.mark.parametrize(
    "url", ["http://169.254.169.254/latest/meta-data", "http://127.0.0.1:8080/", "file:///etc/x"]
)
def test_http_fetch_refuses_internal_urls(url):
    sent: list[httpx.Request] = []

    with pytest.raises(ValueError, match="SSRF"):
        _fetcher(lambda req: sent.append(req) or httpx.Response(200)).fetch(url)
    assert not sent


def test_http_fetch_checks_every_redirect_hop():
    sent: list[str] = []

    def handler(req: httpx.Request) -> httpx.Response:
        sent.append(str(req.url))
        return httpx.Response(302, headers={"location": "http://169.254.169.254/"})

    with pytest.raises(ValueError, match="SSRF"):
        _fetcher(handler).fetch(f"{_PUBLIC}/a")
    assert sent == [f"{_PUBLIC}/a"]


def test_webhook_posts_slack_and_discord_keys():
    bodies: list[dict] = []

    def handler(req: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(req.content))
        return httpx.Response(204)

    hook = WebhookMessageAdapter(url=f"{_PUBLIC}/hook", transport=httpx.MockTransport(handler))
    hook.notify("webhook", "gate-05", "Approval required")

    assert bodies == [
        {"text": "gate-05: Approval required", "content": "gate-05: Approval required"}
    ]


def test_webhook_failure_does_not_raise_into_the_stage():
    def handler(req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    hook = WebhookMessageAdapter(url=f"{_PUBLIC}/hook", transport=httpx.MockTransport(handler))

    assert hook.notify("webhook", "s", "b") == ""


def test_webhook_refuses_an_internal_target():
    sent: list[httpx.Request] = []
    hook = WebhookMessageAdapter(
        url="http://10.0.0.5/hook",
        transport=httpx.MockTransport(lambda req: sent.append(req) or httpx.Response(200)),
    )

    assert hook.notify("webhook", "s", "b") == ""
    assert not sent


def test_console_adapter_logs(caplog):
    with caplog.at_level(logging.INFO, logger="berb.adapters"):
        ConsoleMessageAdapter().notify("console", "stage-03-start", "Starting")

    assert "stage-03-start: Starting" in caplog.text


def test_webhook_truncates_long_messages():
    bodies: list[dict] = []

    def handler(req: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(req.content))
        return httpx.Response(204)

    hook = WebhookMessageAdapter(url=f"{_PUBLIC}/hook", transport=httpx.MockTransport(handler))
    hook.notify("webhook", "stage-05-failed", "x" * 5000)

    assert len(bodies[0]["content"]) <= 2000
    assert bodies[0]["content"].endswith("...")


def test_http_fetch_time_budget_covers_redirects():
    import time

    def handler(req: httpx.Request) -> httpx.Response:
        time.sleep(0.1)
        return httpx.Response(302, headers={"location": f"{_PUBLIC}/next"})

    adapter = HttpWebFetchAdapter(timeout_sec=0.05, transport=httpx.MockTransport(handler))

    with pytest.raises(TimeoutError):
        adapter.fetch(f"{_PUBLIC}/a")


async def test_pipeline_start_route_builds_adapters_from_config(tmp_path, monkeypatch):
    # The route passed a bare AdapterBundle(), so no configured adapter ran.
    pytest.importorskip("fastapi")
    from typing import Any

    from berb.pipeline._helpers import StageResult
    from berb.pipeline.stages import Stage, StageStatus
    from berb.server.app import create_app
    from berb.server.routes import pipeline as routes

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(routes, "_active_run", None)
    monkeypatch.setattr(routes, "_run_task", None)
    seen: dict[str, Any] = {}

    async def fake_execute(**kw: Any):
        seen.update(kw)
        return [StageResult(stage=Stage.TOPIC_INIT, status=StageStatus.DONE, artifacts=())]

    monkeypatch.setattr("berb.pipeline.runner.execute_pipeline", fake_execute)
    app = create_app(_cfg())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://t"
    ) as client:
        resp = await client.post("/api/pipeline/start", json={"topic": "x", "auto_approve": True})
    assert resp.status_code == 200
    await routes._run_task

    assert isinstance(seen["adapters"].message, ConsoleMessageAdapter)
    assert isinstance(seen["adapters"].web_fetch, HttpWebFetchAdapter)
