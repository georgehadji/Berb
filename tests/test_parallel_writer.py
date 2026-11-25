"""ParallelSectionWriter (RI-16, behind BERB_EXPERIMENTAL_PARALLEL_WRITER=1).

A section whose LLM call kept failing was re-selected every wave, forever,
so stage 17 hung. It now gets a bounded number of attempts and then raises,
which makes the caller fall back to the sequential writer.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from berb.writing.parallel_writer import MAX_SECTION_ATTEMPTS, ParallelSectionWriter


class _LLM:
    def __init__(self, intro_failures: int) -> None:
        self.intro_failures = intro_failures
        self.intro_calls = 0

    def chat(self, messages, system=""):
        if "Introduction" in system:
            self.intro_calls += 1
            if self.intro_calls <= self.intro_failures:
                raise RuntimeError("rate limited")
        return SimpleNamespace(content="text")


def _write(llm: _LLM):
    writer = ParallelSectionWriter(llm_client=llm)
    return asyncio.run(asyncio.wait_for(writer.write_sections_parallel({}), timeout=5))


def test_gives_up_on_a_section_that_keeps_failing() -> None:
    llm = _LLM(intro_failures=10**6)

    with pytest.raises(RuntimeError, match="Introduction"):
        _write(llm)
    assert llm.intro_calls == MAX_SECTION_ATTEMPTS


def test_retries_a_section_that_fails_once() -> None:
    paper = _write(_LLM(intro_failures=1))

    assert "Introduction" in paper.sections


def test_independent_sections_are_written_concurrently() -> None:
    # Introduction and Methods have no dependencies, so they share a wave.
    # A sync chat() called on the event loop ran them one after another.
    import threading
    import time

    lock = threading.Lock()
    state = {"now": 0, "peak": 0}

    class _Slow:
        def chat(self, messages, system=""):
            with lock:
                state["now"] += 1
                state["peak"] = max(state["peak"], state["now"])
            time.sleep(0.2)
            with lock:
                state["now"] -= 1
            return SimpleNamespace(content="no issues")

    _write(_Slow())

    assert state["peak"] >= 2
