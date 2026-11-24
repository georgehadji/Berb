# P1b cluster: experiment (EX-)

Scope: `berb.experiment`, `berb.agents`, `berb.experimental`, `berb.optimization`. Read-only pass; every file:line below was read in this session. "unverified" = depends on a path not traced.

## Machines

| id | file:line | holder | states (exact literals) | transition sites (file:line) | persisted where | concurrency | who sees it | wired? | class | suspected defect |
|---|---|---|---|---|---|---|---|---|---|---|
| EX-01 | experiment/search/runner.py:160,180-217,308 | `SearchRunner` (`_node_counter`, `termination_reason`, loop) | `"exhausted"` (init, 180), `"wallclock budget exceeded (...)"`, `"cost budget exceeded (...)"`, `"max_nodes reached (...)"` (BudgetGovernor.check 80-90), `"no_new_candidates"` (216) | 184-188 (budget break), 214-217 (no_new break), 308 (`_node_counter += 1`, only after `_expand_one` completes) | `stage-12/journal.json` + `search_summary.json` written once at the end (`_execution.py:514,530`); crash mid-search loses every node | asyncio.gather batches of `num_workers` (202); counter checked only between batches | developer (summary json), downstream stages read `run-N.json` | yes (`_execution.py:153-161`, gated by `experiment.search.enabled`) | A | When the generator returns no candidates and the journal has no roots, `has_new` stays False and neither break fires (214-217), so the loop spins until the 3600 s wallclock; a node whose `_expand_one` raises after `journal.append` (302) is never counted toward `max_nodes` (308). |
| EX-02 | experiment/search/runner.py:55-92,396; _execution.py:454 | `BudgetGovernor` over `get_cost_tracker()` singleton | `None` / termination string (see EX-01) | runner.py:85-87 | none | single thread of check | developer | yes | A | `check()` compares the process-wide `total_usd()` (cost_tracker.py:208-211 sums every event of every stage) to `budget_usd` (default 5.0, config.py:611), not spend since search start, so a run that spent over $5 in stages 1-11 ends the search before node 1; `node.cost_usd` (396) is likewise cumulative, not per node. |
| EX-03 | experiment/search/runner.py:455-479; sandbox.py:466; factory.py:107 | `SearchRunner._run_in_sandbox` call protocol | branches `hasattr(sandbox,"write_files")` / `hasattr(sandbox,"run")` / `NotImplementedError` | 473-479 | none | each node gets a fresh sandbox (329-331) but all share `runs_dir/"sandbox"` (`_execution.py:459`) | developer | yes | A | Verified by `inspect.signature`: `ExperimentSandbox.run(self, code, *, timeout_sec)` and `DockerSandbox.run` are synchronous, need `code`, and nothing defines `write_files`; `await sandbox.run()` raises TypeError, caught at runner.py:376, so every real-sandbox node is `is_buggy=True`, `returncode=-1`, score 0 (no test covers `_run_in_sandbox`). Even if fixed, a sync `run` inside the coroutine blocks the loop and `asyncio.wait_for` (334) cannot interrupt it. |
| EX-04 | experiment/journal.py:88-98; search/runner.py:321,340-345,366-369,376-379,399-403 | `JournalNode` evaluation fields: `returncode`, `timed_out`, `is_buggy` (True/False/None), `score` | `is_buggy`: `True`/`False`/`None`; `timed_out`: `True`/`False`; `result_source`: `"structured"`/`"stdout_fallback"`/`"synthesized"` | no-files 321; success 344-345; timeout 366-369; exception 376-379; record_evaluation journal.py:260-306 | `journal.json` (journal.py:553-561 `to_dict`/`from_dict` 112-218) | node mutated in place under `async with self._semaphore` (305) | developer, agent (`parent_stderr`/`parent_analysis` fed to generator, 273-282) | yes | A | Line 344 hard-codes `timed_out=False` instead of reading the sandbox result, so a Docker/SSH/Colab timeout is stored as not timed out; `good_nodes()` (journal.py:393-398) treats `is_buggy=None` as good, so a node left unevaluated by an exception after append (302-308) is selectable; scoring's `"timed out"` penalty (scoring.py:166-168) is unreachable because a timeout has `returncode` -1 and `runs_ok` False. |
| EX-05 | experiment/search/policy.py:112,147-189,223-234; runner.py:269,276,298 | `BestFirstDiversePolicy` selection (roots, claimed_roots, `_debug_depth`) | rule branches "bootstrap" / "repair" / "exploit"; node `origin`: `"draft"`/`"improve"` (runner 269,276) vs `"debug"` (policy 228) | policy.py:147,156,169,189 | none (in-memory journal) | `random.Random` shared, single caller | developer | yes | A | Nothing ever creates `origin="debug"` (`_expand_one` only passes `"draft"`/`"improve"`, `_candidate_generator` echoes it, `_execution.py:461-470`), so `_debug_depth` (223) is always 0 and `max_debug_depth` never limits repair of one buggy leaf; `SearchConfig.max_depth` is read nowhere in `search/` (grep), so depth is bounded only by `max_nodes`. |
| EX-06 | experiment/plot_verdict.py:74-87,211-249; runner.py:407-453; search/scoring.py:99-111; journal.py:393-398 | figure verdict chain `PlotVerdict.is_buggy` -> `is_verdict_gating` -> `node.is_buggy_plots` -> `ScoreBreakdown.buggy_plots` -> `good_nodes` | tri-state `True`/`False`/`None` at each link; `PlotAnalysis.is_valid` True/False; `confidence` 0.0-1.0 | plot_verdict.py:104-117 (no critic), 194-209 (critic error: `is_valid=True, confidence=0.0`), 242-249 (gate); runner.py:449; scoring.py:100,108 | `journal.json` (`is_buggy_plots`, `plot_analyses`) | per-node, async | developer, agent (`vlm_feedback_summary`) | yes (`_execution.py:484-492`, `figure_agent.enabled`) | A | Line 214 averages in the 0.0 confidence of errored critics, so one confident invalid plot plus two critic errors gives 0.33 < 0.6 and `is_verdict_gating` returns None (242), opening the gate; also `_verify_node_plots` does `Path(workdir).rglob` over the shared `runs_dir/"sandbox"` (432-434), so one node is judged on earlier or concurrent nodes' images and a blank one gates later candidates (unverified at runtime, EX-03 blocks it today); `PlotVerdict.is_buggy` and `is_verdict_gating` also answer the same question differently (any-invalid vs confidence-filtered). |
| EX-07 | experiment/journal.py:79,80,109,112-162,443-449 | `JournalNode.phase`, `.origin`, `.result_source` free strings; `schema_version` | phase `"baseline"`,`"tuning"`,`"creative"`,`"ablation"` (docstring); origin `"draft"`,`"debug"`,`"improve"`,`"ablation"`,`"hyperparam"`,`"seed"` (comment); `SCHEMA_VERSION = "1.0"` | runner.py:290,298,363 | `journal.json` | none | developer | yes | C | none (vocabulary only; `"debug"` is the unused literal, see EX-05) |
| EX-08 | experiment/sandbox.py:456-464,466-516,518-632,645-649,693,720-722 | `ExperimentSandbox` (`_run_counter` + `_counter_lock`, `_experiment_N.py`, `_project_N/`) | outcome via `SandboxResult(returncode, timed_out, rejected_reason)`; files `_experiment_{counter}.py`, `_project_{counter}` | counter 532-534, 646-648; cleanup only on success 513-514,720-722; project dir `rmtree` only if it already exists (536-537) | workdir files | lock is per instance; Stage 12 search builds a new instance per node on one workdir (`_execution.py:457-459`) so every instance restarts at 1 and collides on `_experiment_1.py`; `subprocess.run(timeout=)` kills only the direct child (693 comment) | developer | yes | A | Failed runs leave `_experiment_N.py` and every `run_project` leaves `_project_N` forever; the legacy path reads `runs_dir/"sandbox"/"_project"/results.json` (`_execution.py:186-188`) but the sandbox only creates `_project_{counter}` (535), so `structured_results` is never found for the local sandbox; a timed-out experiment's grandchildren survive (child-only kill). |
| EX-09 | experiment/docker_sandbox.py:38-46,194-233,234-311,381-467,666-688 | `DockerSandbox` (`_run_counter`, staging dir `_docker_run_N` / `_docker_project_N`, container `rc-exp-{n}-{pid}`, `keep_containers`) | outcome `SandboxResult.timed_out`/`returncode`; container name counter `_CONTAINER_COUNTER` | counter 198,218,242 (unlocked); global container counter locked 43-46; `docker kill` on timeout 424; `docker rm -f` in `finally` 439-440; staging `rmtree` 232,311 | staging dir (volume mount `/workspace`), `.hf_secrets.env` (575-578) removed with staging | instance counter unlocked; module counter locked | developer | yes (mode `docker`) | A | `run()` does `staging.mkdir(exist_ok=True)` (220) with no stale clear, unlike `run_project` (244-245), and the per-instance counter restarts at 1 for each factory-built sandbox, so two concurrent instances on one workdir share `_docker_run_1` and the first `finally: rmtree` (232) deletes the other's staging mid-run; an infrastructure failure returns `returncode=-1` "Docker execution error" (428-434) indistinguishable from an experiment crash (see EX-12). |
| EX-10 | experiment/ssh_sandbox.py:47-87,89-162,203-287,373-411 | `SshRemoteSandbox` (`_run_counter`, local `_ssh_run_N`, remote `rc-<uuid8>` dir) | `_SshResult.timed_out`; remote dir exists/removed | counter 51,78,97 (unlocked); remote mkdir 220, upload 231, exec 269, `rm -rf` 278 | local staging never removed (no `rmtree` after `_execute`); remote dir removed best effort, return ignored | instance counter unlocked | developer | yes (mode `ssh_remote`) | A | On `TimeoutExpired` only the local ssh client dies (393-405); the remote process (or un-named docker container, 324-371) keeps running and `rm -rf` (278) removes its working dir under it; failed `rm` (15 s, result ignored) leaks the remote dir; `_ssh_run_N` local staging accumulates and a fresh instance reuses `_ssh_run_1` with stale files that `scp -r` (427) uploads. |
| EX-11 | experiment/colab_sandbox.py:125-358,360-411 (+ worker template 39-122) | `ColabDriveSandbox` + Colab worker over Drive dirs | directory states `pending/<task>` -> `running/<task>` -> `done/<task>` (+ `result.json` present/absent); outcomes `timed_out` True/False | sandbox: `copytree` to pending 326-329, poll `task_done.exists()` 339, `rmtree(task_pending)` on timeout 345-346, collect + `rmtree(task_done)` 373-402; worker: `task_dir.rename(run_dir)` 71, `result.json` 117, `run_dir.rename(done_dir)` 118 | the Drive folder is the state; local staging `_colab_N` never removed | two processes over a synced Drive; no lock; Drive sync latency | developer, user (must keep the Colab notebook running) | yes (mode `colab_drive`) | A | `shutil.copytree` into `pending/` (329) is not atomic and there is no ready marker, so the worker's 10 s poll can rename a half-copied task to `running/` and run it without `main.py`; on timeout only `pending/` is handled (345), so a task already in `running/` finishes later into `done/` and is never collected, and the unguarded `rmtree` (346) can raise if the worker renames between `exists()` and `rmtree` (timing unverified); `effective_timeout = max(timeout_sec, config.timeout_sec)` (334) overrides a shorter caller timeout. |
| EX-12 | experiment/sandbox.py:424-439; docker_sandbox.py:428-434; ssh_sandbox.py:222-227,234-240; _execution.py:214-237 | `SandboxResult` outcome encoding (`returncode`, `timed_out`, `rejected_reason`) and the derived `run_status` | `"rejected"`, `"completed"`, `"partial"`, `"failed"` (+ `"simulated"`) in `_execution.py:223-237` | derivation `_execution.py:214-237`; `-1` sentinel for rejection, timeout, exception, infra failure | `stage-12/runs/run-1.json` `status` | n/a | agent, user (downstream stages read `status`) | yes | B | Infrastructure failures (Docker daemon error 428, SSH mkdir/scp failure ssh_sandbox 222,234, Drive read error colab 386) are `returncode=-1` with no flag, so they read as the experiment's own `"failed"`; the stage still returns `StageStatus.DONE` for `"failed"`/`"rejected"` (`_execution.py:391-394`, pipeline cluster to confirm). |
| EX-13 | experiment/docker_sandbox.py:505-524; ssh_sandbox.py:357; agents/benchmark_agent/selector.py:97; config.py:35-44,434,465 | network policy config string | `"none"`, `"setup_only"`, `"pip_only"`, `"full"` (docker); ssh docker: `"none"` vs anything else | `_validate_network_policy` at parse (config.py:1441,1463) | config file | read-only | developer | yes | C | none (config.py validates and falls back; SSH docker treats every non-`"none"` value as unrestricted bridge, a deliberate-looking simplification, unverified) |
| EX-14 | experiment/runner.py:101-229 | `ExperimentRunner` keep/discard loop (`history.best_result`, `improved`, `kept`, `no_improvement_count`, `current_code`) | `improved` True/False, `kept` True/False, `error` None/`"Timed out after Ns"`/stderr | 132-143 (improved/kept), 167-168 (best), 200 (`current_code = next_code`), 216-223 (stop after 3) | `experiment_history.json` (`_execution.py:373`, `save_history` 271) | single thread | developer, agent | yes for modes other than sandbox/docker/simulated (`_execution.py:370-390`, e.g. `ssh_remote`, `colab_drive`) | A | `current_code = next_code` (200) runs even when the result was discarded, so the next LLM improvement starts from the discarded code, not from the kept best; `improved` and `kept` diverge (`kept` needs delta > `keep_threshold`) and the stop counter uses `improved` (216), not `kept`. |
| EX-15 | experiment/git_manager.py:21-33,86-95,55-61 | `ExperimentGitManager` (`_original_branch`, `_active_branch`, repo working tree) | branch `experiment/<tag>`, original branch name | `checkout -b` 28, `checkout <orig>` 90, `reset --hard HEAD` 57 | git repo state | not thread-safe, shared repo | developer, user | yes (only when `git_repo_dir` passed to `ExperimentRunner`; `_execution.py:371` passes none, so inactive on the wired call; unverified elsewhere) | A | `run_loop` returns early at runner.py:194 (`llm is None`) before `return_to_original_branch` (227) and has no `finally`, so an exception or the early return leaves the user's repo on `experiment/<tag>`; `discard_experiment` runs `git reset --hard HEAD` (57) and `commit_experiment` `git add -A` (36), destroying or committing unrelated uncommitted user changes. |
| EX-16 | experiment/async_pool.py:153-162,193-235,237-253,255-351,433-443 | `AsyncExperimentPool` (`_running`, `_workers`, `_status`, `_queue`, `_result_db`) | `_running` True/False; `WorkerStatus.is_busy` True/False; result `error` `"Timeout"`/`str(e)`/None | `_running` 207,221,436; `is_busy` 283,349; `failed_count` 318,336; `_workers.append` 248 | none (in-memory) | asyncio tasks, per-worker semaphores (153) | developer | wired per baseline; no pipeline-path importer found (only parked `pipeline/optimization_integration`, `benchmarks/performance_suite.py:160`, lazy export) | A | `_initialize_workers` appends to `self._workers` without clearing (248), so `create_pool` (456) followed by `execute_parallel` (200), or a second `execute_parallel`, doubles the workers, duplicates `worker-N` ids in `_status`, and pushes workers past the semaphore list (290); `_running` is not reset if `queue.join()` raises (218-221), leaving "Pool is already running" (193-194); the outer `except TimeoutError` (302) is dead because `_execute_with_timeout` catches it (380). |
| EX-17 | experiment/worker.py:52-199 | `ExperimentWorkerImpl` (`_is_busy`, `_current_context`, `_completed_count`, `_failed_count`, `_last_heartbeat`) | `_is_busy` True/False; result `kept=True, error=None` vs `kept=False, error=str(e)` | 128,198 (busy), 135,197 (context), 164,173 (counters) | none | one execution at a time per worker object | developer | same as EX-16 | A | `isolation.execute` returns only stdout (isolation.py:250,424,558), so a non-zero exit, Docker error or sandbox timeout still yields `ExperimentResult(kept=True, error=None, stderr="")` (150-162); `config.timeout` (145) ignores the pool's `timeout_per_experiment`. |
| EX-18 | experiment/isolation.py:41-55,129-271,288-462,482-571 | `IsolationStrategy` lifecycle `setup -> execute -> cleanup`; `IsolationContext.resources` (container id, branch) | context present/None; worktree `exp-<id>`; workspace dir | setup 154,330,505; cleanup 259,426,560 | `/tmp/berb/experiments/<id>` (164), worktree `../worktree-<id>` (340), branch `exp-<id>` | async subprocesses | developer | same as EX-16 | A | `WorktreeIsolation.cleanup` computes the branch name and discards it (436) and runs `worktree remove` without `--force`, which fails on the untracked `experiment.py` (403-404), so the worktree and branch `exp-<id>` leak and a re-run of the same design id fails at `git worktree add -b` (343-352); on timeout `wait_for(proc.communicate())` (242,416) never kills the process or container (no `--name`). |
| EX-19 | agents/benchmark_agent/orchestrator.py:57-103,213-358 | `BenchmarkOrchestrator` phases Survey -> Select -> Acquire -> Validate; `BenchmarkPlan.validation_passed` | phase log strings "Phase 1".."Phase 4"; `validation_passed` True/False; retry `for iteration in range(max_iterations)` (276) | early returns 240-245, 261-266; `continue` on acquire failure 292-294; `plan.validation_passed` 327; `break` 330-332 | `survey_results.json`, `selection_results.json`, `acquisition_N.json`, `validation_N.json`, `benchmark_plan.json` (only if `stage_dir` set, 199-211,346) | sequential | agent (prompt block), developer | yes (`_experiment_design.py:475`) | A | A survey/selection failure returns a default `BenchmarkPlan` (240-245, 261-266) with empty lists and `validation_passed=False` and no failure marker, indistinguishable from "nothing found"; failure paths skip `benchmark_plan.json` (346); whether the consumer distinguishes them is unverified. |
| EX-20 | agents/figure_agent/orchestrator.py:330-455 | `FigureOrchestrator` CodeGen -> Render -> Critic loop (`figures`, `final_rendered`, `critic_feedback`) | `all_passed` True/False; review `passed` True/False | `continue` on codegen/render failure 391-392,410-412; merge 417-425; break 445-450; `figures` narrowed 458-461 | `scripts_N.json`, `reviews_N.json` via `_save_artifact` | sequential | agent, user (charts in paper) | yes (`_analysis.py:676`) | A | When the critic call fails (`success` False, `reviews` empty) `critic_feedback` is `[]`, `failed_ids` empty and `figures` becomes `[]` (458-461): the loop stops retrying on nothing and returns unreviewed figures; the return value is `final_rendered` with no per-figure `passed` flag, so figures that never passed review at `max_iterations` look final. |
| EX-21 | agents/figure_agent/critic.py:124-176,330-376,392-399; agents/base.py:99-111,135 | figure review pass/fail (`passed`, `issues`) | `passed` True/False; severity `"critical"`/`"warning"` | `critical_issues` 163-165; `_check_visual_quality` 354-376 | `reviews_N.json` | per figure | agent | yes | A | `_chat_json` returns `{}` on unparseable output (base.py:111), so `quality_score` defaults to 5 with no issues (critic.py:355) and the visual-quality dimension passes as if reviewed; a raised LLM error instead fails the whole critic (124-126, see EX-20). |
| EX-22 | agents/figure_agent/renderer.py:167-262 | `RendererAgent` per-figure `success`, `output_path`, `error` | `success` True/False; `error` strings | 183,253 | `charts/scripts/<id>.py`, PNGs | sequential | developer | yes | C | none claimed; the existence check (239-246) does not clear a prior-iteration PNG before running, so a script exiting 0 without saving could pass on a stale file (unverified, marginal) |
| EX-23 | experiment/validator.py:24-50; physics_guards.py:42-65,192-194; plot_verdict.py:301-330; agents/figure_agent/critic.py:163,223-315; agents/benchmark_agent/validator.py:165,233-245 | `severity` string vocabularies | validator `"error"`/`"warning"`; physics_guards, pixel defects, figure critic `"critical"`/`"warning"`/`"info"`; benchmark validator `"none"`/`"warning"`/`"error"` | n/a | JSON artifacts | n/a | agent, developer | yes | B | none (three vocabularies for one concept; they are bridged only by `detect_pixel_defects` reuse in critic.py:397) |
| EX-24 | agents/figure_agent/nano_banana.py:98-100,355 | `NanoBananaAgent._use_sdk` | `True`/`False` | 98-100 (detect), 355 (ImportError downgrade) | none | n/a | developer | yes | C | none |
| EX-25 | agents/code_searcher/cache.py:21-110; github_client.py:74,87-94,100-121; agent.py:128-232 | `SearchCache` TTL (`_cached_at`), `GitHubClient._last_search_time`, `request_count` | cache hit / expired / absent; HTTP 403 and 422 -> `None` | `put` only when `patterns.has_content` (agent.py:224-225); expiry `unlink` cache.py:44-46 | `data/code_search_cache/<domain>/<hash>.json` | no lock on cache files | developer | yes (`_code_generation.py:617`) | C | none (empty or rate-limited results are not cached, so no poisoning; a 403 is returned as `None` with no degraded flag, minor, unverified consumer) |
| EX-26 | agents/base.py:78-83,98-103,143-157,209-227 | `BaseAgent._calls`/`_tokens` reset-on-read accumulators; `AgentOrchestrator.total_*` | counters 0..n | `_chat` 98-107, `_make_result` reset 150-155, `_accumulate` 221-224 | none | `_stats_lock` | developer | yes | C | none (counters carry over to the next `_make_result` if `execute` raises before it, cosmetic) |
| EX-D1 | experiment/compute_guard.py:26-40,515,673 | `ExperimentStatus` | `"queued"`, `"running"`, `"completed"`, `"failed"`, `"stopped"` | 515, 673 | none | n/a | none | parked (`.reachability-allowlist:98`) | D | n/a |
| EX-D2 | experiment/progress.py:33-48,289-308 | `ExperimentStage`, `StageStatus` | stage `"investigation"`,`"tuning"`,`"agenda_execution"`,`"ablation"`; status `"pending"`,`"in_progress"`,`"completed"`,`"failed"`,`"skipped"` | 289-308 | none | n/a | none | parked (`:100`) | D | n/a (note: second `StageStatus` enum, name clash with `pipeline.stages.StageStatus`) |
| EX-D3 | experiment/self_correcting.py:44-52 | `SimulationStatus` | `"pending"`,`"clarifying"`,`"coding"`,`"executing"`,`"diagnosing"`,`"revising"`,`"completed"`,`"failed"` | not read | none | n/a | none | parked (`:97`) | D | n/a |
| EX-D4 | experiment/evolutionary_search.py:230 | variant id suffix `_v{i}` | none | n/a | none | n/a | none | parked (`:101`) | D | n/a |
| EX-D5 | experiment/harness_template.py:110-121 | module global `_default_harness` | `None`/instance | 118-120 | none | n/a | none | parked (`:103`) | D | n/a (note: `sandbox.py:637`, `docker_sandbox.py:368`, `ssh_sandbox.py:193`, `colab_sandbox.py:284` copy this file's source into every project run as data, so "parked" but load-bearing as a file) |
| EX-D6 | experiment/react_agent.py:34-39,63 | `ReActStep` | `"reason"`,`"act"`,`"observe"` | n/a | none | n/a | none | DEAD (broken imports per CLAUDE.md) | D | n/a |
| EX-D7 | experiment/split_policy.py:236-272,296 | `admit()` returns `ClaimVerdict` | `INCONCLUSIVE`,`UNSPLITTABLE`,`SUPPORTED`,`UNSUPPORTED` | 256-272 | none | n/a | none | DEAD (no importer) | D | n/a |
| EX-D8 | experiment/evaluators/convergence.py:128 | stateless | none | n/a | none | n/a | none | parked (`:102,149`) | D | n/a |
| EX-D9 | experimental/diff_revisions.py:44-57, tdd_generation.py:50-63,387 | `DiffRevisionResult`, `TDDResult`, `PytestRunner` | none (result dataclasses, no status field) | n/a | none | n/a | none | parked (`:92`) | D | n/a |
| EX-D10 | optimization/cost_quality.py:33-37,492-553,572 | `ModelTier`, module global `_optimizer` | `"budget"`,`"mid"`,`"premium"` | 572 | none | n/a | none | parked (`:112`) | D | n/a |

Counts: 26 live machine rows (A 18, B 2, C 6, E 0) + 10 D rows = 36.

## Seed verification

| seed | verdict | detail |
|---|---|---|
| IN-8 (docker/ssh/colab/local counters, staging, Drive dirs) | PARTLY | Docker `_run_counter` unlocked at docker_sandbox.py:198,218,242 and SSH at ssh_sandbox.py:51,78,97: CONFIRMED; local sandbox lock at sandbox.py:461-464: CONFIRMED. Wrong emphasis: the lock is moot for the wired search path because each node builds a new sandbox on one workdir (`_execution.py:457-459`), so counters restart at 1 (EX-08/09). Docker `run()` has no stale-staging clear (219-220 vs 244-245): CONFIRMED. Orphans on timeout: SSH CONFIRMED (269-278), Colab CONFIRMED (345-346 only handles pending), Docker is handled (424, 439-440). |
| IN-9 timed_out forced False | CONFIRMED at runner.py:344 (also set True only on `asyncio.TimeoutError` 366-369). Added: scoring's timeout penalty is unreachable (EX-04). |
| IN-9 busy-spin on empty journal | CONFIRMED in a narrow form: no break when `has_new` is False and `journal.roots()` is empty (runner.py:214-217), loop runs to the wallclock budget (EX-01). |
| IN-9 failed nodes bypassing `max_nodes` | PARTLY WRONG: buggy nodes returned by `_evaluate_node` DO count (308 runs after evaluation, exceptions are swallowed 365-380). Only a node whose `_expand_one` raises (generator or post-append error) is uncounted; the cap is also checked only between batches (184), so it can overshoot by `num_workers - 1`. |
| IN-10 / W3 plot_verdict.py:242 | CONFIRMED with correct cause at 214 (average includes errored critics at confidence 0.0) and 242 (gate returns None below 0.6). |
| W3 runner.py:344 | CONFIRMED; fix = `getattr(result, "timed_out", False)`, but EX-03 means that line is not reached with a real sandbox today. |
| W7 bullet 1 (lock `_run_counter` docker 198/218/242, ssh 78/97; local 464) | CONFIRMED lines. Locking alone does not fix the cross-instance collision. |
| W7 bullet 2 (kill process group; kill remote before rm) | CONFIRMED: sandbox.py:693 comment relies on `subprocess.run` child-only kill; ssh_sandbox.py:269-278 has no remote kill. |
| W7 bullet 3 (colab 303-358) | CONFIRMED: `max(timeout_sec, config.timeout_sec)` at 334, only `pending/` cleaned at 345. |
| W7 "clear stale staging in docker run()" | CONFIRMED (219-220). |
| CLAUDE.md "search/ (Stage 12) ... are live" | PARTLY: wired by `_execution.py:153,399` but the sandbox call protocol (EX-03) cannot execute against any shipped sandbox. |

## Census mapping

Format: `file:line -> id` or `dismissed: reason`. Paths are under `berb/`.

- experiment/compute_guard.py:515, :673, :26, :399, :415 -> EX-D1
- experiment/journal.py:118 -> EX-07 (phase key of `to_dict`); journal.py:449 -> EX-07 (persisted `journal.json`)
- experiment/progress.py:289, :301, :306, :308, :484, :485, :521, :522, :33, :42 -> EX-D2
- experiment/react_agent.py:63, :34 -> EX-D6
- experiment/split_policy.py:296 -> EX-D7
- optimization/cost_quality.py:492, :542, :553, :33, :572 -> EX-D10
- experiment/async_pool.py:207, :221, :283, :349, :436 -> EX-16
- experiment/search/runner.py:321, :344, :368, :369, :379 -> EX-04
- experiment/worker.py:128, :198 -> EX-17
- experiment/evaluators/convergence.py:128 -> EX-D8
- experiment/visualize.py:613 (S3 and S4) -> dismissed: inside `plot_pipeline_timeline`, which has no caller anywhere in `berb/` (grep); stateless chart colouring
- agents/benchmark_agent/selector.py:97 -> EX-13
- agents/benchmark_agent/validator.py:233 -> EX-23
- agents/figure_agent/codegen.py:851 -> dismissed: `_output_format == "latex"` is a constructor-time output mode, never transitions
- experiment/docker_sandbox.py:505 -> EX-13; docker_sandbox.py:43 (S5 `_CONTAINER_COUNTER`) -> EX-09
- experiment/ssh_sandbox.py:357 -> EX-13
- experiment/metrics.py:27 -> dismissed: `MetricType` classifies result shape, no lifecycle or transitions
- experiment/physics_guards.py:193, :194 -> EX-23
- experiment/validator.py:42, :46, :50 -> EX-23
- experiment/self_correcting.py:44, :580 -> EX-D3
- experiment/evolutionary_search.py:230 -> EX-D4 (id suffix only, not a directory rename)
- experiment/harness_template.py:118 -> EX-D5
- experiment/colab_sandbox.py:117, :118, :71 (worker template string), :326, :327, :333, :339, :345, :374 -> EX-11

All 66 census rows are mapped or dismissed; 0 unmapped.

## Module coverage

Wired modules under my prefixes (from `tasks/baseline/wired_modules.txt`):

- berb.experiment — none: lazy-export `__init__` (PEP 562), no state
- berb.experiment.async_pool — EX-16
- berb.experiment.colab_sandbox — EX-11
- berb.experiment.docker_sandbox — EX-09, EX-13
- berb.experiment.factory — EX-03, EX-12 (chooses backend; `create_sandbox` raises on unavailable Docker/SSH/Drive instead of holding state)
- berb.experiment.git_manager — EX-15
- berb.experiment.isolation — EX-18
- berb.experiment.journal — EX-04, EX-07
- berb.experiment.metrics — none: stateless parser, `MetricType` dismissed (census)
- berb.experiment.physics_guards — EX-23 (otherwise stateless AST checks)
- berb.experiment.plot_verdict — EX-06, EX-23
- berb.experiment.runner — EX-14
- berb.experiment.sandbox — EX-08, EX-12
- berb.experiment.science_check — none: pure function, no module state
- berb.experiment.search — none: package re-exports
- berb.experiment.search.policy — EX-05
- berb.experiment.search.runner — EX-01, EX-02, EX-03, EX-04, EX-06
- berb.experiment.search.scoring — EX-04, EX-06 (pure function; consumes the flags)
- berb.experiment.ssh_sandbox — EX-10, EX-13
- berb.experiment.validator — EX-23 (otherwise stateless AST visitor)
- berb.experiment.visualize — none: stateless chart code; only status literal is in a dead function (census)
- berb.experiment.worker — EX-17
- berb.agents — none: package marker
- berb.agents.base — EX-26
- berb.agents.specialized — none: stateless request/response dataclasses (`AgentResult.success`/`confidence`, a second result vocabulary beside `AgentStepResult`; used only via `commands/claude_scholar.py:268`)
- berb.agents.benchmark_agent — none: package re-exports
- berb.agents.benchmark_agent.orchestrator — EX-19
- berb.agents.benchmark_agent.acquirer — none: per-call LLM step, no held state (skimmed)
- berb.agents.benchmark_agent.omissions — none: constant data (skimmed)
- berb.agents.benchmark_agent.selector — EX-13 (read-only config fields)
- berb.agents.benchmark_agent.surveyor — none: read-only config and knowledge load (skimmed)
- berb.agents.benchmark_agent.validator — EX-23
- berb.agents.code_searcher — none: package re-exports
- berb.agents.code_searcher.agent — EX-25
- berb.agents.code_searcher.cache — EX-25
- berb.agents.code_searcher.github_client — EX-25
- berb.agents.code_searcher.pattern_extractor — none: stateless LLM extraction (skimmed)
- berb.agents.code_searcher.query_gen — none: stateless (skimmed)
- berb.agents.figure_agent — none: package re-exports
- berb.agents.figure_agent.orchestrator — EX-20
- berb.agents.figure_agent.critic — EX-21, EX-23
- berb.agents.figure_agent.renderer — EX-22
- berb.agents.figure_agent.nano_banana — EX-24
- berb.agents.figure_agent.codegen — none: per-call LLM step, only a constructor `_output_format` (skimmed, 1020 lines)
- berb.agents.figure_agent.decision — none: LLM decision with heuristic fallback, no held state (skimmed)
- berb.agents.figure_agent.integrator — none: stateless (skimmed)
- berb.agents.figure_agent.planner — none: per-call LLM step (skimmed)
- berb.agents.figure_agent.style_config — none: constants

Parked, DEAD and other non-wired modules (class D, one line each):

- berb.experiment.compute_guard — EX-D1 (parked)
- berb.experiment.progress — EX-D2 (parked)
- berb.experiment.self_correcting — EX-D3 (parked)
- berb.experiment.evolutionary_search — EX-D4 (parked)
- berb.experiment.harness_template — EX-D5 (parked, but its source is copied into every sandbox run)
- berb.experiment.react_agent — EX-D6 (DEAD)
- berb.experiment.split_policy — EX-D7 (DEAD)
- berb.experiment.evaluators, berb.experiment.evaluators.convergence — EX-D8 (parked)
- berb.experimental, berb.experimental.diff_revisions, berb.experimental.tdd_generation — EX-D9 (parked)
- berb.optimization, berb.optimization.cost_quality — EX-D10 (parked)
- berb.domains.experiment_schema — outside my prefixes, parked (`.reachability-allowlist:145`); not read

## Unread / uncertain

- `agents/figure_agent/codegen.py`, `planner.py`, `decision.py`, `integrator.py`; `agents/benchmark_agent/acquirer.py`, `surveyor.py`, `selector.py` (beyond line 97), `validator.py` (beyond severity lines), `code_searcher/query_gen.py`, `pattern_extractor.py`, `agents/specialized.py` bodies: skimmed by grep for `self._x =`, enums, globals and retry loops only; no lifecycle state found, not read in full.
- `experiment/validator.py` (1589 lines), `physics_guards.py`, `science_check.py`, `visualize.py`, `metrics.py` bodies: grep for class/global/enum only.
- EX-16/17/18 wired status: baseline says wired, but the only importers I found are the lazy export in `experiment/__init__.py`, parked `pipeline/optimization_integration`, and `benchmarks/performance_suite.py`; no pipeline-path caller traced.
- EX-15: `ExperimentRunner` is constructed without `git_repo_dir` at `_execution.py:371`; I did not search other callers.
- EX-19/20/21: downstream consumers of an empty `BenchmarkPlan` and of unflagged `final_rendered` were not traced.
- EX-11 race windows (non-atomic `copytree`, `rmtree` vs worker rename) are structural readings; Drive sync timing is unverified.
- EX-06 shared-workdir figure contamination is latent until EX-03 is fixed; not reproduced.
- Cross-cluster: `_execution.py:214-237` run_status strings (PC-8), stage returning `DONE` after `"failed"`/`"rejected"`, and a Stage 12 search with zero good nodes still returning `DONE` (535-560) belong to the pipeline-core reader; noted here only where sandbox encoding feeds them.
