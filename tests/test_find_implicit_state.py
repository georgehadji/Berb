"""Fixture test for scripts/find_implicit_state.py (the implicit state-machine census)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "find_implicit_state.py"
_spec = importlib.util.spec_from_file_location("find_implicit_state", _SCRIPT)
assert _spec and _spec.loader
fis = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fis)

FIXTURE = """
from enum import StrEnum

class Phase(StrEnum):
    IDLE = "idle"
    BUSY = "busy"

_CACHE = {}
COUNT = 0

def remember(k, v):
    _CACHE[k] = v

def bump():
    global COUNT
    COUNT += 1

class Worker:
    def __init__(self):
        self._running = False   # init is not a transition
        self.status = "idle"

    def start(self):
        self._running = True
        self.status = "busy"

    def stop(self):
        if not self._running:
            return
        self._running = False
        self.result = {"verdict": "ok"}

def check(x):
    return x == "busy"
"""


def _by_signal(rows):
    out: dict[str, list] = {}
    for sig, line, note in rows:
        out.setdefault(sig, []).append((line, note))
    return out


def test_scan_source_finds_each_signal():
    rows = _by_signal(fis.scan_source(FIXTURE, {"idle", "busy"}))
    notes = {s: [n for _, n in v] for s, v in rows.items()}

    assert any("attr" == n for n in notes["S1"])  # self.status = ...
    assert any("dict-key" == n for n in notes["S1"])  # {"verdict": ...}
    assert notes["S2"] == ["in start", "in stop"]  # __init__ excluded
    assert notes["S4"][0] == "enum Phase"
    assert "raw string 'busy'" in notes["S4"]
    assert any(n.startswith("global COUNT") for n in notes["S5"])
    assert "_CACHE mutated in remember" in notes["S5"]
    (s12,) = notes["S12"]
    assert "start,stop" in s12 and "guard in first 2 stmts: stop" in s12.replace("if-", "")


def test_scan_tree_marks_wired_and_formats_rows(tmp_path):
    pkg = tmp_path / "berb"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "w.py").write_text(FIXTURE)
    (pkg / "bad.py").write_text("def (:\n")  # unparseable files are skipped, not fatal

    rows = fis.scan_tree(str(tmp_path), wired={"berb.w"})
    assert rows and all(len(r) == 5 for r in rows)
    assert {r[3] for r in rows} == {"berb.w"}
    assert {r[4] for r in rows} == {"Y"}
    assert all(r[1].startswith("berb/w.py:") for r in rows)

    rows_unwired = fis.scan_tree(str(tmp_path), wired=set())
    assert {r[4] for r in rows_unwired} == {"N"}
