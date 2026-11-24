# P0 + P1 results: implicit state machine discovery

Branch `chore/state-machine-census`, 2026-11-11. Plan: `tasks/implicit_state_machines_plan.md`. Nothing here changes `berb/`; this is analysis only.

## Numbers

| | |
|---|---|
| Wired modules (P0 denominator) | 341 (71 parked, 2 dead: `experiment.react_agent`, `experiment.split_policy`) |
| Census rows (S1-S12) | 645 |
| Machines catalogued | 256 across 9 clusters |
| Class A (live defect claimed) | 117 |
| Class B (duplicate vocabulary) | 17 |
| Class E (explicit, unguarded) | 5 |
| Class C (loop-local / one-shot) | 67 |
| Class D (parked / unwired) | 50 |

Per cluster (machines / A): pipeline_core 29/12, stage_impls 22/10, surfaces 30/12, llm 33/17, experiment 36/18, literature 19/10, review_integrity 28/17, research_loop 20/9, bridges_other 39/12. Detail: `tasks/census_parts/machines_<cluster>.md`.

## P1c coverage check

- Census rows: 645 of 645 mapped to a machine id or dismissed with a reason. Matching was by `file:line` token, so it proves every row is mentioned, not that each mapping is right.
- Wired modules: 340 of 341 named in a "Module coverage" section with machine ids or a `none: reason`. The one exception is the root `berb` package. Matching used the module's last name segment, so it is lenient where two packages share a file name.
- Baseline (P0): `tasks/baseline/SUMMARY.md`. Pre-existing: 2 pytest failures, 4 pytest errors, 1 `ruff format` file, 4 mypy yaml-stub errors.

## What every defect claim is worth

The ~117 class A claims are **agent claims**. Most were traced by reading code, a few by running read-only python; several are marked `unverified` in the cluster files. Per plan P2, every High/Critical row needs an adversarial Sonnet verification before it is scheduled into a wave. I re-checked two myself so far: the `EX-03` call site (`search/runner.py:477`, `await sandbox.run()` with no argument, while `run(self, code, ...)` requires `code` and is synchronous) and the baseline numbers. Whether Stage 12 wraps the sandbox in an adapter first is untraced.

## Corrections to the plan

- **W4 / SF-6 is wrong.** `config.project.mode` is validated against `PROJECT_MODES` (`berb/config.py:1304`), so a typo does not silently become blocking. Drop that bullet from W4.
- **W3 / arXiv.** `arxiv_client.py:41-109` trips on any failure; the "stuck half_open" claim holds for Semantic Scholar only (and there it stays half_open but is not blocked).
- **W3 / search.** Clients now raise on failure (commit d08531a), but `search_papers` swallows it and returns `[]`; the fix point moved to `search_papers`.
- **W1 line cites** for the pivot counter (PC-4) are partly off; the persisted counter is right and corrupt-file reads-as-0 is the defect.
- **Reachability open question settled.** `copilot`, `servers`, `collaboration`, `plugins`, `presets`, `hooks`, `skills`, `ui`, `mcp.client/registry/transport`, `dashboard.metrics`, `server.pipeline_stages`, `web.*` clients and `modes.operation_mode` pass the gate only through `ENTRY_PREFIX` in `scripts/check_reachability.py`; nothing on `berb run` / `berb serve` imports them and none is in `.reachability-allowlist`. Live: `modes.workflow`, `wizard.quickstart/templates`, `commands`, `server`, `dashboard`, `mcp.server`.

## Strongest cross-cluster findings (all unverified unless noted)

Outage read as fact (the plan's W3 theme, now much wider):
- `verify.py` outage -> `HALLUCINATED`, cached with no TTL (LT); total outage scores integrity 1.0; retraction `UNKNOWN` skipped and cached 30 days; novelty says "proceed" during an outage.
- `FalsificationCritic` returns `[]` on LLM failure and stage 8 records `gate_passed` (BR-14); PRM judge outage scores 0.0 and the gate passes (BR-4); default web-fetch stub returns 200 so sources are stamped "verified" (BR-26); `verify_citation` maps "UNVERIFIED" to verified via `"VERIFIED" in content` (LL).
- Review placeholders enter the average (RI, confirmed seed); `plot_verdict` failed critic dilutes the gate (confirmed seed).

Money:
- Cost tracker singleton is never reset, so run 2 in a server process inherits run 1's spend; unpriced models record $0 (including the `deepseek-v4-flash` preset default) so budgets never trip (LL).
- Discovery budget cap inert: `StageResult` has no `cost_usd` (RL, PC).
- `BudgetGovernor` compares process-wide `total_usd()` to a $5 default (EX-02).

Resume / state loss:
- `--resume` of a finished run restarts at stage 1; archived `stage-NN_vN` outranks live `stage-NN` in readers; discovery state saved only after the loop; corrupt `decision_history.json` reads as 0 and resets the pivot cap (PC, RL).
- Veto marker and `degradation_signal.json` never reset between runs (RI-4/5).

Surfaces that lie:
- `berb write|experiment|review|rebuttal` print "Starting ..." and exit 0 having run nothing; `berb literature` prints "Stages: 1-8" and runs all 23; cancelled `berb wizard` writes `{}` and reports success; web "Approve & Continue" only closes the modal; the UI calls `/api/v1/research` endpoints the server lacks (SF).
- Three UI status vocabularies vs the server's `{running, completed, failed, stopped, idle}`; only three words overlap (S10).
- Dashboard collector shows stage 0 / `running` for every run (confirmed in planning; SF-1).

Possibly broken wired path (highest value to confirm first): `EX-03`, every real-sandbox Stage 12 search node ends `is_buggy` with score 0 if `run()` is called as it reads. `berb/trends/feeds.py` imports a nonexistent `search_s2` and always returns `[]`.

## Not done / not covered

- Defect claims not adversarially verified (P2).
- Parked modules and some stateless modules were read by grep or skim only; each cluster file lists them under "Unread / uncertain".
- No fix applied, no commit made. New untracked files: `scripts/find_implicit_state.py`, `tests/test_find_implicit_state.py`, `tasks/state_machines_census.tsv`, `tasks/census_parts/`, `tasks/baseline/`, the plan and this file.

## Next: P2 (classify and score)

Verify the High/Critical A rows with Sonnet agents (cheapest first: EX-03, the outage-as-fact group, cost-tracker reset, `--resume` of a finished run), score visibility × damage ÷ blast radius, then re-order W1-W7. W4 changes per the correction above.
