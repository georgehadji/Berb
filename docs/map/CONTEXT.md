# How to walk the map

1. Read `CLAUDE.md`, then `objects/_index.md`.
2. Pick the one line for your noun. Stub lines name the owning path; open that source.
3. Cards, when they exist, cite `path:line`. If a comment and code disagree, code wins.

## Universes

| Universe | Meaning | Where decided |
|---|---|---|
| live | wired, reachable from `berb run` / `berb serve` | `scripts/check_reachability.py` |
| leftover | present, parked, on a 90-day clock (PARK, groups D-05..D-08) | `.reachability-allowlist` |
| ghost | named or filed but not wired, deleted, or broken | allowlist CLOSED notes, root `CLAUDE.md` |

Public API packages `berb.llm` and `berb.literature` are live by contract (`__all__`, `tests/test_public_api_contract.py`) even where no internal caller exists.

## Status values

`stub` (one line, no body), `verified` (needs date, commit, citations), `stale`. Only `objects/pipeline-core/` and `objects/llm/` are verified.

## Not covered yet

Inbound consumers (external configs, scheduled jobs, other repos, `berb-*` skills pointing at `berb/` paths) are unrecorded. Add them to the card they land on when the owner supplies them.
