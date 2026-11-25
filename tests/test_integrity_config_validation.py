"""Integrity config validation (wave 6: RI-11, RI-12).

RI-11  ``integrity.mode`` was never validated, and ``gates()`` gates nothing
       for an unknown mode, so a typo ("submision") silently disabled every
       integrity gate.
RI-12  ``fail_on_*``, ``require_source_snippets`` and ``auto_strict_domains``
       had no reader: setting them changed nothing. They are removed, and a
       config that still sets them is warned that they have no effect.
See tasks/state_machines_p2_results.md item 6.
"""

from __future__ import annotations

import copy

import pytest

from berb.config import IntegrityConfig, RCConfig, validate_config
from berb.integrity.findings import CheckId, Finding, Severity, gates

_BASE = {
    "project": {"name": "t"},
    "research": {"topic": "t"},
    "runtime": {"timezone": "UTC"},
    "notifications": {"channel": "console"},
    "knowledge_base": {"root": "kb"},
    "llm": {"provider": "openai-compatible", "base_url": "http://x", "api_key_env": "T"},
}

_UNREAD = (
    "fail_on_unsupported_claims",
    "fail_on_unverified_statistics",
    "fail_on_citation_fallback",
    "require_source_snippets",
    "auto_strict_domains",
)


def _with_integrity(**integrity: object) -> dict:
    data = copy.deepcopy(_BASE)
    data["integrity"] = integrity
    return data


@pytest.mark.parametrize("mode", ["draft", "submission", "strict"])
def test_known_integrity_modes_validate(mode: str):
    assert validate_config(_with_integrity(mode=mode), check_paths=False).ok


@pytest.mark.parametrize("mode", ["submision", "Strict", "off", ""])
def test_unknown_integrity_mode_is_a_config_error(mode: str):
    result = validate_config(_with_integrity(mode=mode), check_paths=False)

    if mode == "":
        assert result.ok  # blank falls back to the default, like other enums
    else:
        assert not result.ok
        assert any("integrity.mode" in e for e in result.errors)


@pytest.mark.parametrize("mode", [["strict"], {"m": 1}, 3])
def test_non_string_integrity_mode_is_a_config_error(mode: object):
    result = validate_config(_with_integrity(mode=mode), check_paths=False)

    assert any("integrity.mode" in e for e in result.errors)


@pytest.mark.parametrize("mode", ["", "  ", None])
def test_blank_integrity_mode_loads_as_draft(mode: object):
    cfg = RCConfig.from_dict(_with_integrity(mode=mode), check_paths=False)

    assert cfg.integrity.mode == "draft"


def test_integrity_modes_match_the_gate_table():
    from berb.config import INTEGRITY_MODES
    from berb.integrity.findings import _GATING_SEVERITIES_BY_MODE

    assert set(_GATING_SEVERITIES_BY_MODE) == INTEGRITY_MODES


@pytest.mark.parametrize("section", ["strict", ["draft"], 1])
def test_non_mapping_integrity_section_refuses_to_load(section: object):
    data = copy.deepcopy(_BASE)
    data["integrity"] = section

    with pytest.raises(ValueError, match="Invalid integrity"):
        RCConfig.from_dict(data, check_paths=False)


def test_unknown_integrity_mode_refuses_to_load():
    with pytest.raises(ValueError, match="integrity.mode"):
        RCConfig.from_dict(_with_integrity(mode="submision"), check_paths=False)


def test_gates_fail_closed_on_an_unknown_mode():
    block = Finding(check=CheckId.RETRACTION, severity=Severity.BLOCK, message="x")

    assert gates((block,), "submision") == (block,)


@pytest.mark.parametrize("key", _UNREAD)
def test_unread_integrity_flags_warn_that_they_do_nothing(key: str):
    result = validate_config(_with_integrity(**{key: True}), check_paths=False)

    assert result.ok
    assert any(f"integrity.{key}" in w and "no effect" in w for w in result.warnings)


@pytest.mark.parametrize("key", _UNREAD)
def test_unread_integrity_flags_are_not_config_fields(key: str):
    assert key not in IntegrityConfig.__dataclass_fields__


def test_example_config_sets_no_removed_integrity_keys():
    from pathlib import Path

    import yaml

    example = Path(__file__).resolve().parents[1] / "configs" / "config.arc.example.yaml"
    integrity = yaml.safe_load(example.read_text(encoding="utf-8")).get("integrity", {})

    assert integrity.get("mode") in ("draft", "submission", "strict")
    assert not set(integrity) & set(_UNREAD)
