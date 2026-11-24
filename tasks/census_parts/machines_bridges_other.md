# P1b cluster: bridges_other (id prefix BR-)

Reader scope: every `berb.*` module outside the other eight clusters. 87 wired modules in the slice (24.7k loc, from `tasks/baseline/wired_modules.txt`) plus 11 parked modules. Read-only; line numbers re-checked against the code read in this session.

Note on "wired": the baseline marks several modules wired only because a package `__init__` or lazy export imports them (reasoning, metrics, benchmarks, overleaf watcher/conflict). Where I found no in-repo caller, the row says so and the defect is marked `unverified` (reach, not logic).

## Machines

| id | file:line | holder | states (exact literals) | transition sites | persisted where | concurrency | who sees it | wired? | class | suspected defect |
|---|---|---|---|---|---|---|---|---|---|---|
| BR-1 | berb/metaclaw_bridge/session.py:19,45,53-55 | `MetaClawSession._active` | `True` (init) / `False` (after `end()`) | session.py:19 set; session.py:45 cleared | none | single caller, no lock | nobody: `is_active` has no reader (grep of `\.is_active` finds only dashboard/server `RunSnapshot`, not this class) | Y | C | none (flag is dead, seed IN-14 confirmed) |
| BR-2 | berb/metaclaw_bridge/session.py:22-37,39-51; berb/pipeline/metaclaw_post.py:116-140 | MetaClaw session-id protocol (`X-Session-Id`, `X-Turn-Type`, `X-AutoRC-Stage`, `X-Session-Done`) | session open (`get_headers`) / done (`end` headers `"X-Session-Done": "true"`) | `get_headers` has zero callers in `berb/`; `MetaClawSession(run_id)` is constructed only at run end, metaclaw_post.py:121, then `end()` at :122; urlopen result and all exceptions swallowed at :135-140 | none (HTTP side effect to proxy) | fire-and-forget, 5 s timeout | agent/developer (MetaClaw proxy) | Y | A | Proxy never receives a session-open or per-stage turn headers, only a `session-end` call for a session id it never saw, so post-session skill evolution is signalled against nothing; a failed end call is invisible (`pass`). |
| BR-3 | berb/metaclaw_bridge/config.py:32-41; berb/llm/client.py:518-529 | `MetaClawBridgeConfig.enabled` (frozen) | `enabled` False / True | read-only; LLM client swaps `base_url` to `proxy_url` and fallback to prior URL (client.py:522-529) | config yaml | none | developer | Y | C | none in this cluster (proxy-down failover state lives in llm.client, other reader) |
| BR-4 | berb/metaclaw_bridge/prm_gate.py:156-206; berb/pipeline/executor.py:289-345 | PRM score of a gate stage | `-1.0` / `0.0` / `1.0` | prm_gate.py:104-107 parse; :198-200 all calls failed -> `0.0`; :205-206 tie/any exception -> `0.0`; executor.py:331 acts only on `== -1.0` | `stage_dir/prm_score.json` (executor.py:326) with `prm_score` only | ThreadPoolExecutor, `votes` workers (prm_gate.py:180) | user/agent via stage FAILED | Y | A | Judge outage, all-tie and "ambiguous" all store `0.0`, and executor.py:331 lets 0.0 pass, so an unreachable PRM endpoint silently approves a gate stage and `prm_score.json` cannot tell outage from "ambiguous". Gate-stage set is also duplicated: `_GATE_INSTRUCTIONS` keys (prm_gate.py:21), `PRMConfig.gate_stages` (config.py:19), executor default `(5, 9, 15, 20)` (executor.py:295). |
| BR-5 | berb/metaclaw_bridge/skill_feedback.py:18-69,98-117; berb/pipeline/metaclaw_post.py:68-113 | `SkillEffectivenessRecord.stage_success` JSONL | `stage_success` True/False | metaclaw_post.py:109 `success = "done" in status.lower()`; records the static `STAGE_SKILL_MAP` skills (:107), not what MetaClaw injected | `run_dir/evolution/skill_effectiveness.jsonl` (metaclaw_post.py:76), append-only | no lock, append | nobody: `compute_skill_stats` (skill_feedback.py:71) has no caller | Y | A | Docstring says effectiveness "across pipeline runs" but the file is per run_dir and has no reader, and `active_skills` is the preferred-skill table rather than injected skills, so the data cannot support its stated purpose (low impact, write-only). |
| BR-6 | berb/evolution.py:152-176; berb/pipeline/metaclaw_post.py:79-103; berb/metaclaw_bridge/stage_skill_map.py:13-129 | stage-name vocabulary | 23 snake-case names `topic_init` ... `citation_verify` | three hand-copied tables vs `Stage` IntEnum (pipeline/stages.py:26-66) | none | none | developer | Y | B | none today (all three match the enum); drift hazard only. |
| BR-7 | berb/evolution.py:40-48,58,211,225,245,338,357,460,544-553; berb/metaclaw_bridge/lesson_to_skill.py:25,132-134,208-210; berb/metaclaw_bridge/config.py:27; berb/pipeline/metaclaw_post.py:50 | lesson `severity` and `category` (free `str` shadowing `LessonCategory`) | severity written: `"info"`,`"warning"`,`"error"`; reader also knows `"critical"` (never written); category enum `system/experiment/writing/analysis/literature/pipeline` | writers evolution.py:211 (error), :225/:245/:338 (warning), :357 (error); readers lesson_to_skill.py:134, evolution.py:460,489 | `lessons.jsonl` (evolution.py:408) | none | agent (prompt overlay), developer | Y | B | Min-severity default disagrees across three sites (`"error"` config.py:27, `"warning"` metaclaw_post.py:50 and lesson_to_skill.py:142); category mapped three times (evolution.py:544, stage_skill_map.py:133, lesson_to_skill.py:208); `LessonEntry.category: str` not `LessonCategory`. |
| BR-8 | berb/evolution.py:197-250 | `extract_lessons` raw compares on `StageResult` | substrings `"failed"`, `"blocked"` of `str(status)`; decision literals `"pivot"`,`"refine"` | evolution.py:204 `"failed" in status.lower() and error`; :219; :233 | lessons.jsonl via caller | none | agent | Y | B | A FAILED stage whose `error` is None/empty yields no lesson (:204 `and error`), and `rejected`/`paused`/`retrying` never yield one; unverified whether such results occur. |
| BR-9 | berb/evolution.py:266-283,374-394,402-464 | `EvolutionStore` lessons.jsonl + time-decay | implicit: fresh / aged (>`MAX_AGE_DAYS` 90 -> weight 0.0, invisible, never pruned) | append evolution.py:414-426; weight :378-394; stage-15 lookup `sorted(run_dir.glob("stage-15*"), reverse=True)` :266 | `lessons.jsonl`, `decision_structured.json` read | append from parallel stages, no lock | agent | Y | C | `sorted` is lexicographic, so `stage-15_v9` outranks `stage-15_v10` and a stale rationale is quoted; unverified (needs >=10 versions). |
| BR-10 | berb/reasoning/registry.py:56-62,137-153,188-203,272-276,387-443 | `ReasonerRegistry._registry`, `_singletons`, `auto_register_all._called` | unregistered / registered / singleton-cached | register :78; `get` :151-152; `get_async` :201-202; `clear_singletons` :272; `_called` :443 | none | sync `threading.Lock` (:145) and `asyncio.Lock` (:195) are different locks | developer | import-only (no `get_reasoner` caller outside `berb/reasoning`) | E | Singleton keyed by method type only: the first caller's `llm_client`/kwargs win for the process (:137-138), and `get`/`get_async` can each create an instance because they hold different locks; unverified at runtime (no live caller). |
| BR-11 | berb/reasoning/jury.py:144,162; debate.py:117,136; socratic.py:121,139; pre_mortem.py:163,171; dialectical.py:117,135; scientific.py:174,192; research.py:120,138; multi_perspective.py:175,210 | per-`execute` `self._run_id` on a (possibly singleton) instance | `None` / `"<method>-<8hex>"` | each `execute` overwrites | none | not safe under concurrent `execute` on a shared instance | developer | import-only | C | Concurrent executes on a registry singleton overwrite `_run_id`, so `_track_cost` (e.g. jury.py:456-474) books cost to the wrong run; unverified (no live caller). |
| BR-12 | berb/reasoning/debate.py:257-285,386-406; multi_perspective.py:322-323,522-523,629-644; bayesian.py:584-585,618-619; research.py:261-346,312,166-168,181; scientific.py:474,506-510; socratic.py:274-277,313-316; dialectical.py:249-252,299-302,346-349,403-406; pre_mortem.py:422-423,600-622 | `ReasoningResult.success` after LLM failure | `success=True` with canned content vs `error_result` | every `except Exception` in the helper methods falls back and the outer method still returns `ReasoningResult.success_result` (e.g. bayesian.py:219, debate.py:178, research.py:186) | returned in memory only | per call | agent (callers read `output`) | import-only (writing.pattern_memory uses `ResearchMethod`, pattern_memory.py:440-453) | A | An LLM outage yields a normal success: debate judge picks a winner from invented 0.5 strengths (debate.py:386-406), research loop reads failed `_identify_gaps` as `[]` and logs "converged" with fixed confidence 0.7 (research.py:166-168,181,346), multi_perspective returns "Fallback solution" via `_FallbackProvider` (:629-644). |
| BR-13 | berb/reasoning/jury.py:50-58,61-88,297-341,351-365,419-430 | `Juror.verdict` and `JuryResult.verdict` (free strings) | juror `"approve"`,`"reject"`,`"abstain"`; jury `"unanimous_approve"`,`"majority_approve"`,`"majority_reject"`,`"unanimous_reject"`,`"hung"` | juror set :329 (LLM text, unvalidated) and :339 fallback; vote count :353; jury verdict :356-365; result dict :212,216 (in-memory, not persisted: seed S9 claim WRONG) | none | sequential per juror | agent | import-only | A | Verdict strings are unvalidated: `"Approve"`/`"yes"` add a new `vote_count` key and fall to `"hung"` (jury.py:353-365); `jury_size=0` gives `0 == 0` -> `"unanimous_approve"` (:356); router-only construction (documented Option 2) hits `if self.llm_client:` false (:297) so all jurors abstain and a `hung` success is returned; `require_unanimous` is stored (:143) and never read. |
| BR-14 | berb/reasoning/socratic.py:405-511; berb/pipeline/stage_impls/_synthesis.py:384-459 | falsification gate issues list | empty list = pass; items with `severity` `"hard"`/`"soft"` | socratic.py:433-435 no client -> `[]`; :438-439 `[]`; :497-499 any exception -> `[]`; consumer `_synthesis.py:408-409,439,453` | `hypotheses.md` rewrite (:446) plus gate state in `_hypothesis_state` | `asyncio.run` per round (:407) | user (hypotheses), agent | Y (stage 8) | A | Any LLM failure, parse failure or non-list reply returns `[]` and `_synthesis.py:439/453` records `passed=True`/`gate_passed=True`, so an outage reads as "hypothesis passed falsification". |
| BR-15 | berb/metrics/collector.py:35-44,143-167,169-175,178-234 | `MetricsCollector` + `_COLLECTOR` singleton | counters/gauges/histograms keyed by label string; `_metric_types` | increment :56; set_gauge :69; observe :82; reset :169 (does not clear `_metric_types`/descriptions) | none | `threading.Lock` (non-reentrant, :36) | developer | import-only (no `observe`/`increment` caller in `berb/`; `PrometheusExporter.export` has no caller) | A | `get_all_metrics` holds `self._lock` (:145) and its histogram comprehension calls `get_histogram_stats` (:151) which takes the same non-reentrant lock (:114), so it deadlocks as soon as any histogram exists; reads also mutate the defaultdicts (:99,105,115). Unverified reach. |
| BR-16 | berb/metrics/reasoning_cost_tracker.py:284-325,391-403,445-472,526-533,645-649,726-752 | `ExtendedReasoningCostTracker` conn + `_tracker` singleton + budget | `_conn` None/open (lazy reopen after `close`); `budget_status` `"over"`/`"under"`; `Provider` StrEnum derived from model prefix (:410-439) | open :323; close :391-395; singleton replace :747-751 (old tracker not closed); budget :527-533 logs only | sqlite `cost_tracking.db`; JSON report `export_report` (:721) | `sqlite3.connect` without `check_same_thread=False` (:323) and no lock, unlike token_tracker.py:197 | developer; user via cost report | Y (deep_query_client._track_cost, deep_query_client.py:424-446) | A | Budget is advisory only (log at :530) while docstring promises enforcement; `budget_status` compares a windowed total to a per-run budget (:645-649); unknown model id prices as `(0, 0)` (:463) so cost reads $0 and "under"; cross-thread use raises `ProgrammingError`, swallowed by deep_query_client.py:445-446 so cost is dropped (unverified thread path). |
| BR-17 | berb/utils/token_tracker.py:149-200,269-282 | `TokenTracker._conn` | None / open (lazy reopen after `close`) | open :195-199; close :271-274 | sqlite `tracking.db` | `RLock` (:164), `check_same_thread=False` | developer | Y | C | none |
| BR-18 | berb/utils/time.py:32-34,88-104 | `_last_timestamp`, `_last_monotonic` | monotone float counters | `utc_timestamp` :93-102 | none | `_ts_lock` | developer | Y | C | none |
| BR-19 | berb/logging_setup.py:42-56,59-66,69-87 | `_current_run_id` ContextVar, `_factory_installed` | run id str / None; factory installed / not | `set_run_id` :56 (never unwound, docstring :52-55); `run_context` :62-66; `_install_record_factory` :75-87 | none | per-task contextvar | developer | Y | C | `set_run_id` leaks the id into later log lines in the same context for a long-lived process; cosmetic. |
| BR-20 | berb/data/__init__.py:122-136 | `_CACHE` seminal papers | None (unloaded) / list / `[]` after failure | `_load_all` :127-135 | none | none | developer | Y | C | A load failure caches `[]` for the process (:133-135, no retry); low. |
| BR-21 | berb/domains/detector.py:155-173 | `_profile_cache` | empty / populated | `load_all_profiles` :157-168; `if _profile_cache:` :158 | none | none | developer | Y | C | A profile that fails to load (:169-170) is missing for the process, and an empty directory is re-scanned every call (:161-163); low. |
| BR-22 | berb/domains/detector.py:34-41,72,131; berb/domains/prompt_adapter.py:127,145,190,198,206,222; berb/domains/adapters/math.py:59,78; physics.py:75,120; neuroscience.py:91; berb/domains/profiles/physics_chaos.yaml:5 | `experiment_paradigm` (free `str` shadowing `ExperimentParadigm`) | enum `"comparison"`,`"convergence"`,`"progressive_spec"`,`"simulation"`,`"ablation_study"`; raw compares to `"convergence"`,`"progressive_spec"`,`"simulation"` | read-only from YAML (detector.py:131) | YAML profiles | none | agent (prompt guidance) | Y | B | `physics_chaos.yaml:5` sets `experiment_paradigm: "Numerical simulation"`, which matches no branch (prompt_adapter.py:206 `== "simulation"`, :222), so that profile silently gets no simulation guidance; no validation at detector.py:131. |
| BR-23 | berb/overleaf/sync.py:20-45,47-123,133-145; berb/cli.py:553-588 | `OverleafSync.local_dir`, `_last_sync`, git working tree | unset (`local_dir` None) / set up / synced (`_last_sync`); merge-conflict state is implicit in the repo (markers) | `setup` :37-44; `push_paper` :87; `pull_changes` :98-108; `_git` :143 swallows non-zero exit if stderr contains "conflict" | in memory only; git repo under `run_dir/overleaf_repo` | subprocess, 60 s timeout | user (CLI) | Y (cli.py:562) | A | `berb overleaf --status` builds a fresh `OverleafSync` (cli.py:564-575) so `local_dir`/`last_sync` are always None; `--sync` prints "Overleaf sync complete." (cli.py:584) after a conflicted pull because `_git` returns normally (sync.py:143) and HEAD is unchanged so `pull_changes` returns `[]` (:101-102); `resolve_conflicts` is never called. |
| BR-24 | berb/overleaf/conflict.py:59-108 | marker parsers `in_conflict`, `state` | `"normal"`,`"ours"`,`"theirs"` | conflict.py:92-107; :62-84 | rewrites `.tex` in place (:53) | none | user | import-only (only `OverleafSync.resolve_conflicts`, uncalled) | C | An unterminated `<<<<<<<` leaves `state` at `"ours"` for the rest of the file (:95-107), dropping the remainder under `"theirs"`; an unknown strategy keeps neither side; unverified reach. |
| BR-25 | berb/overleaf/watcher.py:13-65 | `FileWatcher._snapshot`, `poll_loop` | snapshot mtime dict; loop running | `_take_snapshot` :22-29; `check_changes` :52; `while True` :61 | none | intended background thread, no stop flag | nobody | package-export only, no caller | D | none (uncancellable loop; unwired). |
| BR-26 | berb/adapters.py:73-124,145-193; berb/pipeline/executor.py:182-190,349-350,361-368; berb/pipeline/stage_impls/_literature.py:227-235; berb/cli.py:367,988; berb/server/routes/pipeline.py:125 | `AdapterBundle` default `Recording*` stubs and `MCP*Adapter` | call lists; stub results (status 200, ids) | defaults :176-182; `from_config` :184-193 | in-process lists only | none | user/agent | Y | A | Default `web_fetch` returns `status_code=200` for every URL (adapters.py:113-115, MCP stub :161-162), so with `openclaw_bridge.use_web_fetch` every source is stamped `"verified"` (_literature.py:231-232) and written to `sources.json` (:241) with no network call; gate auto-approval log (`adapters.memory.append("gates", ...)`, executor.py:350) and stage notifications (:184,361) go to in-process stubs and vanish; MCP notify/fetch fabricate success without any call (adapters.py:151-162). Whether `use_web_fetch` defaults on is unverified. |
| BR-27 | berb/templates/compiler.py:96-214 | `CompileResult` / compile-fix loop | `success` False/True; `attempts` 1..`max_attempts`; loop break reasons | `compile_latex` :155-212 | rewrites `.tex` (:198) | single-threaded | agent | Y | C | Fixes applied on the final attempt are written to disk (:198) but never recompiled, so `.tex` on disk differs from the log behind `success=False`; low. |
| BR-28 | berb/templates/converter.py:24-43,86 | `_render_counters` thread-local table/figure numbers | counters 0..n | `_reset_render_counters` :27-30 at convert start :86 | none | `threading.local` | agent | Y | C | none |
| BR-29 | berb/math/verification.py:132-160,164-186,236,284-290,328-333 | `VerifiedTheorem.verification_status`, `VerificationReport.overall_status` | `"verified"`,`"partial"`,`"failed"`; `overall_status` default `"unknown"` | status computed :284-290 | none | async gather | agent | import-only (benchmarks use `verify_equation_numerically`, evaluation_framework.py:328) | A | `generate_and_verify_theorem` imports `get_llm_client` from `berb.llm.client` (verification.py:236) which is defined nowhere in `berb/` and `await`s a sync `chat`, so the verified/partial/failed path always raises; no claims extracted also reads as `"failed"` (:282,290). Unverified reach. |
| BR-30 | berb/benchmarks/suite.py:84-196,246; berb/benchmarks/performance_suite.py:64-153; berb/benchmarks/evaluation_framework.py:86-120 | benchmark result objects (`success`, `passed`, placeholder scores) | `success=True` constant; `passed` bool | suite.py:156-163 placeholder review; :186-193 `success=True,  # Simplified` | `benchmark_report.json` (performance_suite.py:149) | none | developer | lazy-export only, no caller | D | Reproduction benchmark returns constant success and a fixed 5% deviation without running anything (suite.py:186-193); unwired so no live impact. |
| BR-31 | berb/trends/feeds.py:39-62,92-94,129,161; berb/trends/daily_digest.py:36-46; berb/cli.py:881-910 | feed fetch result (list) | non-empty list / `[]` | exception at feeds.py:50-51 and per-source returns `[]` | none | sequential | user (CLI digest) | Y | A | If every source fails, `fetch_recent_papers` returns `[]` and the digest reads "No new papers found" (daily_digest.py:42-46), indistinguishable from a quiet day. |
| BR-32 | berb/report.py:53-56,72-127; berb/pipeline/summary.py:44 | `final_status` string read from `pipeline_summary.json` | `StageStatus.value` of the last stage: `"pending"`,`"running"`,`"blocked_approval"`,`"approved"`,`"rejected"`,`"paused"`,`"retrying"`,`"failed"`,`"done"`; report knows `"done"`,`"failed"`, else warning icon | report.py:56 | `pipeline_summary.json` (written by the pipeline reader's `summary.py`) | none | user | Y | B | Raw string compares against `StageStatus` values (report.py:56); `final_status` is only the last executed stage's status (summary.py:44); fixed `stage-17`/`stage-22`/`stage-19` paths ignore versioned dirs except stage-14 (report.py:121-127), so a rolled-back run may print "Draft: not generated" (unverified, depends on rollback naming owned by pipeline reader). |
| BR-33 | berb/audit/reproducibility.py:139-162,350-364,413-445,447-462 | `ReproducibilityGenerator.artifacts` (artifact writers) | list of written paths | `_generate_audit_trail` :364; `_generate_cost_report` :425-445 constant `total_cost_usd: 0.65`; `_generate_trace` :456-462 | json/md/jsonl files | none | developer | class exported, only `write_reproducibility_files` is called (pipeline/packaging.py:249-251) | D | Generator writes fabricated cost ($0.65), a canned decision log ("Decision made to proceed with experimentation", :395-396) and a placeholder trace; unwired, the live helper `write_reproducibility_files` (:52-113) does not fabricate. |
| BR-P1 | berb/mnemo_bridge/__init__.py:88-141,351,369 | `MnemoBridge._client` (httpx.AsyncClient created in `__init__` :123, `close` :133) and `{"status": "error"/"unhealthy"}` dicts | open/closed client; status strings | :133, :351, :369 | none | async | developer | N (parked D-08) | D | none recorded (parked). |
| BR-P2 | berb/reasoner_bridge/__init__.py:34-52,199-224 | `ReasonerBridge`, `PerspectiveType`, `StressScenario` | enums | none read | none | none | developer | N (parked D-08) | D | none recorded (parked). |
| BR-P3 | berb/i18n/multilingual.py:34,223-228,539-598; berb/i18n/academic_languages.py:33 | `_adapter` global, `_current_language`, `SupportedLanguage`, `WritingDirection` | enums | multilingual.py:558,598 | none | none | developer | N (parked) | D | none recorded (parked). |
| BR-P4 | berb/integrations/scite_mcp.py:32 | `SciteCitationType` | enum | none read | none | none | developer | N (parked) | D | none recorded (parked). |
| BR-P5 | berb/voice/commands.py:10; berb/voice/synthesizer.py | `VoiceCommand` StrEnum, synthesizer | enum | none read | none | none | developer | N (parked) | D | none recorded (parked). |
| BR-P6 | berb/domains/experiment_schema.py:17,25; berb/writing_guide.py | `ConditionRole`, `ExperimentType` enums; writing guide | enums | none read | none | none | developer | N (parked) | D | none recorded (parked). |

## Seed verification

| seed | verdict | detail |
|---|---|---|
| IN-14 `metaclaw_bridge/session.py:19-45` `_active` | CONFIRMED (class C) | `_active` set True at session.py:19, False at :45, exposed at :53-55, no reader. Worse than the seed says: `get_headers` (:22) has no caller and the session object is created only at run end (metaclaw_post.py:121), see BR-2. |
| brief: `reasoning/jury.py:212` untraced S9 writer | WRONG as S9 | jury.py:212 and :216 are keys in the in-memory `ReasoningResult.output` dict (:208-230); nothing in jury.py persists them. Jury state is catalogued as BR-13 (free-string verdict vocabulary, not persisted). |
| Parked list (`berb.i18n`, `berb.voice.*`) | CONFIRMED parked/unwired | baseline lists `i18n*`, `voice.commands`, `voice.synthesizer` as parked; `voice.transcriber` is wired (70 loc, stateless config holder). `berb.hyperagent` is outside this cluster. |

No other seed row touches files in this cluster.

## Census mapping

All 56 census rows.

S1
- calendar/planner.py:60 -> dismissed: display label in a milestone dict from a fixed 8-step table (planner.py:15-24,58-63), stateless.
- evolution.py:559 -> BR-7 (memory metadata copy of `stage_name`).
- logging_setup.py:83 -> BR-19.
- metrics/reasoning_cost_tracker.py:99 -> dismissed: `phase` is a field in `ReasoningCostRecord.to_dict`, a label not a state (see BR-16 for the tracker).
- mnemo_bridge/__init__.py:351, :369 -> BR-P1.
- reasoning/jury.py:212, :216 -> BR-13 (transient output dict, not persisted).
- reasoning/jury.py:329, :339 -> BR-13.

S2
- metaclaw_bridge/session.py:45 -> BR-1.

S3
- report.py:56 -> BR-32.

S4
- domains/adapters/math.py:59, :78; neuroscience.py:91; physics.py:75, :120; domains/prompt_adapter.py:190, :198, :206 -> BR-22.
- domains/detector.py:34 (ExperimentParadigm) -> BR-22; detector.py:44 (MetricType) -> BR-22 (default `["scalar"]` list of raw strings, detector.py:94).
- domains/experiment_schema.py:17, :25 -> BR-P6.
- evolution.py:40 (LessonCategory), :460 (`severity == "error"`) -> BR-7.
- export/latex_exporter.py:229 -> dismissed: config template-name dispatch (latex_exporter.py:224-229), no lifecycle.
- export/multi_format.py:29 (ExportFormat) -> dismissed: config enum; `ExportResult` is a per-call accumulator (multi_format.py:155-204), no persisted or shared state.
- i18n/academic_languages.py:33, i18n/multilingual.py:34 -> BR-P3.
- integrations/scite_mcp.py:32 -> BR-P4.
- metrics/reasoning_cost_tracker.py:48 (Provider) -> BR-16.
- reasoner_bridge/__init__.py:34, :43 -> BR-P2.
- reasoning/base.py:21 (MethodType) -> BR-10 (registry key).
- reasoning/jury.py:50 (JurorRole) -> BR-13.
- reasoning/multi_perspective.py:56 (PerspectiveType) -> BR-12 (loop-local perspective set; fallback behaviour).
- report.py:56 ('done', 'failed') -> BR-32.
- templates/converter.py:841, :1827 -> dismissed: markdown heading text match at parse time (`sec.heading_lower == "abstract"`), no state.
- voice/commands.py:10 -> BR-P5.

S5
- data/__init__.py:127 -> BR-20.
- domains/detector.py:157, :168 -> BR-21.
- i18n/multilingual.py:598 -> BR-P3.
- logging_setup.py:71 -> BR-19.
- metrics/collector.py:184 -> BR-15.
- metrics/reasoning_cost_tracker.py:745 -> BR-16.
- utils/time.py:88 -> BR-18.

S6
- evolution.py:268 -> dismissed: read-only `.exists()` on the stage-15 artifact `decision_structured.json`, not a marker written by this module; its lookup ordering is BR-9.

S9
- audit/reproducibility.py:364, :444, :495 -> BR-33 (not called by the pipeline; fabricated cost/trace content).
- metrics/reasoning_cost_tracker.py:721 -> BR-16 (`export_report` snapshot including `budget_status`).

Rows unmapped: 0.

## Module coverage

Wired modules in slice (87):
- berb — none: package init
- berb.__main__ — none: CLI shim
- berb._lazy — none: stateless re-export helper (one-shot namespace cache, _lazy.py:55,77)
- berb.adapters — BR-26
- berb.audit — none: re-export
- berb.audit.reproducibility — BR-33
- berb.benchmarks — none: lazy re-exports
- berb.benchmarks.evaluation_framework — BR-30
- berb.benchmarks.performance_suite — BR-30
- berb.benchmarks.suite — BR-30
- berb.calendar — none: re-export
- berb.calendar.deadlines — none: conference table loader (only `yaml_path.exists()` at :87, config presence; read by grep, not in full)
- berb.calendar.planner — none: stateless timeline calculator
- berb.calendar.reminder — none: stateless, `days_until in reminder_days` per call (no "already reminded" state exists)
- berb.data — BR-20
- berb.domains — none: re-export
- berb.domains.adapters — none: re-export
- berb.domains.adapters.{biology, chemistry, economics, generic, ml, security, robotics} — none: stateless prompt text builders (robotics.py:38 reads paradigm for display only)
- berb.domains.adapters.math, .neuroscience, .physics — BR-22
- berb.domains.detector — BR-21, BR-22
- berb.domains.prompt_adapter — BR-22
- berb.evolution — BR-7, BR-8, BR-9
- berb.export — none: re-export
- berb.export.latex_exporter — none: stateless renderer (template dispatch dismissed)
- berb.export.multi_format — none: per-call result accumulator
- berb.hardware — none: re-detected each call, no cache
- berb.logging_setup — BR-19
- berb.math — none: re-export
- berb.math.verification — BR-29
- berb.metaclaw_bridge — none: re-export
- berb.metaclaw_bridge.config — BR-3
- berb.metaclaw_bridge.lesson_to_skill — BR-7 (conversion itself stateless)
- berb.metaclaw_bridge.prm_gate — BR-4
- berb.metaclaw_bridge.session — BR-1, BR-2
- berb.metaclaw_bridge.skill_feedback — BR-5
- berb.metaclaw_bridge.stage_skill_map — BR-6
- berb.metrics — none: re-export
- berb.metrics.collector — BR-15
- berb.metrics.prometheus — BR-15 (stateless formatter over the collector)
- berb.metrics.reasoning_cost_tracker — BR-16
- berb.overleaf — none: re-export
- berb.overleaf.conflict — BR-24
- berb.overleaf.formatter — none: pure string transforms
- berb.overleaf.sync — BR-23
- berb.overleaf.watcher — BR-25
- berb.prompts — none: `PromptManager` copies defaults at init and is read-only afterwards (prompts.py:90-98)
- berb.quality — none: pure functions
- berb.reasoning — none: re-export
- berb.reasoning.base — BR-10 (MethodType), BR-12 (result factories)
- berb.reasoning.registry — BR-10
- berb.reasoning.jury — BR-11, BR-12, BR-13
- berb.reasoning.socratic — BR-11, BR-12, BR-14
- berb.reasoning.{bayesian, debate, dialectical, multi_perspective, pre_mortem, research, scientific} — BR-11, BR-12 (bayesian has no `_run_id`)
- berb.report — BR-32
- berb.templates — none: re-export
- berb.templates.compiler — BR-27
- berb.templates.conference — none: static venue templates (grep found no state; not read in full)
- berb.templates.converter — BR-28
- berb.templates.results_table_builder — none: stateless builder (grep found no state; not read in full)
- berb.trends — none: re-export
- berb.trends.feeds — BR-31
- berb.trends.daily_digest — BR-31
- berb.trends.auto_topic, .opportunity_finder, .trend_analyzer — none: stateless scorers/heuristics (LLM failure falls back to heuristics, opportunity_finder.py:52-54, treated as degraded output not a verdict)
- berb.utils — none: re-export
- berb.utils.atomic — none: loop-local retry in `replace_with_retry` (atomic.py:47-57)
- berb.utils.sanitize — none: pure string functions (read by grep only)
- berb.utils.thinking_tags — none: pure string functions (read by grep only)
- berb.utils.time — BR-18
- berb.utils.token_tracker — BR-17
- berb.voice — none: package marker
- berb.voice.transcriber — none: holds two config strings (transcriber.py:16-17), stateless

Parked modules (not wired): domains.experiment_schema -> BR-P6; i18n, i18n.academic_languages, i18n.multilingual -> BR-P3; integrations, integrations.scite_mcp -> BR-P4; mnemo_bridge -> BR-P1; reasoner_bridge -> BR-P2; voice.commands, voice.synthesizer -> BR-P5; writing_guide -> BR-P6.

## Unread / uncertain

- Not read in full (grep/skim only, no machine found): calendar.deadlines, templates.conference, templates.results_table_builder, utils.sanitize, utils.thinking_tags, domains/adapters/{biology,chemistry,economics,generic,ml,security,robotics}, trends.{auto_topic,opportunity_finder,trend_analyzer}, export.latex_exporter, templates.converter (only lines 20-90 and the two census lines), templates.compiler (loop at :94-214 read, fixers :217-420 and sanitizers skimmed by grep), math.verification (status logic and `_extract`/`_run` parts only), benchmarks.* (state-bearing parts only), reasoning bayesian/pre_mortem/dialectical/scientific/socratic (fallback and execute paths only).
- Parked modules were not read beyond grep for class/global/status lines (mnemo_bridge, reasoner_bridge, i18n.*, integrations.scite_mcp, voice.*, domains.experiment_schema, writing_guide).
- Whether `use_web_fetch` (BR-26) defaults to on, and whether `config.metaclaw_bridge` is ever enabled in practice (BR-2, BR-4, BR-5), were not checked; both live in `berb.config` (other reader).
- Reasoning package (BR-10 to BR-14, except BR-14): no caller found outside `berb/reasoning` except `writing/pattern_memory.py` (`ResearchMethod`) and `ExperimentDesign` imports; runtime reach is unverified. BR-14 (`FalsificationCritic`) is live in stage 8.
- BR-16 cross-thread `sqlite3.ProgrammingError`: logic read from reasoning_cost_tracker.py:323 vs token_tracker.py:187-199, thread of the actual caller not traced.
- BR-32 rollback directory naming is owned by the pipeline reader (`iterative.py`); the report's stage-dir assumption is not confirmed against it.
- Consumers of `MetaClawSession` outside `metaclaw_post.py` and `get_headers` consumers beyond a repo-wide grep of `berb/` were not checked in `tests/`.
