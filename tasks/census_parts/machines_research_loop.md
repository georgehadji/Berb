# P1b cluster read: research_loop (RL-)

Scope: `berb.research`, `berb.project`, `berb.memory`, `berb.knowledge`, `berb.learning`, `berb.self_evolve`, `berb.hyperagent`, plus `berb/pipeline/discovery.py` and `berb/pipeline/iterative.py`. Read-only. All lines re-read this session. "wired" is the reachability verdict from `tasks/baseline/wired_modules.txt`; where the verdict and real callers disagree, the cell says so.

## Machines

| id | file:line | holder | states (exact literals) | transition sites (file:line) | persisted where | concurrency | who sees it | wired? | class | suspected defect |
|---|---|---|---|---|---|---|---|---|---|---|
| RL-1 | `research/discovery_loop.py:269-328`; `world_model.py:130,166` | `DiscoveryLoop.run` locals + `DiscoveryResult.stop_reason` + `WorldModel.current_cycle` | stop_reason: `"disabled"`, `"no_executor"`, `"no_tasks_remaining"`, `"converged"`, `"budget_exhausted"`, `"max_cycles_reached"`; cycle int 0..max_cycles+1 | `discovery_loop.py:279,283,297,306,311,319` (stop_reason); `:290` (`wm.current_cycle = cycle`); `world_model.py:166` (`current_cycle += 1` in `update`, called `discovery_loop.py:389`) | `current_cycle` in `world_model.json` only (`world_model.py:251`, written once at end `pipeline/discovery.py:367`). `stop_reason` not persisted (printed `runner.py:309-312`) | cycles sequential; tasks within a cycle `asyncio.gather` (`discovery_loop.py:335`) | developer, user (stdout line), agent (world_model.json) | Y (`research.discovery.enabled`, default off) | A | Two writers of `current_cycle` agree mid-loop (set to N at :290, bumped to N+1 at :166) but leave N+1 after a normal exit and N after a `no_tasks_remaining` break; the loop never reads the restored value (`for cycle in range(1, ...)` :288), so a rerun over a restored model restarts numbering at 1 and duplicates `source_cycle` values, and a restored already-converged model still runs one full cycle before `converged()` is checked (:304). |
| RL-2 | `discovery_loop.py:184-204`; `pipeline/discovery.py:322-324`; `pipeline/_helpers.py:74-83` | `BudgetGovernor.spent_usd/exhausted` | `exhausted` False/True (sticky); `spent_usd` float | `discovery_loop.py:302` (`budget.spend`), `:196` (sets exhausted), `:309` (check, after the cycle, after the convergence check) | not persisted (`WorldModel.to_dict` has no spend; governor rebuilt `discovery_loop.py:267`) | single-threaded update after gather | developer | Y | A | `_slice_cost` sums `getattr(r, "cost_usd", 0.0)` over `StageResult`, which has no `cost_usd` field (`_helpers.py:74-83`), so every outcome costs 0.0 and `research.discovery.budget_usd` can never trip; also spend is not restored on a rerun and the cap is checked only after a whole cycle ran (overshoot up to width tasks). |
| RL-3 | `world_model.py:83-131,133-245` | `WorldModel` slots | lists `established`, `refuted`, `open_questions`, `contradictions`, `dead_ends`; `guidance`; `current_best_explanation`; derived `converged()` | add: `world_model.py:150-157`; cap-drop-oldest `:168-171`; guidance set `discovery_loop.py:382`; no removal path for questions/contradictions | `world_model.json` (`to_dict` :247-260, `from_dict` :263-283); `max_list_size` not saved; `converged` saved but derived | one writer (post-gather) | agent (file), developer | Y | A | An open question or contradiction is never closed: `converged()` stays False while any contradiction exists or a question has `priority > 0.7` (:240-244), and a question whose task produced a non-empty outcome is proposed again every cycle (only empty outcomes add a dead end, `discovery_loop.py:361-370`); `_cap_list` silently drops the oldest established findings and dead ends past 50, enabling re-exploration. |
| RL-4 | `research/world_model.py:22-26`; `pipeline/discovery.py:231-302` | `FindingVerdict` + slice verdict read from stage 15 | `FindingVerdict.SUPPORTED="supported"`, `REFUTED="refuted"`; slice decision free string compared to `"PROCEED"`, else `""` = no decision, else any other word = refuted | `discovery.py:248` (`== "PROCEED"`), `:263` (`not decision`), `:270` (else-branch), `:302` (`str(...).upper()`); list placement in `world_model.update` | `world_model.json` (verdict inside findings); `discovery/index.jsonl` `admitted` bool | per-task, concurrent tasks | agent | Y | B | Verdict is encoded twice (enum field and list membership) and a third time as the stage-15 `decision` string (`proceed/pivot/refine` in `StageResult.decision`, upper-cased here); any non-`PROCEED` text, including an unexpected value like `"PROCEED "` (no strip, :302), becomes a REFUTED finding plus a new open question, which feeds RL-3's never-closing questions. |
| RL-5 | `pipeline/discovery.py:53-71,103-125,130-156,159-206,209-228,327-368`; `runner.py:275-322,398-415` | discovery artifacts on disk: `world_model.json`, `discovery/index.jsonl`, `discovery/cycle-N/<uuid8>/`, `task.txt`, promoted `stage-07..15` copies | task dir exists; index line `admitted` true/false; promoted = non-empty return of `promote_best_task` | `discovery.py:104-106` (create), `:155-156` (append index), `:203` (`copytree ... dirs_exist_ok=True` promote), `:367` (save model after loop), `runner.py:401-415` (skip slice) | files above; promotion is not checkpointed (`checkpoint_mgr.write` only on DONE, `runner.py:598-599`; `read_checkpoint` returns next stage, `checkpoint.py:132-165`) | tasks append `index.jsonl` concurrently in one event loop (sync write, interleave-safe in-process) | developer, user | Y | A | World model is saved only after the whole loop (`discovery.py:366-367`), so a crash mid-loop loses all epistemic state while `index.jsonl` keeps the crashed attempt's lines (never truncated) and `promote_best_task` may promote a slice the model never saw; and if the run fails in stage 16 before its checkpoint, resume restarts at stage 7 (checkpoint still at 6) and reruns the whole discovery loop, spending again. |
| RL-6 | `pipeline/iterative.py:310-430` | `execute_iterative_pipeline`: `iteration_scores`, `score`, `converged`, `all_results` | locals; summary keys `total_iterations`, `converged`, `met_threshold`; score `None` or float | `iterative.py:352,398` (append), `:356-362` (threshold stop), `:364-374` (convergence stop), `:401-406` | `iteration_summary.json` at end only (`:419-421`); `iteration_context.json` per iteration (`:132`); read by `experiment/visualize.py:786`, `_paper_writing.py:79` | sequential | developer, user | module Y; **function has no caller** in `berb/` (only docs and `.claude/skills/researchclaw/SKILL.md`) | D | Latent if wired: scores live only in memory, so a crash loses history and a rerun restarts at "Iteration 1" with `from_stage` default `TOPIC_INIT` (`:342-349`); `read_quality_score` reads `stage-20/quality_report.json` with no freshness check (`:106-119`), so an iteration that dies before stage 20 re-reads the old score and trips "unchanged for 2 rounds" (`:368`). |
| RL-7 | `pipeline/iterative.py:67-103`; callers `runner.py:621,642` | `decision_history.json` as the pivot counter | JSON list of `{"decision","rollback_target","rollback_stage_num","attempt","timestamp"}`; count = `len(list)` | append `iterative.py:94-103` (called `runner.py:642`); read `:67-78` (called `runner.py:621`) | `decision_history.json`, plain `write_text`, not atomic (`:103`) | read-modify-write, no lock; DAG levels run concurrently but pivots are in the decision stage only (unverified) | developer, agent | Y | A | A corrupt or non-list file reads as 0 (`:76-78`) so the pivot cap resets; `record_decision_history` then starts from `[]` and overwrites the remaining history (`:87-103`); the `attempt = pivot_count + 1` that results can collide with an existing `stage-NN_v1`, which `_version_rollback_stages` `rmtree`s (:148-149). Counts every entry, so "PIVOT/REFINE" mixing is by design. |
| RL-8 | `pipeline/iterative.py:135-150`; caller `runner.py:655` | `stage-NN` -> `stage-NN_v{attempt}` renames for NN in rollback..15 | dir `stage-NN` / `stage-NN_v{attempt}` present or absent | `iterative.py:148-150` (`rmtree` existing version dir, then `rename`); history written before (`runner.py:642`), pivot event appended after (`runner.py:657-658`) | directory names | single caller | developer, agent (stage dirs) | Y | A | Not atomic: a crash between `record_decision_history` and the loop (or mid-loop) leaves the cap consumed with some stages renamed and some not, and nothing rewinds `checkpoint.json` here; only stages rollback..15 are renamed, so stage 16+ output from the earlier pass stays in place and is read by the rerun (unverified for stages that do not overwrite). |
| RL-9 | `pipeline/iterative.py:153-241,244-307`; callers `runner.py:184,625,671,695` | promoted-best marker files `experiment_summary_best.json`, `analysis_best.md`, and the overwrite of `stage-14/` | file present or absent; dir `stage-14*` candidates | `iterative.py:214-217` (write best copies), `:226-241` (overwrite `stage-14/` from the best dir) | run-root marker files, read by `_analysis.py:928`, `_archive.py:159`, `_paper_writing.py:1479`, `_review.py:549`, `verified_registry.py:278,326`, `_metric_helpers.py:84` | none | developer, agent | Y | A | When the best candidate is an older `stage-14_vN`, the current `stage-14/experiment_summary.json` and `charts/` are overwritten with no backup of the latest iteration (`:226-241`), so later `_consecutive_empty_metrics` (`:35-61`) compares an older iteration as "current" (unverified whether this masks empty metrics in practice). |
| RL-10 | `project/models.py:10-34`; `project/manager.py:168-182,185-190` | `Project.status` | `"idle"` (default :17), `"running"`, free string passed to `finish_run` (comment says `completed`, `failed`) | `manager.py:171` (`proj.status = "running"` in `start_run`), `:179` (`proj.status = status` in `finish_run`, no validation) | `registry.json` via `_save_registry` (`:46-55`) | no lock between CLI processes | user (`berb project list` prints `[{p.status}]`, `cli.py:493-495`) | Y (CLI `berb project`, `cli.py:480-518`); `start_run`/`finish_run` have no caller in `berb/` | A | `berb project list` can only ever show `[idle]`, because `berb run` never calls `start_run`/`finish_run`; a project left `running` by a crash would never be reset (no recovery), and `finish_run` accepts any string. |
| RL-11 | `project/manager.py:24,29-55,91-92,102-103,133` | `ProjectManager._active` + `registry.json` | `_active`: project name or `None` | `manager.py:92` (first create), `:103` (delete picks `next(iter(...))`), `:133` (`switch`) | `registry.json` (`write_text`, non-atomic `:53-55`) | read-modify-write, no lock | user | Y | A | `_load_registry` catches `JSONDecodeError`/`KeyError` and leaves `projects` empty (`:43-44`), so the next `create`/`switch` rewrites the registry with only the new entry and the whole previous registry is lost; a crash during `write_text` truncates it the same way. |
| RL-12 | `project/models.py:56-72`; `project/idea_pool.py:73-106` | `Idea.status` | `"draft"` (default :63), `"evaluated"`, `"planned"`; `"running"`, `"completed"` named in the comment but never written | `idea_pool.py:78` (`"evaluated"`), `:104` (`"planned"`) | pool JSON (`idea_pool.py:37-40`) | none | developer | module Y via `project/__init__`; **no caller outside the package and no CLI route** | D | Latent: `evaluate` sets `"evaluated"` even on a `"planned"` idea (backward step, :78); the idea-to-project link is only a name derived from the title (`:100`), not stored, so a name collision raises after nothing is marked. |
| RL-13 | `project/scheduler.py:23-89` | `ProjectScheduler._queue` / `_running` | queued, running, absent | `scheduler.py:44` (push), `:51` (pop), `:60` (`_running.add`), `:69` (`discard`) | in-memory only | none | developer | module Y via package; **no caller** | D | Latent: `_running` duplicates `Project.status == "running"` in a second vocabulary and `next()` never calls `start_run`; `mark_done` of an unknown name is silent. |
| RL-14 | `memory/embeddings.py:62-104,167-169,178-194` | `EmbeddingProvider._backend/_dim` | `None`, `"api"`, `"sentence_transformers"`, `"tfidf"` | `embeddings.py:84,94,102` (detect), `:62-63` (ctor); per-call fallback `:167-169` leaves `_backend` as `"api"` | in-memory; vectors persisted by callers | none | developer | Y but used only as `EmbeddingProvider(backend="tfidf")` (`review/ensemble.py:731`) | C | Live path is fixed to tfidf (dim 256 = `_TFIDF_DIM`), so none today; latent if another caller uses `"api"`: a failed call returns a 256-vector while `_dim` stays 1536 (empty text returns `[0.0]*self._dim`, :181-182), and `cosine_similarity` returns 0.0 on any length mismatch (`retriever.py:30-31`). |
| RL-15 | `memory/store.py:58-292` | `MemoryStore._entries`, `_dirty` | `_dirty` False/True; category in `("ideation","experiment","writing")` | `store.py:124,177,198,241` (set), `:256` (clear) | `{category}.jsonl`, opened `"w"` (non-atomic `:252`) | none | developer | module Y via package init, but `config.py:120` says nothing constructs it | D | Latent: `_dirty` is written and never read; a crash inside `save()` truncates a category file. |
| RL-16 | `hyperagent/base.py:23-34,117-270`; `meta_agent.py:59,350`; `task_agent.py:73,146`; `improvement_loop.py:78` | `AgentPhase`, `HyperagentState`, `variant_id`, `current_iteration` | `AgentPhase`: `"init"`, `"task_execution"`, `"performance_tracking"`, `"meta_analysis"`, `"self_modification"`, `"evaluation"`, `"selection"` (only the first, second, third and fifth are ever assigned, `base.py:214,231,261,268`) | `base.py:158,214,231,261,268`; `meta_agent.py:350`; `improvement_loop.py:78` | none | n/a | developer | N (parked) | D | none (parked; `.reachability-allowlist`). |
| RL-17 | `self_evolve/__init__.py:42-48,597,606,671` | `ExperienceType`, `_improvement_count`, hard-coded `"status"` | `"success"`, `"partial_success"`, `"failure"`, `"recovery"`; `"complete"`, `"active"` | `__init__.py:597` | none | n/a | developer | N (parked) | D | none (parked). |
| RL-18 | `memory/shared_memory.py:62,394,684-688`; `memory/{ideation,experiment,writing}_memory.py` | `AgentState.status`, module singleton `_memory` | free string status; `_memory` None/instance | `shared_memory.py:394,688` | none | `_sync_lock` / `_memory_lock` | developer | N (parked) | D | none (parked, D-07). |
| RL-19 | `learning/cross_project_learning.py:268,309,468` | stage-record `status` | compared to `"success"`, `"failed"`, `"repaired"` (not `StageStatus` values) | n/a | none | n/a | developer | N (parked) | D | none (parked); note the vocabulary does not match `StageStatus`. |
| RL-20 | `knowledge/graph/entities.py:10`, `relations.py:10` | `EntityType`, `RelationType` | StrEnum vocabularies | n/a | none | n/a | developer | N (parked) | D | none (parked). |

Dismissed as machines (see Module coverage): `knowledge/base.py` (stateless writer), `knowledge/obsidian_export.py` (stateless; `_link_cache` :188 is never read), `memory/decay.py`, `memory/retriever.py` (pure scoring; `mark_accessed` mutates store entries only).

Counts: 20 machine rows. A: 9 (RL-1, 2, 3, 5, 7, 8, 9, 10, 11). B: 1 (RL-4). C: 1 (RL-14). D: 9 (RL-6, 12, 13, 15, 16, 17, 18, 19, 20). E: 0. Defects claimed: 10 on wired paths (9 A + 1 B) and 4 latent on unwired code (RL-6, 12, 13, 15).

## Seed verification

| seed | verdict | detail |
|---|---|---|
| `discovery_loop.py:290` current_cycle | PARTLY | Writer confirmed (`discovery_loop.py:290`) and second writer confirmed (`world_model.py:166`, reached via `discovery_loop.py:389`). They agree mid-loop; they diverge only at exit (N+1 vs N), and the loop never reads a restored value (:288). The real resume problem is that the loop restarts numbering at 1. |
| `world_model.py:166` | CONFIRMED | `self.current_cycle += 1` inside `update`. |
| PC-7 `discovery_loop.py:288-319` stop_reason, budget, current_cycle | PARTLY | stop_reason lines are `:297,306,311,319` (not persisted). "Budget not restored" CONFIRMED (`:267`, not in `to_dict`). New finding: the budget is also inert, because `StageResult` has no `cost_usd` (`_helpers.py:74-83`, `discovery.py:324`). |
| PC-4 `iterative.py:67-103` + `_pivot_depth` | PARTLY | In my files, the persisted counter is `decision_history.json` (`iterative.py:67-78`) and `_handle_pivot` takes the cap decision from it (`runner.py:621,632`), so `--resume` does not reset that cap. The in-memory part is `_pivot_depth` only (pipeline-core agent). Real defect in my half: corrupt file reads as 0 (`:76-78`). |
| W6 `iterative.py:76-78` | CONFIRMED | `except (json.JSONDecodeError, OSError): pass` then `return 0` at `:78`. Also non-list JSON falls through to 0 (:74-75). |
| PC-5 / W6 `iterative.py:135-150` | CONFIRMED (rename, `rmtree` of existing `_v{attempt}` at :148-149); ordering is history (`runner.py:642`), rename (`:655`), event (`:657-658`), no checkpoint rewind in this path. |
| W6 `iterative.py:106, 310-399` | CONFIRMED | `read_quality_score` has no freshness check (:106-119); scores are in-memory (`:337,352,398`); summary only at end (`:419`). Also found: `execute_iterative_pipeline` has no caller in `berb/`. |
| PC-6 `checkpoint.py:60-202` | OUTSIDE (pipeline-core) | Only the discovery consequence verified: promotion of stages 7-15 is not checkpointed (RL-5). |
| PC-9 `_review.py` marker | NOT MINE | not read. |
| seed discovery interplay "two cycle writers" | see PC-7 | |

## Resume-survival table

| loop state | persisted? | restored on resume? | file:line |
|---|---|---|---|
| discovery `current_cycle` | yes, only after the loop ends | restored into the model, ignored by the loop (restarts at 1) | `discovery.py:367`; `world_model.py:267`; `discovery_loop.py:288` |
| discovery budget spend | no | no (fresh governor) | `discovery_loop.py:267`; `world_model.py:247-260` |
| discovery `stop_reason` | no (stdout only) | no | `runner.py:309-312` |
| established / refuted / open questions / dead ends / contradictions | yes, only after the loop ends | yes if the file parses, else silently fresh | `discovery.py:65-71`; `world_model.py:270-279` |
| `guidance` | yes | yes | `world_model.py:259,280-282` |
| `max_list_size` | no | no (default 50) | `world_model.py:127,247-260` |
| mid-loop crash | nothing saved until the end | all cycles lost; `index.jsonl` and `cycle-N/` dirs remain | `discovery.py:366-367,143-156` |
| `discovery/index.jsonl` | yes, append-only | read by `promote_best_task` including stale lines | `discovery.py:155-156,176-198` |
| task slice's own checkpoint | yes, in `cycle-N/<uuid>/` | never resumed (new uuid each call) | `discovery.py:104` |
| "slice promoted" | derived (return of `promote_best_task`) | resume from checkpoint stage 7 reruns discovery if the run died before stage 16 DONE | `runner.py:401-415`; `checkpoint.py:132-165` |
| pivot count | yes, `decision_history.json` | yes; corrupt reads 0 | `iterative.py:67-78` |
| `stage-NN_v{N}` dirs | yes (directory names) | attempt derived from count; stale `_vN` may be deleted | `iterative.py:135-150` |
| iteration scores (`execute_iterative_pipeline`) | no (only `iteration_summary.json` at the end) | no; no caller | `iterative.py:337,419` |
| `quality_report.json` score | yes | read with no iteration tag | `iterative.py:106-119` |
| `iteration_context.json` | yes, overwritten per iteration | read by stage 16 even outside an iterative run | `iterative.py:122-132`; `_paper_writing.py:79-95` |
| `experiment_summary_best.json` | yes | read by many stages; never invalidated | `iterative.py:214`; see RL-9 |
| `Project.status`, `last_run_id`, `_active` | yes, `registry.json` | yes; `"running"` never reset | `manager.py:46-55,171` |
| scheduler queue and running set | no | no | `scheduler.py:29-30` |
| IdeaPool | yes | yes | `idea_pool.py:26-40` |
| MemoryStore entries | only on explicit `save()` | only on explicit `load()` | `store.py:246,260` |

## Census mapping

Census file `cluster_research_loop.tsv`:

- `hyperagent/base.py:134,187,214,231,261,268` -> RL-16
- `hyperagent/meta_agent.py:117,487,350` -> RL-16
- `hyperagent/task_agent.py:146,369,566` -> RL-16
- `hyperagent/base.py:23`, `:158` (S4, S8) -> RL-16
- `hyperagent/improvement_loop.py:78` -> RL-16
- `knowledge/base.py:60` -> dismissed: YAML frontmatter label of the stage, no state held
- `knowledge/graph/entities.py:10`, `relations.py:10` -> RL-20
- `learning/cross_project_learning.py:468`, `:268` (S3 and S4), `:309` -> RL-19
- `memory/shared_memory.py:336,394,684` -> RL-18
- `memory/embeddings.py:118` -> RL-14
- `memory/ideation_memory.py:137,61` -> RL-18 (parked per-stage memory; mapped from the census snippet, file not read)
- `project/idea_pool.py:78,104` -> RL-12
- `project/manager.py:124,153,159` -> RL-10 (read-only consumers of status)
- `project/manager.py:171,179` -> RL-10
- `project/manager.py:54` (S9) -> RL-11
- `project/models.py:29` -> RL-10; `:80` -> RL-12
- `self_evolve/__init__.py:162,606,671`, `:42` (S4), `:597` (S8) -> RL-17
- `research/world_model.py:22` -> RL-4
- `research/discovery_loop.py:290` -> RL-1; `research/world_model.py:166` -> RL-1

Rows from `cluster_pipeline_core.tsv` for my two files:

- `pipeline/iterative.py:96` (S1 and S11, two rows) -> RL-7
- `pipeline/discovery.py:245,248,302` (S11) -> RL-4

Unmapped: 0.

## Module coverage

Wired modules under my prefixes plus the two pipeline files:

- `berb.research` — none: empty `__all__`, package docstring only
- `berb.research.world_model` — RL-1, RL-3, RL-4
- `berb.research.discovery_loop` — RL-1, RL-2, RL-3
- `berb.pipeline.discovery` — RL-1, RL-2, RL-4, RL-5
- `berb.pipeline.iterative` — RL-6, RL-7, RL-8, RL-9
- `berb.project` — RL-10..RL-13 (package init only re-exports)
- `berb.project.models` — RL-10, RL-12
- `berb.project.manager` — RL-10, RL-11
- `berb.project.idea_pool` — RL-12
- `berb.project.scheduler` — RL-13
- `berb.memory` — none: re-exports
- `berb.memory.decay` — none: pure functions
- `berb.memory.embeddings` — RL-14
- `berb.memory.retriever` — none: pure scoring; only `mark_accessed` side effect lands on RL-15's store
- `berb.memory.store` — RL-15
- `berb.knowledge` — none: re-exports
- `berb.knowledge.base` — none: stateless writer; entry id `{stage_name}-{run_id}` is overwritten when a stage reruns, no state is held
- `berb.knowledge.obsidian_export` — none: stateless exporter; `_link_cache` (:188) is never read
- Parked, one line each, class D: `berb.hyperagent`, `.base`, `.improvement_loop`, `.memory`, `.meta_agent`, `.task_agent` — RL-16; `berb.self_evolve` — RL-17; `berb.memory.shared_memory`, `.experiment_memory`, `.ideation_memory`, `.writing_memory` — RL-18; `berb.learning`, `.cross_project_learning` — RL-19; `berb.knowledge.graph` and its `.builder`, `.entities`, `.query`, `.relations`, `.visualizer` — RL-20.

## Unread / uncertain

- `berb/hyperagent/memory.py`, `improvement_loop.py` beyond line 78, `knowledge/graph/builder.py`, `query.py`, `visualizer.py`, `memory/{experiment,ideation,writing}_memory.py`, and most of `self_evolve/__init__.py` and `learning/cross_project_learning.py` were not read; their rows rest on the census snippets and parked status.
- Whether `read_quality_score`'s staleness bites depends on whether stage 20 clears its report on entry (not traced); RL-6 is class D anyway.
- RL-9 consequence for `_consecutive_empty_metrics` after promotion (unverified).
- RL-7 concurrency: whether two pivots can overlap under parallel DAG levels is not traced.
- `execute_pipeline` internals (`runner.py:380-415`) were read only for the discovery gate (`_pivot_depth == 0 and to_stage is None`); the checkpoint-on-resume claim in RL-5 relies on `checkpoint.py:132-165` returning the stage after `last_completed_stage` and on `checkpoint_mgr.write` being called only for DONE stages (`runner.py:598-599`). Skipped stages 7-15 do not pass that call.
- `Project` CLI: `cmd_project create` with no `--name` would pass `None` (not a state issue, not pursued).
