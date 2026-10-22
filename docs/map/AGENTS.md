# Berb map

Edit map of `berb/`: the nouns, what each one touches, and which are actually wired. The source tree stays the truth; cards cite it.

Built on ICM (system map form). Slice 2: `objects/pipeline-core/` and `objects/llm/` cards are verified; other clusters are still stub lines.

## Where things live

| Path | What it holds |
|---|---|
| `CONTEXT.md` | how to walk the map, the three universes, name collisions |
| `_meta/schema.md` | closed node types and labels |
| `_templates/` | `object.md`, `process.md` starters |
| `objects/_index.md` | one line per noun, with status |

`processes/` and `effects/` do not exist yet. They are created only after noun cards are verified.

## Route by what you need

| If | Go to |
|---|---|
| asked what X is | `objects/_index.md`, then the card (once it exists) or the source path on its line |
| about to change X | open X's card, read "If you change this" (stub: grep callers yourself) |
| deciding if code is live | `.reachability-allowlist`, then `python scripts/check_reachability.py` |
| need the old architecture prose | `docs/CODEBASE_MIND_MAP.md`; do not copy it here |

## Names that collide

- Berb = ARC = AutoResearchClaw = ResearchClaw: one project, renamed over time.
- Config file: `berb init` writes `config.arc.yaml` (`berb/cli.py:705`); `berb run` searches `config.arc.yaml`, then `config.yaml` (`berb/config.py:19`). `config.berb.yaml` is never searched; only `berb literature` defaults to it (`berb/cli.py:960`). Unreconciled.
- Root `*_plan.md`, `*_audit_report*.md`, `IMPLEMENTATION_*.md`: history, not spec. Treat as ghost.
