"""Typed adapter interfaces and deterministic recording stubs.

# Author: Georgios-Chrysovalantis Chatzivantsidis
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx

from berb.web._ssrf import check_url_ssrf

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FetchResponse:
    url: str
    status_code: int
    text: str
    fetched: bool = True
    """False for a stub that made no request; its status_code proves nothing."""


@dataclass(frozen=True)
class BrowserPage:
    url: str
    title: str


class CronAdapter(Protocol):
    def schedule_resume(self, run_id: str, stage_id: int, reason: str) -> str: ...


class MessageAdapter(Protocol):
    def notify(self, channel: str, subject: str, body: str) -> str: ...


class SessionsAdapter(Protocol):
    def spawn(self, name: str, command: tuple[str, ...]) -> str: ...


class WebFetchAdapter(Protocol):
    def fetch(self, url: str) -> FetchResponse: ...


class BrowserAdapter(Protocol):
    def open(self, url: str) -> BrowserPage: ...


# ============================================================================
# Port Protocols
# ============================================================================


class LLMProvider(Protocol):
    """Port: LLM inference, injected into stage implementations as ``adapters.llm``.

    Most stage implementations receive an ``LLMClient`` directly as a
    function parameter — that is the primary seam. ``adapters.llm`` mirrors
    the same client instance (wired by the executor) for call paths that
    thread the adapter bundle through instead, e.g.
    ``stage_impls/_literature.py``'s PDF-ingestion helper.
    """

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str: ...
    def complete(self, prompt: str, **kwargs: Any) -> str: ...


# ============================================================================
# Recording stubs for deterministic testing
# ============================================================================


@dataclass
class RecordingCronAdapter:
    calls: list[tuple[str, int, str]] = field(default_factory=list)

    def schedule_resume(self, run_id: str, stage_id: int, reason: str) -> str:
        self.calls.append((run_id, stage_id, reason))
        return f"cron-{len(self.calls)}"


@dataclass
class RecordingMessageAdapter:
    calls: list[tuple[str, str, str]] = field(default_factory=list)

    def notify(self, channel: str, subject: str, body: str) -> str:
        self.calls.append((channel, subject, body))
        return f"message-{len(self.calls)}"


@dataclass
class RecordingSessionsAdapter:
    calls: list[tuple[str, tuple[str, ...]]] = field(default_factory=list)

    def spawn(self, name: str, command: tuple[str, ...]) -> str:
        self.calls.append((name, command))
        return f"session-{len(self.calls)}"


@dataclass
class RecordingWebFetchAdapter:
    calls: list[str] = field(default_factory=list)

    def fetch(self, url: str) -> FetchResponse:
        self.calls.append(url)
        return FetchResponse(url=url, status_code=200, text=f"stub fetch for {url}", fetched=False)


@dataclass
class RecordingBrowserAdapter:
    calls: list[str] = field(default_factory=list)

    def open(self, url: str) -> BrowserPage:
        self.calls.append(url)
        return BrowserPage(url=url, title=f"Stub browser page for {url}")


# ============================================================================
# Recording stub for the LLMProvider port
# ============================================================================


@dataclass
class RecordingLLMProvider:
    calls: list[tuple[str, list[dict[str, str]] | str]] = field(default_factory=list)

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        self.calls.append(("chat", messages))
        return "Stub chat response"

    def complete(self, prompt: str, **kwargs: Any) -> str:
        self.calls.append(("complete", prompt))
        return "Stub completion response"


# ============================================================================
# Real adapters, built by AdapterBundle.from_config
# ============================================================================

_MAX_REDIRECTS = 5
# Discord rejects content over 2000 characters; Slack allows more.
_MAX_NOTIFY_CHARS = 1900


@dataclass
class ConsoleMessageAdapter:
    """Notifications to the log (``notifications.channel: console``)."""

    def notify(self, channel: str, subject: str, body: str) -> str:
        logger.info("[notify:%s] %s: %s", channel, subject, body)
        return f"console-{subject}"


@dataclass
class WebhookMessageAdapter:
    """POST notifications to ``notifications.target`` (Slack or Discord style).

    Never raises: a notification that cannot be sent must not fail a stage.
    The URL is a secret, so it is never logged.
    """

    url: str
    timeout_sec: float = 10.0
    transport: httpx.BaseTransport | None = None

    def notify(self, channel: str, subject: str, body: str) -> str:
        text = f"{subject}: {body}"
        if len(text) > _MAX_NOTIFY_CHARS:
            text = text[: _MAX_NOTIFY_CHARS - 3] + "..."
        blocked = check_url_ssrf(self.url)
        if blocked:
            logger.warning("Webhook notification not sent: %s", blocked)
            return ""
        try:
            with httpx.Client(
                timeout=self.timeout_sec, follow_redirects=False, transport=self.transport
            ) as client:
                # "text" is read by Slack, "content" by Discord.
                client.post(self.url, json={"text": text, "content": text}).raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Webhook notification failed: %s", type(exc).__name__)
            return ""
        return f"webhook-{subject}"


@dataclass
class HttpWebFetchAdapter:
    """Checks a URL with a real request.

    Every hop, redirects included, passes the SSRF check first: source URLs
    can come from LLM output, so an unchecked fetch would probe internal hosts.
    HEAD is tried first; a server that refuses HEAD gets a streamed GET whose
    body is never read. ``timeout_sec`` bounds the whole check, redirects
    included, so a list of slow hosts cannot stall stage 3 for minutes.
    """

    timeout_sec: float = 10.0
    transport: httpx.BaseTransport | None = None

    def fetch(self, url: str) -> FetchResponse:
        deadline = time.monotonic() + self.timeout_sec

        def remaining() -> float:
            left = deadline - time.monotonic()
            if left <= 0:
                raise TimeoutError(f"Source check exceeded {self.timeout_sec}s: {url}")
            return left

        with httpx.Client(follow_redirects=False, transport=self.transport) as client:
            current = url
            for _ in range(_MAX_REDIRECTS + 1):
                blocked = check_url_ssrf(current)
                if blocked:
                    raise ValueError(f"Blocked by SSRF check: {blocked}")
                response = client.head(current, timeout=remaining())
                if response.status_code in (405, 501):
                    with client.stream("GET", current, timeout=remaining()) as streamed:
                        response = streamed
                location = response.headers.get("location")
                if not (response.is_redirect and location):
                    return FetchResponse(url=url, status_code=response.status_code, text="")
                current = str(httpx.URL(current).join(location))
        raise ValueError(f"Too many redirects: {url}")


@dataclass
class AdapterBundle:
    """Wiring hub for cross-cutting adapters, used by the pipeline runner
    and threaded through to stage implementations.

    llm (LLMProvider) is the one port stage implementations actually read
    via the bundle (see LLMProvider's docstring); the rest exist purely for
    the runner's own cross-cutting concerns (scheduling, notifications,
    sessions, web fetch, browsing).

    The defaults are recording stubs for tests; ``from_config`` builds the
    real message and web-fetch adapters.
    """

    cron: CronAdapter = field(default_factory=RecordingCronAdapter)
    message: MessageAdapter = field(default_factory=RecordingMessageAdapter)
    sessions: SessionsAdapter = field(default_factory=RecordingSessionsAdapter)
    web_fetch: WebFetchAdapter = field(default_factory=RecordingWebFetchAdapter)
    browser: BrowserAdapter = field(default_factory=RecordingBrowserAdapter)
    llm: LLMProvider = field(default_factory=RecordingLLMProvider)

    @classmethod
    def from_config(cls, config: object) -> AdapterBundle:
        """Build the adapters a run uses from RCConfig.

        Each is called only when its ``openclaw_bridge`` flag is on, so
        building them unconditionally changes nothing for a flag that is off.
        """
        notifications = getattr(config, "notifications", None)
        message: MessageAdapter = ConsoleMessageAdapter()
        if notifications is not None and notifications.channel == "webhook":
            message = WebhookMessageAdapter(url=notifications.target)
        return cls(message=message, web_fetch=HttpWebFetchAdapter())


def create_adapters(config: object) -> AdapterBundle:
    """Create an AdapterBundle from RCConfig.

    This is a convenience function that calls AdapterBundle.from_config.
    """
    return AdapterBundle.from_config(config)
