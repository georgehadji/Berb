"""ACP (Agent Client Protocol) LLM client via acpx.

Uses acpx as the ACP bridge to communicate with any ACP-compatible agent
(Claude Code, Codex, Gemini CLI, etc.) via persistent named sessions.

Key advantage: a single persistent session maintains context across all
23 pipeline stages — the agent remembers everything.
"""

from __future__ import annotations

import atexit
import logging
import os
import shutil
import subprocess
import threading
import weakref
from dataclasses import dataclass
from typing import Any

from berb.llm.client import LLMResponse

logger = logging.getLogger(__name__)

# acpx exit codes (docs/exit-codes.md in openclaw/acpx).
_EXIT_USAGE = 2
_EXIT_NO_SESSION = 4
_EXIT_PERMISSION_DENIED = 5


@dataclass
class ACPConfig:
    """Configuration for ACP agent connection."""

    agent: str = "claude"
    cwd: str = "."
    acpx_command: str = ""  # auto-detect if empty
    session_name: str = "berb"
    timeout_sec: int = 1800  # per-prompt timeout
    permission_mode: str = "approve-reads"  # acpx --approve-reads|--approve-all|--deny-all


def _close_session(acpx: str, cwd: str, agent: str, session_name: str) -> None:
    """Best-effort ``acpx sessions close``; never raises."""
    try:
        subprocess.run(
            [acpx, "--ttl", "0", "--cwd", cwd, agent, "sessions", "close", session_name],
            capture_output=True,
            timeout=15,
        )
    except Exception:  # noqa: BLE001
        pass


def _find_acpx() -> str | None:
    """Find the acpx binary — check PATH, then OpenClaw's plugin directory."""
    found = shutil.which("acpx")
    if found:
        return found
    # Check OpenClaw's bundled acpx plugin
    openclaw_acpx = os.path.expanduser("~/.openclaw/extensions/acpx/node_modules/.bin/acpx")
    if os.path.isfile(openclaw_acpx) and os.access(openclaw_acpx, os.X_OK):
        return openclaw_acpx
    return None


class ACPClient:
    """LLM client that uses acpx to communicate with ACP agents.

    Spawns persistent named sessions via acpx, reusing them across
    ``.chat()`` calls so the agent maintains context across the full
    23-stage pipeline.
    """

    # Track live instances for atexit cleanup (weak refs to avoid preventing GC)
    _live_instances: list[weakref.ref[ACPClient]] = []
    _atexit_registered: bool = False
    # (acpx, cwd, agent, session_name) of every session opened and not yet closed.
    _open_sessions: set[tuple[str, str, str, str]] = set()

    def __init__(self, acp_config: ACPConfig) -> None:
        self.config = acp_config
        self._acpx: str | None = acp_config.acpx_command or None
        self._session_ready = False
        # One prompt at a time: callers on several threads (the parallel
        # writer) share one named session, and a reconnect from one thread
        # closed it under the others.
        self._prompt_lock = threading.Lock()
        # Prune dead weakrefs, then track this instance
        ACPClient._live_instances = [r for r in ACPClient._live_instances if r() is not None]
        ACPClient._live_instances.append(weakref.ref(self))
        if not ACPClient._atexit_registered:
            atexit.register(ACPClient._atexit_cleanup)
            ACPClient._atexit_registered = True

    @classmethod
    def from_rc_config(cls, rc_config: Any) -> ACPClient:
        """Build from a Berb ``RCConfig``."""
        acp = rc_config.llm.acp
        return cls(
            ACPConfig(
                agent=acp.agent,
                cwd=acp.cwd,
                acpx_command=getattr(acp, "acpx_command", ""),
                session_name=getattr(acp, "session_name", "berb"),
                timeout_sec=getattr(acp, "timeout_sec", 1800),
                permission_mode=getattr(acp, "permission_mode", "approve-reads"),
            )
        )

    # ------------------------------------------------------------------
    # Public interface (matches LLMClient)
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        json_mode: bool = False,
        system: str | None = None,
        cached_prefix: str | None = None,
        cache_ttl: str = "5m",
        strip_thinking: bool = False,
        stage: Any | None = None,
    ) -> LLMResponse:
        """Send a prompt and return the agent's response.

        Parameters mirror ``LLMClient.chat()`` for drop-in compatibility.
        ``model``, ``max_tokens``, ``temperature``, and ``json_mode`` are
        accepted but not forwarded — the agent manages its own model and
        parameters. ``cached_prefix``/``cache_ttl`` request provider-side
        prompt caching, which doesn't apply to a CLI-driven agent — the
        text is still sent (folded into ``system``) so it isn't silently
        dropped, just without a cache_control breakpoint. ``stage`` (per-stage
        token limits in ``LLMClient``) is accepted and ignored for the same
        reason; every stage passes it, so rejecting it failed them all (LL-22).
        """
        del stage, model, max_tokens, temperature, json_mode
        if cached_prefix:
            system = f"{cached_prefix}\n\n{system}" if system else cached_prefix
        prompt_text = self._messages_to_prompt(messages, system=system)
        content = self._send_prompt(prompt_text)
        if strip_thinking:
            from berb.utils.thinking_tags import strip_thinking_tags

            content = strip_thinking_tags(content)
        return LLMResponse(
            content=content,
            model=f"acp:{self.config.agent}",
            finish_reason="stop",
        )

    def preflight(self) -> tuple[bool, str]:
        """Check that acpx and the agent are available."""
        acpx = self._resolve_acpx()
        if not acpx:
            return False, (
                "acpx not found. Install it: npm install -g acpx  "
                "or set llm.acp.acpx_command in config."
            )
        # Check the agent binary exists
        agent = self.config.agent
        if not shutil.which(agent):
            return False, f"ACP agent CLI not found: {agent!r} (not on PATH)"
        # Create the session
        try:
            self._ensure_session()
            return True, f"OK - ACP session ready ({agent} via acpx)"
        except Exception as exc:  # noqa: BLE001
            return False, f"ACP session init failed: {exc}"

    def close(self) -> None:
        """Close the acpx session."""
        if not self._session_ready:
            return
        acpx = self._resolve_acpx()
        if not acpx:
            return
        key = self._session_key(acpx)
        _close_session(*key)
        ACPClient._open_sessions.discard(key)
        self._session_ready = False

    def _session_key(self, acpx: str) -> tuple[str, str, str, str]:
        return (acpx, self._abs_cwd(), self.config.agent, self.config.session_name)

    # No __del__: the acpx session is shared by name across clients. The
    # executor builds each stage's client before dropping the previous one, so
    # closing on garbage collection killed the session the new client was
    # about to reuse (LL-22). _atexit_cleanup closes it once, at shutdown.

    @classmethod
    def _atexit_cleanup(cls) -> None:
        """Close all live ACP sessions on interpreter shutdown."""
        for ref in cls._live_instances:
            inst = ref()
            if inst is not None:
                try:
                    inst.close()
                except Exception:  # noqa: BLE001
                    pass
        cls._live_instances.clear()
        # Sessions whose client was already garbage-collected.
        for key in list(cls._open_sessions):
            _close_session(*key)
        cls._open_sessions.clear()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _resolve_acpx(self) -> str | None:
        """Resolve the acpx binary path (cached)."""
        if self._acpx:
            return self._acpx
        self._acpx = _find_acpx()
        return self._acpx

    def _abs_cwd(self) -> str:
        return os.path.abspath(self.config.cwd)

    def _ensure_session(self) -> None:
        """Find or create the named acpx session."""
        if self._session_ready:
            return
        acpx = self._resolve_acpx()
        if not acpx:
            raise RuntimeError("acpx not found")

        # Use 'ensure' which finds existing or creates new
        result = subprocess.run(
            [
                acpx,
                "--ttl",
                "0",
                "--cwd",
                self._abs_cwd(),
                self.config.agent,
                "sessions",
                "ensure",
                "--name",
                self.config.session_name,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        if result.returncode != 0:
            # Fall back to 'new'
            result = subprocess.run(
                [
                    acpx,
                    "--ttl",
                    "0",
                    "--cwd",
                    self._abs_cwd(),
                    self.config.agent,
                    "sessions",
                    "new",
                    "--name",
                    self.config.session_name,
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Failed to create ACP session: {result.stderr.strip()}")
        self._session_ready = True
        ACPClient._open_sessions.add(self._session_key(acpx))
        logger.info("ACP session '%s' ready (%s)", self.config.session_name, self.config.agent)

    # Error patterns that indicate a dead/stale session (retryable)
    _RECONNECT_ERRORS = (
        "agent needs reconnect",
        "session not found",
        "Query closed",
        f"(exit {_EXIT_NO_SESSION})",
    )
    _MAX_RECONNECT_ATTEMPTS = 2

    def _send_prompt(self, prompt: str) -> str:
        """Send a prompt via acpx and return the response text.

        If the session has died (common after long-running stages), retries
        up to ``_MAX_RECONNECT_ATTEMPTS`` times with automatic reconnection.
        """
        acpx = self._resolve_acpx()
        if not acpx:
            raise RuntimeError("acpx not found")

        with self._prompt_lock:
            return self._send_prompt_locked(acpx, prompt)

    def _send_prompt_locked(self, acpx: str, prompt: str) -> str:
        last_exc: RuntimeError | None = None
        for attempt in range(1 + self._MAX_RECONNECT_ATTEMPTS):
            self._ensure_session()
            try:
                return self._send_prompt_cli(acpx, prompt)
            except RuntimeError as exc:
                if not any(pat in str(exc) for pat in self._RECONNECT_ERRORS):
                    raise
                last_exc = exc
                if attempt < self._MAX_RECONNECT_ATTEMPTS:
                    logger.warning(
                        "ACP session died (%s), reconnecting (attempt %d/%d)...",
                        exc,
                        attempt + 1,
                        self._MAX_RECONNECT_ATTEMPTS,
                    )
                    self._force_reconnect()

        raise last_exc  # type: ignore[misc]

    def _force_reconnect(self) -> None:
        """Close the stale session and reset so _ensure_session creates a new one."""
        try:
            self.close()
        except Exception:  # noqa: BLE001
            pass
        self._session_ready = False

    def _send_prompt_cli(self, acpx: str, prompt: str) -> str:
        """Send the prompt on stdin (``--file -``) and return the final text.

        stdin has no argument-length limit, so no prompt needs a temp file, and
        ``--format quiet`` prints only the agent's final answer.
        """
        try:
            result = subprocess.run(
                [
                    acpx,
                    f"--{self.config.permission_mode}",
                    "--format",
                    "quiet",
                    "--ttl",
                    "0",
                    "--cwd",
                    self._abs_cwd(),
                    self.config.agent,
                    "-s",
                    self.config.session_name,
                    "--file",
                    "-",
                ],
                input=prompt,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.config.timeout_sec,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"ACP prompt timed out after {self.config.timeout_sec}s") from exc
        except OSError as exc:
            raise RuntimeError(f"ACP prompt failed: cannot run {acpx}: {exc}") from exc

        if result.returncode == _EXIT_USAGE:
            stderr = (result.stderr or "").strip()
            raise RuntimeError(
                f"ACP prompt failed (exit 2, usage error): {stderr}. Berb needs an acpx "
                "with --approve-reads, --format quiet and --file -; upgrade acpx."
            )
        if result.returncode == _EXIT_PERMISSION_DENIED:
            raise RuntimeError(
                f"ACP prompt failed: acpx denied every tool request under "
                f"--{self.config.permission_mode}. Widen llm.acp.permission_mode "
                "only if the agent needs tools; prompts include third-party paper text."
            )
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            raise RuntimeError(f"ACP prompt failed (exit {result.returncode}): {stderr}")

        return (result.stdout or "").strip()

    @staticmethod
    def _messages_to_prompt(
        messages: list[dict[str, str]],
        *,
        system: str | None = None,
    ) -> str:
        """Flatten a chat-messages list into a single text prompt.

        Preserves role labels so the agent can distinguish context.
        """
        parts: list[str] = []
        if system:
            parts.append(f"[System]\n{system}")
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                parts.append(f"[System]\n{content}")
            elif role == "assistant":
                parts.append(f"[Previous Response]\n{content}")
            else:
                parts.append(content)
        return "\n\n".join(parts)
