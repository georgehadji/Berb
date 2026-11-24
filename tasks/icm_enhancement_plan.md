# ICM enhancement plan

Drafted 2026-10-22 against `fb7bd25`. Source: the "research how to enhance the project with ICM" findings. Nothing here is started. Sizes are relative (S/M/L), not time.

Scope rule from the research: apply ICM to the agent-facing layer (repo navigation) and the run directory. Do NOT move runtime orchestration into folders: parallel DAG levels, pivot recursion and the discovery loop are cases ICM says need code.

## Decisions needed before the marked phases

| ID | Decision | Blocks | Default if unanswered |
|---|---|---|---|
| D1 | Per-stage `CONTEXT.md`: write into each run dir at runtime, or generate one static reference into `docs/map/`? | P3 | static (zero runtime risk) |
| D2 | Root `CLAUDE.md` sections "Workflow Orchestration", "Task Management", "Core Principles" are generic working rules. Drop them from the repo file, or move them to a separate rules file? | P6 | move to `.claude/rules/workflow.md`, linked from the entry file |
| D3 | `QWEN.md` and `REASONIX.md` serve other tools that do not follow links. Pointer file or generated copy of the slim entry file? | P6 | generated copy |
| D4 | Anything outside this repo that hardcodes a path into it (scheduled jobs, other repos, MCP configs, the `berb-*` skills, `.reasonix/`)? | P1 close, P7 | none known; ask before any move |

## P0 — Baseline (S)

- [ ] Branch each phase off `main` after `fix/llm-cascade-kwargs-and-preflight` merges; one PR per phase.
- [ ] Record baseline: `pytest -m "not slow and not e2e and not llm"`, `ruff check berb/ tests/`, `ruff format --check berb/ tests/`, `python scripts/check_reachability.py`. Note failures that predate this work so they are not blamed on it.
- Done when: baseline numbers are written at the top of the first PR.

## P1 — Finish the map (L)

One cluster per slice, each human-gated, same method as pipeline-core and llm: read source, find callers, write cards with `path:line`, re-verify load-bearing claims, update `objects/_index.md`, regenerate twins.

- [x] literature (done 2026-10-22, 8 cards in `docs/map/objects/literature/`): public API contract, search cascade and clients, verification, advisory screens, novelty, PDF ingestion; parked modules recorded as leftover. Two defects found and fixed (uncommitted), see the cards.
- [ ] experiment: sandboxes, `search/`, `validator`, `plot_verdict`, `pipeline/code_agent.py`, `experiment_repair.py`; `react_agent` ghost.
- [ ] integrity-review: ensemble, claim manifests, citation anchors, `paper_verifier`, `hallucination_detector`.
- [ ] config-prompts: `berb/config.py` schema, `prompts.default.yaml`, `PromptManager`; resolve the `config.arc.yaml` / `config.berb.yaml` collision note into a card.
- [ ] surfaces: CLI commands, server, MCP, dashboard, copilot, discovery loop, iterative loop, bridges.
- [ ] Carry-over: llm modules not yet carded (`acp_client`, `deep_query_client`, adapters, `presets`, `registry`, `pricing`, `output_limits`, `prompt_cache`, `cross_model`).
- [ ] `processes/` (only real movements): `berb run` stage sequencing, resume and `--from-stage`, gate approve/reject, pivot/refine, discovery loop, LLM call path.
- [ ] `effects/CONTEXT.md`: "if you change X, open these cards", walked backwards for inbound consumers (answer D4 first).
- Known input: the model-cascade card cites lines that moved about 9 lines after the fix; re-verify it in this phase.
- Done when: every row in `_index.md` is `verified` or deliberately `stub` with a reason; a cold walk answers "what is X" and "what else moves" from `map/CLAUDE.md` plus one card, within 2k-8k tokens.

## P2 — Map rot guard (S-M)

- [ ] `scripts/check_map.py`: for each card, every cited `path[:line[-line]]` exists and the line is within the file; frontmatter has `type`, `cluster`, `universe`, `status`; `verified` cards carry a date and commit; `AGENTS.md` and `routing.md` equal `CLAUDE.md` byte for byte; every `[[link]]` resolves to a card.
- [ ] Unit tests for the script (a deliberately broken fixture card for each rule).
- [ ] Wire into `.github/workflows/ci.yml` Lint job beside `check_reachability.py`.
- [ ] Optional: `--regen-twins` flag so twins are rebuilt by script, never by hand.
- Risk: line-number checks go stale on every edit. Keep to "exists and in range", not "same content".
- Done when: CI fails on a broken cite and passes on the current map.

## P3 — Per-stage contract context (S-M, needs D1)

Shared first step: [ ] list everything that reads or copies `stage-NN/` contents (`package_deliverables`, `write_stage_to_kb`, dashboard scanner, `build_pipeline_summary`) so an extra file cannot leak into deliverables or counts.

- Option static (default): [ ] `scripts/gen_stage_contracts.py` writes `docs/map/processes/stage-contracts.md` from `CONTRACTS` (inputs, outputs, definition of done, `depends_on`, gate yes/no, noncritical). Generated, never hand-edited; checked by P2.
- Option runtime: [ ] write `stage-NN/CONTEXT.md` in `execute_stage` (where `stage_dir` is created, `executor.py:163`) from `CONTRACTS[stage]`. Tests: file present, content matches contract, not counted as an artifact, excluded from deliverables, does not satisfy or break output validation.
- Done when: the chosen output is generated from `CONTRACTS` only, and a test fails if it drifts from `CONTRACTS`.

## P4 — Edit-then-resume documented (S)

- [ ] Verify the real behaviour on one stage: edit a stage-N artifact, run `berb run --from-stage N+1` (or `--resume`), confirm the edit is read. Note that `execute_stage` checks input existence only (`executor.py:168-181`), so a human edit is accepted unchecked.
- [ ] Write the `processes/edit-and-resume.md` card: which gates (5, 9, 20) are the natural stop points, which flags, what is not re-validated.
- [ ] If the check shows a stage ignores a human edit (regenerates the file), record it as a defect with its own fix, not in this plan.
- Done when: the card exists and its claims were each exercised once.

## P5 — One home per fact (M, after P1)

- [ ] Coverage matrix: for each section of `docs/CODEBASE_MIND_MAP.md`, `docs/HOW_BERB_WORKS.md` and the `berb-*` skills, is the fact now in a map card?
- [ ] For fully covered sections: replace the body with a one-line pointer to the card. Do not delete files. Leave anything not covered alone.
- [ ] Fix claims the audit found false in whichever file still carries them (`tasks/todo.md` notes `docs/HOW_BERB_WORKS.md:376` claimed prompt caching that was not live; caching has since been wired through `cached_prefix` in `client.py`, so re-check before editing).
- Done when: no fact has two full copies; every pointer resolves.

## P6 — Slim entry files (M, after P1, needs D2 and D3)

- [ ] Rewrite root `CLAUDE.md` to roughly 60 lines: what Berb is, commands, routing table (map, reachability gate, tests), the few hard rules (never raise the reachability ceiling; `berb.llm` and `berb.literature` are contracts).
- [ ] Move the Subsystems table and the long prose (public-API history, vision, cascade, discovery notes, deleted-module notes) into the matching cards; verify each moved fact exists in a card before removing it from the entry file.
- [ ] D2 outcome for the three generic workflow sections.
- [ ] D3 outcome for `QWEN.md` (537 lines; referenced by `docs/HOW_BERB_WORKS.md`, `docs/NAMING_CONVENTION.md`, `RELEASE_NOTES_v3.0.md`, `TODO.md`) and `REASONIX.md` (68 lines; no in-repo referrer, but `.reasonix/` exists, so a tool probably reads it). Do not delete either.
- [ ] Generate the twins by script and let P2 check them.
- Done when: entry file is within 2k-8k tokens with its routing target, a cold walk reaches a card in two hops, and no content was lost (diff of facts, not lines).

## P7 — Root clutter restructure (M, last, gated)

Restructure mode, so nothing moves before approval.

- [ ] Inventory: 18 root `.md` plus one `.pdf` besides the entry files. Classify catalog / contract / factory / product / dead.
- [ ] Reference report per file (in-repo, `../`, scripts, external via D4). Known so far: `IMPLEMENTATION_COMPLETE.md` is referenced by `scripts/cleanup_docs.bat`, `docs/DOCUMENTATION_CLEANUP.md`, `docs/IMPLEMENTATION.md`, `docs/OPTIMIZATION_SUMMARY.md`, `RELEASE_NOTES_v3.0.md`; `IMPLEMENTATION_STATUS.md` and `BERB_OPTIMIZATION_PLAN_v1.md` by each other and `docs/ARCHITECTURE_v3_OPTIMIZATIONS.md`. `RELEASE_NOTES_v3.0.md` and `TEST_RESEARCH_SUBMISSION.md` showed none in-repo. Read `scripts/cleanup_docs.bat` first: it may move or delete these files itself.
- [ ] Propose target tree and migration map (old -> new -> role -> referrers). Candidate: history, plans and audits to `docs/history/`; `README.md`, `CONTRIBUTING.md`, `LICENSE`, `CLAUDE.md`, `TODO.md` stay.
- [ ] Case-fold check on destinations, then `git mv`, update every referrer in the same commit, verify with a link check.
- [ ] Hold any file with a live external referrer until it is updated.
- Done when: root holds only catalog files, every old reference resolves, and `git log --follow` still tracks the moved files.

## Order and parallelism

```
P0 -> P1 ------> P5 -> P6 -> P7
 |     \-> P2 (can start once the first cluster exists)
 |-> P3, P4 (independent of P1; can run beside it)
```

P3, P4 and P2 touch disjoint files from P1's cards, so they can run in parallel sessions. P5, P6 and P7 touch shared docs and run in sequence.

## Verification at the end

- [ ] Walk test from `map/CLAUDE.md`: where am I, where do I go, status derivable, no routing file carrying payload, no fact in two places, token band met.
- [ ] `pytest -m "not slow and not e2e and not llm"`, `ruff check` and `ruff format --check`, `mypy berb/ --python-version 3.11`, `check_reachability.py`, `check_map.py` all green or no worse than baseline.

## Not doing

- Folder-driven runtime orchestration.
- Numbering `berb/` subpackages.
- Splitting `prompts.default.yaml` per stage.
- Deleting root files or the `QWEN.md` and `REASONIX.md` entry files.
