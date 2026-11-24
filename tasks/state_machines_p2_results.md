# P2 results: verified and ranked state-machine defects

2026-11-24, branch `chore/state-machine-census`. Input: P1 (`tasks/state_machines_p1_results.md`). Method: 7 independent Sonnet agents tried to falsify every class A/B/E row (137 rows), tracing live callers and reproducing in tmp dirs or with in-process fakes where possible; no network, no repo edits. Per-row evidence, test sketch and fix direction: `tasks/p2_ranked.tsv` (113 live rows, ranked) and `tasks/census_parts/p2_g*_verdicts.tsv` (all 137).

Score = V × D ÷ B (visibility, damage, blast radius of the fix, each 1-3). The score ignores whether the path is on by default, so the table below adds a **default?** column.

## Verdicts

| CONFIRMED | PARTLY | UNREACHABLE | REFUTED |
|---|---|---|---|
| 65 | 48 | 19 | 5 |

The P1 claim count of ~117 class A defects was inflated: 113 survive as real or partly real, 24 do not. PARTLY means real but narrower than claimed; read the evidence column before scheduling.

## Highest-impact rows

Grouped by theme, not strictly sorted by score (RI-1 and BR-14 score lower on fix blast radius but are default-on and silent). Full ranking: `tasks/p2_ranked.tsv`.

| # | Id | Score | Default? | What happens |
|---|---|---|---|---|
| 1 | EX-03 | 9.0 | no (`experiment.search.enabled`, default False) | Stage 12 tree search calls `sandbox.run()` with no `code`; `TypeError` is caught, every node is buggy, stage returns DONE with no run files. Reproduced. |
| 2 | BR-31 | 6 | yes (`berb trends --digest`) | Always prints "No new papers found": `feeds.py` imports nonexistent `search_s2` and calls `.get()` on `Paper` dataclasses. |
| 3 | PC-12 | 6 | yes | A gate stage (5, 9, 20) that crashed or returned FAILED is rewritten to `BLOCKED_APPROVAL`. |
| 4 | RI-3 | 6 | yes | A reviewer reply that omits a field raises `KeyError`; stage 20 swallows it at debug level, no review, no veto, gate passes. Reproduced. |
| 5 | RI-1 | 3 | yes | Failed reviewer calls are scored as real 5.0 votes; one real 3.0 plus five failures averages 4.63 and REJECT never fires. Reproduced. |
| 6 | RI-4 | 6 | yes | `ensemble_veto_used.json` never reset; a `--resume` rerun lets the same REJECT through. The automatic rollback the row assumed does not exist. |
| 7 | RI-11/RI-12 | 6 | yes | `integrity.mode` is never validated (a typo disables gates); `fail_on_*` flags have no reader. |
| 8 | SI-04 | 6 | yes | A decision line starting with a negated PIVOT, or a later "Refinements" line, overrides the real decision. |
| 9 | SF-25, SF-27 | 6 | yes | Monitor view shows hard-coded stage 7 / 78% for every run; `berb wizard` with a blank topic overwrites the output file with `{}` and exits 0. |
| 10 | LL-5, LL-8 | 6 | yes | Cost tracker never reset (run 2 in `berb serve` inherits run 1; stage-12 budget counts all earlier spend); unpriced models (`deepseek-v4-flash`, `gpt-5.2`, `MiniMax-M2.5`, `claude-sonnet-4-5`) record $0 so budgets never trip. |
| 11 | LT-1, LT-2, LT-7 | 4.5 | yes | Total source outage marks real citations `HALLUCINATED` at 0.7, cached with no TTL (reproduced); retraction `NONE` cached 30 days on a partial outage, keyed by `cite_key`. |
| 12 | PC-5, SI-03 | 4.5 | yes | After a PIVOT, `_find_prior_file` returns archived `stage-NN_v1` over live `stage-NN`; stage 9 reads stale hypotheses. If stage 8 then fails, `--resume` continues on archived results. |
| 13 | PC-6 | 4.5 | yes | `--resume` of a finished run restarts at stage 1; a parallel level with 10 FAILED and 11 DONE leaves checkpoint 11 and resume skips stage 10. |
| 14 | PC-10 | 4.5 | yes | Stages 13 and 14 share a DAG level; 14 needs 13's `selection_bias.json` and fails "Missing input" when 13 is slow. A failed sibling also stops the level loop before completed siblings are recorded. |
| 15 | SF-2 | 4.5 | yes | `/pipeline/start` without `auto_approve` never passes `stop_on_gate`, so runs pass gates and end "completed"; `/stop` overwrites a finished run's status; the cancelled stage's thread keeps running (reproduced) and a new start is allowed. |
| 16 | BR-14 | 3 | yes | `FalsificationCritic` returns `[]` on any LLM failure; stage 8 records `gate_passed=true`. |
| 17 | LL-22 | 6 | no (provider `acp`) | `ACPClient.chat` has no `stage` parameter; `_chat_with_prompt` passes it at 30 call sites, so every stage fails. Reproduced. |

Flag-gated or default-off: EX-03, EX-02 (`search.enabled`), BR-4 (`prm.enabled`), LL-9 (`cascade.enabled`), LL-22 (`acp`), RI-16 (`BERB_EXPERIMENTAL_PARALLEL_WRITER=1`), BR-26 (`use_web_fetch`). These rank high on score but touch few users today.

## What changed in my own earlier claims

- **W1 is not the keystone.** PC-1 and PC-2 (the house FSM bypass and the discarded `advance()`) score V1 D1: nothing consults `TRANSITION_MAP` (PC-3b is unreachable) and the logged event vocabulary has no reader. The real W1 defects are PC-12 (failed gate shown as blocked), PC-5/SI-03 (archived output wins) and PC-4 (third PIVOT ignored). Re-scope W1 to those.
- **`GATE_ROLLBACK` is never read by the runner or executor.** W4's "REJECT uses the existing `GATE_ROLLBACK`" is wrong; the rollback must be wired, not reused. SI-05/06/07 assumed it existed and drop to PARTLY.
- **W5 MCP path traversal (SF-3) is UNREACHABLE.** `berb mcp --start` serves nothing (SF-7); no live caller of `handle_tool_call`. Demote from "do first"; a cheap defensive `run_id` check is still fine. Traversal could only read files named `checkpoint.json`, `experiment_results.json`, `paper_draft.md` or `paper.tex`.
- **W7 sandbox lifecycle is mostly UNREACHABLE** (EX-09, 15, 16, 17, 18). Drop W7 except EX-12 (CONFIRMED, V2 D2) and re-check before scheduling.
- **W4 `project.mode` bullet:** already struck in P1. The server route ignores `project.mode` and defaults `auto_approve=True` instead (SF-2 / PC-26).
- **SF-13 corrected:** `berb literature` crashes with `FrozenInstanceError` at `cli.py:966` rather than spending 23 stages; `write`, `experiment`, `review`, `rebuttal` are no-ops that exit 0.
- **W3 widened:** the `HALLUCINATED`-on-outage fix lives in `verify.py`, but retraction (LT-7), review placeholders (RI-1/RI-3), `FalsificationCritic` (BR-14) and PRM (BR-4) share the shape "failed check reads as a clean result". The shared fix is one explicit `UNAVAILABLE` state, not seven local patches.

## Proposed wave order (for your approval, nothing started)

Ordered by score, default-on first, smallest blast radius first. Every wave starts with characterization tests that fail today.

1. **Review gate that cannot fail** (RI-1, RI-3, RI-4, BR-14): failed reviewer/critic = unavailable, excluded from averages and counted; tolerate missing JSON fields; reset the veto marker per attempt. Blast radius 1-2 files.
2. **Outage is not a verdict** (LT-1, LT-2, LT-7, BR-4): `UNAVAILABLE` state, no cache of outages, version the citation cache key (D4), retraction cache keyed by DOI.
3. **Money** (LL-5, LL-8, EX-02): reset or scope the cost tracker per run; unknown model price = loud warning and a conservative default, not $0.
4. **Resume and pivot correctness** (PC-5/SI-03, PC-6, PC-10, PC-12, PC-4, SI-04): prefer live over archived directories, resume of a finished run is a no-op with a message, split 13/14 into separate levels, stop recording FAILED as blocked.
5. **Server and CLI honesty** (SF-1, SF-2, SF-25, SF-27, SF-13, BR-31): one run-status read model (old W2), `/stop` returns 409 on a finished run, `stop_on_gate` passed, no-op commands say so, `berb trends` works or errors.
6. **Config validation** (RI-11/RI-12): enum-validate `integrity.mode`; wire or delete the `fail_on_*` flags.
7. **Flag-gated** (EX-03, LL-22, LL-9, BR-26, RI-16): fix when the flag is about to be turned on; EX-03 is a one-function adapter plus a test.

Not scheduled: UNREACHABLE and REFUTED rows (24), recorded in the verdict files so they are not re-found.

## Limits of this verification

- CONFIRMED means traced through callers by an agent, with a reproduction for most PC, RI, LT, SF and EX-03 rows; the SI rows (except SI-03, SI-04) and PC-20/21 rest on code reading. I re-checked the EX-03 call site myself; I did not re-run the others.
- One agent accidentally made a single live OpenAlex GET with query "q" while testing LT-5 (wrong patch target), then re-ran it with the right patch.
- Wave scores use agent-assigned V/D/B; treat the ordering inside a score band as a tie.
