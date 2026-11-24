# Implicit state machines: discovery and consolidation plan

Drafted 2026-11-11 against `7338445` (branch `docs/map-literature`). Nothing here is started. Sizes are relative (S/M/L), not time.

An **implicit state machine** is state held in loose variables, flags, strings, counters, files or directory names, where the set of states and the legal transitions are not declared in one place. Examples: `{"status": "running"}`, `self._closed`, `_pivot_depth`, `stage-14_v2/`, the presence of `ensemble_veto_used.json`.

## Goal and the one decision behind it

Find every implicit state machine on a wired path. Then fix only the ones where the missing declaration causes wrong behaviour that someone can see.

**Decision: extend the house pattern already in `berb/pipeline/stages.py`. Do not add a library, a base class or a framework.** That file already has the right shape: a `StrEnum` of states, a frozen `TRANSITION_MAP`, a pure `advance()` that raises on illegal moves, and an append-only `EventStore` with `PipelineState.apply` replay. The trouble is that the rest of the code bypasses it. Making that existing pattern load-bearing improves all three experiences at once:

| | How the decision helps |
|---|---|
| UX | One status read model means the CLI, dashboard, web and chat show the same, true state, including `blocked_approval` and `paused`, which no surface shows today. |
| DX | One vocabulary, one writer, illegal transitions raise in tests instead of corrupting runs. No new dependency to learn. |
| AX | Agents (MCP, LLM stages reading artifacts) get typed, documented states and a catalogue with diagrams in `docs/map/`, instead of raw checkpoint JSON and inferred directory names. Outages stop being reported to agents as negative facts. |

Rules that follow from it:

1. **Rule of three.** A shared helper (for example a 15-line `check_transition(table, cur, new)`) is added only once three machines need the same code. Until then each machine gets its own `StrEnum` and transition table next to its owner.
2. **Leave loop-local counters alone.** `attempt`, `cycle` and `iteration` locals that never leave a function are not machines worth declaring. Catalogue them as class C (below) and move on.
3. **Additive persistence only.** `checkpoint.json`, `heartbeat.json`, `event_log.json`, `decision_history.json` and HTTP payloads gain fields; they never lose or rename one. Old runs must still resume and still display.
4. **Parked code is out of scope.** Anything PARK or EXEMPT in `.reachability-allowlist` is listed once and skipped. Unwired-but-not-allowlisted code (see "Open questions") goes to dead-code triage, not here.
5. **Absence of evidence is its own state.** Wherever a network failure, timeout or open breaker can produce a value that looks like a negative verdict, give it a distinct `UNAVAILABLE`/`SKIPPED` state and keep it out of caches and averages.

## Decisions needed before the marked waves

| ID | Decision | Blocks | Default if unanswered |
|---|---|---|---|
| D1 | Run-status source of truth: replay `event_log.json` (activates the unused `PipelineState`), or add fields to `checkpoint.json`? | W2 | event log, with checkpoint as fallback for runs that predate it |
| D2 | Add a gate approval surface (`berb approve <run> [--reject]`, plus persisted `blocked_approval`)? It is a feature, not a fix. | W4 | yes, CLI only; web and MCP later |
| D3 | HTTP `/pipeline/status` vocabulary: replace `completed`/`stopped`/`idle`, or keep them and add `run_status` beside them? | W5 | keep old keys, add `run_status` (additive) |
| D4 | Citation verdicts already cached as `hallucinated` under `~/.cache/berb/citation_verify` may be outage artefacts. Purge, or version the cache key? | W3 | version the cache key; never delete user cache files without asking |

## Model routing for subagents

Main session (Opus) owns design decisions, the classification calls in P2, and final review of each wave. Subagents:

| Task type | Model | Why |
|---|---|---|
| Mechanical census: run grep/AST patterns, list hits as `file:line`, count per module | `haiku` | No judgement needed |
| Re-verifying that cited `file:line` still says what the catalogue claims | `haiku` | Line lookup |
| Rendering catalogue rows into Mermaid `stateDiagram-v2` blocks | `haiku` | Template work |
| Cluster deep read (trace a candidate's writers, readers, persistence, concurrency) | `sonnet` | Needs cross-file reasoning |
| Adversarial verification of each High/Critical claim ("try to prove this is not a bug") | `sonnet` | Fresh eyes, not anchored on the finder |
| Characterization tests before a change; implementing one wave | `sonnet` | Bounded code work |
| Reviewing a wave's diff | `sonnet` (`ecc:python-reviewer` or `caveman:cavecrew-reviewer`) | Independent read |

One task per subagent. Never give a verifier the finder's conclusion, only the code location and the question.

## P0: Baseline (S)

- [ ] Branch off `main` (this plan's branch is a docs branch). One PR per wave.
- [ ] Record the baseline with `pytest -m "not slow and not e2e and not llm"`, `ruff check berb/ tests/`, `ruff format --check berb/ tests/`, `mypy berb/ --python-version 3.11` and `python scripts/check_reachability.py`. Write down failures that predate this work.
- [ ] Record the wired-module list from `check_reachability.py`. It is the denominator for "found all".
- Done when: baseline numbers and the wired-module count are at the top of the first PR.

## P1: Discovery, finding all of them (M)

Discovery runs in two passes so that "all" can be defended: a mechanical census that over-collects, then a deep read that confirms or discards.

### P1a. Signal census (haiku, one agent per signal group)

| # | Signal | How to find it |
|---|---|---|
| S1 | Assignment to an attribute or key named `status`, `state`, `phase`, `mode`, `stage`, `step`, `decision`, `verdict` | AST: `Assign`/`AugAssign` targets, `dict` literals with those keys |
| S2 | Boolean lifecycle flags mutated outside `__init__`: `_running`, `_closed`, `_active`, `_started`, `is_*`, `timed_out` | AST: attribute assignment of `True`/`False` in a method that is not `__init__` |
| S3 | String-literal comparisons against state words (`== "running"`, `in {"done", "failed"}`) | grep with the vocabulary list from S1 hits |
| S4 | `StrEnum`/`IntEnum` members assigned from more than one module, or compared as raw strings | AST: enum member references by module, and string equality with enum values |
| S5 | Module-global mutable state (`global` keyword, module-level dict or list mutated in functions) | grep `global `; AST module-level `Dict`/`List` names written in functions |
| S6 | File presence as state: `.exists()` on marker files (`topic.txt`, `ensemble_veto_used.json`, `quality_warning.txt`) | grep `.exists()` and `write_text` on fixed names |
| S7 | Directory names as state: `_v{N}`, `cycle-N`, `pending/` → `running/` → `done/`, renames | grep `rename`, `replace(`, f-strings building `_v` or `cycle-` paths |
| S8 | Retry, backoff and circuit-breaker loops: `attempt`, `while True`, `half_open`, `consecutive_*` | grep, then keep only loops whose state outlives the call |
| S9 | Persisted JSON with a status-like key (checkpoint, heartbeat, stage meta, summaries) | grep `json.dump` near keys from S1 |
| S10 | Client-side vocabularies in `berb/ui/web` (TypeScript unions like `'queued' \| 'running'`) | grep `.ts`/`.tsx` |
| S11 | Free-string `decision` or `run_status` fields shared between writers | grep the field name across `berb/pipeline/` |
| S12 | Lifecycle methods with no order guard (`start`/`stop`/`close`/`end` callable twice or out of order) | AST: classes that define two or more of these methods |

Write `scripts/find_implicit_state.py` (stdlib `ast` only, about 150 lines) to run S1, S2, S4, S5 and S12, and grep for the rest. Keep the script because P5 turns it into a ratchet. Add one fixture-based test for it.

Output: `tasks/state_machines_census.tsv` with columns `signal`, `file:line`, `snippet`, `module`, `wired` (from the allowlist).

### P1b. Cluster deep read (sonnet, one agent per cluster)

Use the same clusters as the map (`docs/map/objects/`): pipeline-core, research loop, surfaces (server, websocket, dashboard, CLI, MCP, wizard), llm, experiment and sandboxes, literature, review and integrity, bridges. Each agent gets its slice of the census plus the seed rows below, and returns one row per machine:

`id` | `file:line` | holder | states (exact literals) | transition sites | persisted where | concurrency | who sees it (user / developer / agent) | wired? | suspected defect

### P1c. Coverage check, the proof of "all"

- [ ] Every wired module from P0 appears in the catalogue with either at least one machine or a line `none: <reason>` (for example "stateless AST visitor").
- [ ] Every census hit is either mapped to a catalogue id or dismissed with a reason.
- Done when: both lists have zero unexplained rows. A haiku agent produces the diff; the main session decides the leftovers.

## P2: Classify and prioritise (S)

Each catalogue row gets one class:

| Class | Meaning | Action |
|---|---|---|
| A | Machine with a live defect (wrong state shown, stuck state, illegal transition, lost on resume, outage read as fact) | Fix in a wave, test first |
| B | Same concept encoded in a second vocabulary (status strings that shadow `StageStatus`) | Consolidate onto the owner's enum |
| E | Explicit enum but transitions scattered and unguarded | Add a transition table and a single writer |
| C | Loop-local counter or one-shot flag, correct as is | Catalogue only |
| D | Parked or unwired | One line, link to the allowlist entry |

Score A, B and E rows on three axes, each 1 to 3: **visibility** (does a user or an agent act on the wrong state?), **damage** (wrong paper content, spend, lost work, security), **blast radius** (callers and persisted formats touched). Order the waves by visibility × damage ÷ blast radius. Every High or Critical row gets an adversarial sonnet verification before it is scheduled.

## P3: Catalogue for agents and developers (S)

- [ ] `docs/map/state_machines.md`: one section per class A, B and E machine with a Mermaid `stateDiagram-v2`, the owner file, the single writer, the persisted location and the "if you change this" list. Class C and D are one table at the end.
- [ ] Link it from `docs/map/CLAUDE.md` ("Route by what you need": "about to change a status or lifecycle → `state_machines.md`"), and keep `AGENTS.md` and `routing.md` byte-identical as the map requires.
- [ ] Link each machine from its cluster card in `docs/map/objects/` where one exists.

## Fix waves

Each wave has the same gate: characterization tests that pin current behaviour first (they fail only where the wave intends to change behaviour), then the change, then the P0 baseline commands, then a sonnet review. Old persisted files from `tests/` fixtures must still load.

### W1. Make the house FSM load-bearing in the pipeline core (M)

- [ ] `berb/pipeline/runner.py:172-244`: build transition events from `advance()` output, not by hand. A gate result is currently logged as `TransitionEvent.FAIL` (`runner.py:235`); it should be `SUCCEED` with `to_status=BLOCKED_APPROVAL`, which is what `advance()` already returns.
- [ ] `runner.py:82-84`: the hand-built `DONE → RUNNING` event labelled `SUCCEED` goes through `advance()` or is removed.
- [ ] `berb/pipeline/executor.py:223`: `_ = advance(...)` discards the result. Use it as the guard or delete the line.
- [ ] `StageResult.decision` becomes a `StrEnum` (`proceed`, `retry`, `block`, `degraded`, `pivot`, `refine`). Fix `PipelineState.apply` so that `refine` is counted (`stages.py:421-439`). Accept old strings when reading old event logs.
- [ ] `from_status` comes from the stage's own last status, not the loop-local `previous_status` shared by parallel stages (`runner.py:388, 443, 462, 473`).
- Done when: every event appended to `event_log.json` passes `advance()`, and a test replays a real run's log to the same final `PipelineState` as the runner's view.

### W2. One run-status read model (M, keystone for UX and AX) [D1]

Today the dashboard, HTTP, MCP and chat each invent a status, and all of them are wrong:

- `berb/dashboard/collector.py:91-95` reads `stage`, `stage_name`, `status`, `topic` and `start_time`, but `checkpoint.json` writes none of them (`berb/pipeline/checkpoint.py:66-71`). Every run shows stage 0 and `running`.
- `collector.py:105-106` subtracts an ISO string (`checkpoint.py:47`) from `time.time()`. The `TypeError` is swallowed, so `is_active` is always `False`.
- `berb/mcp/server.py:66-78` returns raw checkpoint JSON or `"no_checkpoint"`.
- `berb/server/routes/pipeline.py:130-133` reports a gate-blocked run as `completed`.

Work:

- [ ] Add `RunStatus` (`StrEnum`: `pending`, `running`, `blocked_approval`, `paused`, `failed`, `done`, `stopped`), defined next to `StageStatus` and derived from it. A docstring states the mapping.
- [ ] Add `read_run_status(run_dir) -> RunStatusView` in `berb/pipeline/` (frozen dataclass: run status, current stage and name, per-stage statuses, last heartbeat, liveness, last error, pivot count). Source per D1: event-log replay, with a checkpoint fallback for old runs. Liveness uses the heartbeat timestamp parsed as ISO, plus a pid check.
- [ ] Route all four readers through it: the dashboard collector, `/pipeline/status` (additive `run_status` key, D3), MCP `get_pipeline_status` (typed fields beside the raw `checkpoint` key), and the chat `CHECK_STATUS` handler (`server/dialog/router.py:51`).
- [ ] Fix `berb/dashboard/broadcaster.py` diffing so that `stage_complete` can fire once the stage is real.
- Done when: one fixture run directory in each state renders the same status through all four surfaces (a single parametrised test).

### W3. Outage is not a verdict (M, highest damage) [D4]

- [ ] `berb/literature/verify.py:598-606`: an empty search result returns `HALLUCINATED` at confidence 0.7, and `verify.py:854-856` caches every status except `SKIPPED`, with no TTL. When the search was skipped or a breaker was open, return `SKIPPED`. This needs the search layer to say "unavailable" instead of `[]`; the recon says `berb/literature/search.py:203-262` returns `[]` for an open breaker (verify that claim first). Version the cache key (D4).
- [ ] `berb/literature/semantic_scholar.py:58-142`: a `half_open` probe that fails with a non-429 error leaves the breaker stuck in `half_open`. Give the breaker a transition table covering every outcome. `arxiv_client.py:41-109` has the same shape, so the two plus `LLMClient`'s breaker (`berb/llm/client.py:304-412`) meet the rule of three: one shared `CircuitBreaker` class with tests is now justified. Reset module-global breaker state per run.
- [ ] `berb/literature/retraction.py:206`: `screen_bibliography` emits nothing for `UNKNOWN`, so an unchecked reference looks clean. Emit an advisory finding.
- [ ] `berb/review/ensemble.py:553-558, 635-654`: placeholder reviews from failed calls (`weak_reject`, 5.0) enter the average. Mark them unavailable and exclude them; report the count.
- [ ] `berb/experiment/search/runner.py:344` hard-codes `node.timed_out = False`. Read it from the sandbox result.
- [ ] `berb/experiment/plot_verdict.py:242`: one failed critic (confidence 0.0) dilutes the average and can open the gate. Exclude failed critics from the average.
- Done when: a test with every external source forced unavailable produces zero `HALLUCINATED`, zero cached negatives and zero placeholder scores.

### W4. Gate approval as a real state (M) [D2]

- [ ] Persist `blocked_approval` (event log per D1) so that `--resume` restores the gate instead of re-running the stage.
- [ ] `berb approve <run_dir> [--reject] [--reason]` appends `APPROVE`/`REJECT` through `advance()`; `REJECT` uses the existing `GATE_ROLLBACK`.
- [ ] Validate `config.project.mode` against a `StrEnum` (`full-auto`, `semi-auto`, `docs-first`). Today a typo silently becomes blocking (`berb/cli.py:252-262`). Collapse `--auto-approve`, `project.mode` and `stop_on_gate` into one derived gate policy.
- Done when: a semi-auto run stops at a gate, `berb approve` resumes it from the next stage, and `berb approve --reject` rolls back to the configured target.

### W5. Server run lifecycle (S-M) [D3]

- [ ] `berb/server/routes/pipeline.py:54-170`: replace the `_active_run` string status with `RunStatus` and a transition table. `/stop` on a finished run returns 409 instead of overwriting `completed` with `stopped` (`pipeline.py:156-161`). Stop waits for the task, and marks the run `stopping` until the worker thread has exited, so a new `start` cannot overlap the old run's writes.
- [ ] Emit the declared but never-sent `pipeline_started`, `pipeline_completed`, `stage_start` and `stage_fail` events (`server/websocket/events.py:12-37`), or delete them from the enum if D3 says not yet.
- [ ] WebSocket and chat lifecycle: handle every exception on disconnect (`server/app.py:126-136`, `routes/chat.py:64`), and remove the dialog session on disconnect (`dialog/router.py:13`).
- [ ] MCP: validate `run_id` the way `pipeline.py:21-29` does (`berb/mcp/server.py:70, 83, 111` build `Path(f"artifacts/{run_id}")` from caller input, which allows `../`). This is a security fix; do it first in the wave even if the rest slips.

### W6. Resume and rollback consistency (M-L, riskiest, last)

- [ ] Pivot cap: one source of truth. `decision_history.json` is the persisted one; `_pivot_depth` (`runner.py:338, 489, 669`) is derived from it so that `--resume` cannot reset the cap. A corrupt history file fails loudly instead of reading as 0 (`berb/pipeline/iterative.py:76-78`).
- [ ] Rollback ordering: write the pivot event and rewind `checkpoint.json` before renaming `stage-NN` to `stage-NN_v{N}` (`iterative.py:135-150`, `runner.py:655-656`), so a crash mid-rollback resumes safely. Do not `rmtree` an existing `_vN`.
- [ ] Checkpoint monotonicity under parallel DAG levels (`checkpoint.py:189-192`): never write a lower `last_completed_stage` than the one on disk. The recon marked this as inferred; prove it with a test first.
- [ ] Discovery loop: restore budget spend and the cycle counter from `world_model.json`, and make one place own `current_cycle` (`berb/research/discovery_loop.py:290`, `world_model.py:166`).
- [ ] Iterative loop: persist iteration scores; ignore a `quality_report.json` older than the current iteration (`iterative.py:106, 310-399`).
- [ ] `run_status` vocabulary in `stage_impls/_execution.py:223-237` and `experiment_repair.py:916`: one shared `StrEnum`.

### W7. Sandbox lifecycle (S-M)

- [ ] Lock `_run_counter` in the Docker (`berb/experiment/docker_sandbox.py:198, 218, 242`) and SSH (`ssh_sandbox.py:78, 97`) sandboxes, matching the local sandbox (`sandbox.py:464`). Clear a stale staging directory in `docker_sandbox.run()`.
- [ ] Kill the process group on timeout in the local sandbox, and kill the remote process before `rm -rf` over SSH.
- [ ] Colab: on timeout, also handle a task already in `running/`, and respect the caller's shorter timeout (`colab_sandbox.py:303-358`).

## P5: Guard against regressions (S)

- [ ] Turn `scripts/find_implicit_state.py` into a ratchet in the same shape as `check_reachability.py`: count raw state-word literals assigned to `status`/`state` fields outside the owning enum's module, and fail CI if the count rises. An allowlist holds the class C rows. Never raise the ceiling to make a build pass.
- [ ] Add the ratchet to the Lint job in `.github/workflows/ci.yml`.
- [ ] Add a short "State and lifecycle" section to the root `CLAUDE.md`: owner enum, transition table, single writer, additive persistence, a link to `docs/map/state_machines.md`.

## Seed inventory from the recon

Three sonnet recon agents produced these rows on 2026-11-11. ✔ means the main session re-read the lines and confirmed them; the rest go to P1b for verification. This is a starting point, not the catalogue.

| Id | Where | Holder | Class (provisional) | Note |
|---|---|---|---|---|
| PC-1 ✔ | `pipeline/runner.py:172-244` | hand-built `StageTransitionEvent` | A | gate logged as `FAIL`; bypasses `advance()` |
| PC-2 ✔ | `pipeline/executor.py:223` | `_ = advance(...)` | A | result discarded |
| PC-3 ✔ | `pipeline/stages.py:406-439` | `PipelineState`, `EventStore.replay` | E | no runtime caller |
| PC-4 | `runner.py:338` vs `iterative.py:67-103` | `_pivot_depth` and `decision_history.json` | A | two pivot counters; memory one resets on resume |
| PC-5 | `iterative.py:135-150` | `stage-NN_v{N}` directory renames | A | rollback not atomic (inferred) |
| PC-6 | `checkpoint.py:60-202` | `checkpoint.json` (DONE only) | A | gate, discovery and iteration state lost on resume |
| PC-7 | `research/discovery_loop.py:288-319` | `stop_reason`, budget, `current_cycle` | A | two cycle writers; budget not restored |
| PC-8 | `stage_impls/_execution.py:223-237`, `experiment_repair.py:916` | `run_status` strings | B | overlapping vocabularies |
| PC-9 | `stage_impls/_review.py:864-871` | `ensemble_veto_used.json` marker | A | written before gate outcome; never reset on rollback |
| SF-1 ✔ | `dashboard/collector.py:85-110` | `RunSnapshot.status`, `is_active` | A | reads keys that are never written; str minus float |
| SF-2 ✔ | `server/routes/pipeline.py:150-170` | `_active_run["status"]` | A/B | stop overwrites completed; blocked shows completed |
| SF-3 ✔ | `mcp/server.py:66-85` | raw checkpoint, unvalidated `run_id` | A | path traversal; untyped status for agents |
| SF-4 | `server/websocket/manager.py`, `events.py` | connections, 16-member `EventType` | A | 8 event types never emitted; queue drained every 15 s |
| SF-5 | `server/dialog/router.py:13`, `session.py:28-35` | chat sessions | A | never freed; `current_project`/`current_run` dead |
| SF-6 | `cli.py:252-262` | `--auto-approve` + `project.mode` + `stop_on_gate` | A | one mode in three variables; no approve command |
| SF-7 | `mcp/server.py:25-132` | `_running` | A | `berb mcp --start` returns at once; no transport |
| SF-8 | `berb/ui/web` (`api.ts:15`, `types/index.ts:255`) | two TS status unions | B/D | no live backend; mock data |
| SF-9 | `copilot/`, `modes/operation_mode.py` | `ResearchMode`, feedback action strings | D? | appear unwired; confirm in P1 |
| IN-1 ✔ | `literature/verify.py:598-606, 854-856` | `VerifyStatus` + disk cache | A | empty search result cached as `HALLUCINATED` |
| IN-2 | `literature/semantic_scholar.py:58-142`, `arxiv_client.py:41-109` | module-global breakers | A | stuck `half_open`; never reset between runs |
| IN-3 | `llm/client.py:304-412, 764-863` | `CircuitBreakerState`, retry loop | A | shared breaker across fallback chain; final status lost |
| IN-4 | `llm/client.py:1277` | `_current_provider_idx` | C/A | never reassigned; no provider health memory |
| IN-5 | `llm/model_cascade.py:182-247` | rung index, `last_response` | A | last-rung error returns a cheap rejected answer |
| IN-6 | `llm/cost_tracker.py:132-317` | `_closed` | A | events dropped silently after close; no budget state |
| IN-7 | `llm/nadirclaw_router.py:490-595` | TTL cache dicts | A | unlocked mutation |
| IN-8 | `experiment/docker_sandbox.py:198-456`, `ssh_sandbox.py`, `colab_sandbox.py`, `sandbox.py` | run counters, staging dirs, Drive dirs | A | races and orphans on timeout |
| IN-9 ✔ | `experiment/search/runner.py:182-344` | search loop, `JournalNode` flags | A | `timed_out` forced False (✔); busy-spin on empty journal and failed nodes bypassing `max_nodes` not yet checked |
| IN-10 | `experiment/plot_verdict.py:230-249` | averaged confidence | A | failed critic dilutes the gate |
| IN-11 | `review/ensemble.py:341-416, 553-675` | placeholder reviews, batch poll | A | placeholders averaged; submitted batch not cancelled |
| IN-12 | `literature/retraction.py:206, 318` | `RetractionState.UNKNOWN` | A | silent for unknown |
| IN-13 | `integrity/claims.py:63-149` | `ClaimVerdict` | E/C | set once at creation; unknown coerced to `not_checked` |
| IN-14 | `metaclaw_bridge/session.py:19-45` | `_active` | C | meaningless flag |

Parked and skipped (from the allowlist): `berb.hyperagent` (`AgentPhase`), `berb.i18n`, `berb.voice.*`, `llm.batch_api`, `llm.speculative_*`, `llm.adaptive_temp`, `experiment.compute_guard`, `experiment.progress`, `experiment.self_correcting`, `experiment.evolutionary_search`, `integrity.eval.hidden_eval` and the rest listed in `.reachability-allowlist`.

## Open questions for P1

- `copilot/` and `modes/operation_mode.py` have no importer that the recon could find, and are not in the allowlist. Either the reachability gate counts package `__init__` imports, or they are dead and the gate misses them. Settle this before cataloguing them.
- The recon's infrastructure pass saw some grep output truncated, so the allowlist may hold more entries in scope than listed above.
- Not yet read: `pipeline/tracing.py`, `packaging.py`, `contracts.py`, `summary.py`, most of `stage_impls/`, `server/routes/uploads.py` and `projects.py`, `modes/workflow.py` internals, and `wizard/` step handling.

## Done when

- The coverage check in P1c has zero unexplained rows.
- Every class A row is fixed with a test, or deferred with a written reason.
- Every class B row uses its owner's enum.
- `docs/map/state_machines.md` exists and is linked from the map entry file.
- The ratchet runs in CI.
- The P0 baseline commands are no worse than at the start.

> **P0+P1 done 2026-11-11:** results and plan corrections (notably W4 / SF-6) are in `tasks/state_machines_p1_results.md`.

> **P2 done 2026-11-24:** verified/ranked defects and the revised wave order are in `tasks/state_machines_p2_results.md` (W1 re-scoped, W7 mostly dropped, W4 GATE_ROLLBACK note).
