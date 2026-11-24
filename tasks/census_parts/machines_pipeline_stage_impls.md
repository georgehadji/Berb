# P1b cluster read: berb.pipeline.stage_impls (id prefix SI-)

Scope: all 13 wired modules under `berb/pipeline/stage_impls/`. Read-only; no pipeline run, so every end-to-end claim is reasoned from code. Directory-rename and marker machines whose writer lives in `berb/pipeline/iterative.py` or `_io_helpers.py` are listed here because the readers are in this cluster. Paths below are relative to `berb/pipeline/stage_impls/` unless prefixed.

## Machines

| id | file:line | holder | states (exact literals) | transition sites (file:line) | persisted where | concurrency | who sees it | wired? | class | suspected defect |
|----|-----------|--------|-------------------------|------------------------------|-----------------|-------------|-------------|--------|-------|------------------|
| SI-01 | _execution.py:223-237 | local `run_status`, copied into run payload | `"rejected"`, `"completed"`, `"partial"`, `"failed"`; also `"simulated"` (358), `"completed"`/`"failed"` (378, 539); `experiment_repair.py:916` writes only `"completed"`/`"failed"`; `_analysis.py:181` hard-codes `"completed"` | _execution.py:223, 229, 231, 237, 242, 259, 279, 358, 378, 539, 546; _analysis.py:181 | `stage-12/runs/run-1.json` key `status`; stage-14 `experiment_summary.json` best_run | sequential; sandbox subprocess underneath | developer, agent (stage 17 and 20 prompts) | yes | B | The only consumers compare to `"failed"` (_review.py:570, 673), so `"rejected"`, `"partial"` and `"simulated"` are all treated as not failed; and when the search path writes zero run files (it writes only for good_nodes, _execution.py:535) the draft block at _paper_writing.py:1813-1848 starts from `all_simulated = True` and tells the writer the data is simulated. Zero-run misreport is reasoned from code, not run. |
| SI-02 | _execution.py:867-1337 | locals `best_metric`, `best_files`, `best_version`, `no_improve_streak`, `consecutive_no_metrics`, `prior_timed_out`, `timeout_refine_attempts`; persisted `refinement_log.json` | `stop_reason`: `"max_iterations_reached"`, `"llm_unavailable"`, `"wall_clock_time_cap"`, `"consecutive_no_metrics"`, `"no_improvement_for_2_iterations"`; `converged` bool; dirs `experiment_v{iteration}`, `refine_sandbox_v{iteration}`, `refine_sandbox_v{iteration}_fix`, `experiment_final` | _execution.py:881, 907, 947, 984, 1051, 1136, 1161, 1208, 1263, 1280, 1285, 1287-1289, 1291, 1292-1294, 1302, 1311, 1337 | `stage-13/refinement_log.json`, `experiment_v*/`, `experiment_final/` | sequential loop, max 10 iterations | developer, agent (stage 14 and 17 read the log) | yes | A | The `elif validation.ok and best_version == "experiment/"` branch (1292-1294) is the only adoption path outside sandbox/docker, and `no_improve_streak` / `consecutive_no_metrics` change only inside the sandbox/docker branch (1153-1291); in ssh_remote or colab_drive mode the loop therefore runs every iteration (up to 10 LLM calls) with no stop condition and no later candidate is adopted. Reasoned from code, mode not run. |
| SI-03 | _io_helpers.py:25-57 (readers); iterative.py:135-150 (writer); readers in this cluster: _analysis.py:68, _code_generation.py:156, 278, _experiment_design.py:158, 178-203, _review.py:696, _paper_writing.py:1494, 1521, 2030, 2066, 2110, _export.py:466, 1235, _execution.py:790-812, 619, 626 | directory-name suffix on `stage-NN` | `stage-NN` (live) vs `stage-NN_v{attempt}` (archived by `_version_rollback_stages`) | rename in iterative.py:135-150 for NN from rollback target to 15; readers pick with `sorted(..., reverse=True)` | filesystem under run_dir | rename happens between stages; no lock | developer only | yes | A | `stage-NN_vK` sorts after `stage-NN`, so a reverse sort returns the archived superseded version first. After a PIVOT (rollback to stage 8) stage 9 reads the old `hypotheses.md` and `hypothesis_state.json`; after a REFINE (rollback to 13) stage 14 reads the archived `refinement_log.json`; the glob readers in stage 10, 17, 20, 22 pick `_vK` the same way. Verified at helper and call-site level; end-to-end not run. Stage 20 rollback to stage 16 renames nothing because `range(16, 16)` is empty. |
| SI-04 | _analysis.py:797-845 | return value of `_parse_decision`; `StageResult.decision` | `"proceed"`, `"pivot"`, `"refine"`; default `"proceed"` | _analysis.py:988, 1002-1010, 1018 | `stage-15/decision.md`, `decision_structured.json`; read by archive (_archive.py:57) and paper writing (_paper_writing.py:68) as free text | sequential | developer, agent, runner | yes | A | The fallback regex `(?:^|##\s*Decision\s*\n\s*)KW` under MULTILINE matches any line starting with the keyword, so a decision text containing a line "PIVOT is not warranted..." returns `"pivot"` and triggers a rollback to HYPOTHESIS_GEN, contrary to the docstring. Verified by reading the regex. |
| SI-05 | _review.py:570-955 | local `verdict`, gate outcome | quality report `verdict` free string, default `"proceed"` (656); outcomes FAILED, DONE with `decision="degraded"` (929), DONE passed; `claim_adjudication.json` `status` (771) | _review.py:570, 656, 673, 895-955; _figure_helpers.py:71-79 (default report) | `stage-20/quality_report.json`, `ensemble_review.md`, `claim_adjudication.json` | sequential; ensemble reviewers parallel inside | user, agent, runner (GATE_ROLLBACK to PAPER_OUTLINE) | yes | A | `_default_quality_report` scores `threshold*0.7`, below threshold, so an LLM outage or unparseable gate response fails the gate and GATE_ROLLBACK rewrites the paper although nothing was judged (outage reported as a verdict). Verified at the default-report call. |
| SI-06 | _review.py:864-881 | marker file `ensemble_veto_used.json` at run_dir root | absent / present | _review.py:865 (read), 871 (write) | run_dir root; never deleted | sequential across rollback cycles | developer | yes | A | Written whenever the ensemble rejects and the marker is absent, whether or not the score also failed (895); nothing resets it, so after one rollback the second rewrite is never vetoed even if the ensemble rejects again. The ensemble is wrapped in `except Exception` with a debug log (855-856), so an ensemble outage also means no veto. Confirms seed PC-9. |
| SI-07 | _review.py:921-922; _export.py:393-394 | marker file `degradation_signal.json` at run_dir root | absent / present | write _review.py:922; read _export.py:394 | run_dir root; never deleted | sequential | user (degraded notice in the export), agent | yes | A | The marker is never removed, so a run that degrades at stage 20, rolls back and then passes the gate still has stage 22 insert the degraded notice into the final paper. Reasoned from the write and read sites. |
| SI-08 | _synthesis.py:366-471; _experiment_design.py:158-203 | dict `_hypothesis_state` with `gate_passed` | `gate_passed` default `True`; set at 453; exception means passes (462-463) | _synthesis.py:366-371, 400-423 (`_max_rounds = 2`), 453, 462-463, 465; _experiment_design.py E09_GATE_REJECT path | `stage-08/hypothesis_state.json` | sequential | agent, runner (stage 9 FAILED) | yes | A | A falsification-gate exception writes the same `gate_passed: true` as a genuine pass, and stage 9 treats an absent or unparseable file as a pass; after a PIVOT stage 9 reads the archived `stage-08_v1` copy first (SI-03), so the gate verdict can belong to the superseded hypothesis. |
| SI-09 | _literature.py:437, 470, 627, 720, 732, 784-797 | local bool `real_search_succeeded` to `search_meta.json` key `real_search` | `True`/`False` | _literature.py:437, 470 (set), 509-533 and 536-563 (uploads, seminal injection; do not set it), 627, 720, 732, 784-797 | `stage-04/search_meta.json`, `web_search_result.json` | sequential; `_MAX_EXPANSION_ROUNDS = 3` | developer, runner | yes | A | Stage 5 returns FAILED `E05_GATE_REJECT` when `real_search is False`; uploaded PDFs and seminal injection do not set the flag, so a run whose corpus is only user uploads and whose online search failed is rejected although it has a real corpus. Reasoned from code. |
| SI-10 | _literature.py:213-236 | source dict key `status` | `"available"`, `"verified"`, `"unreachable"`, `"unknown"` | _literature.py:213, 222, 231, 236 | `stage-03/sources.json` | sequential | nobody (write-only) | yes | C | `"available"` rows carry a fabricated `verified_at` stamp, but no reader was found (grep), so it is harmless today. |
| SI-11 | _paper_writing.py:535-560, 600-619, 674-699, 2346-2376 | draft text (stub placeholders) | no flag; placeholder strings "[... could not be generated — regenerate this stage]", `\| Ours \| --- \|` table | _paper_writing.py:535, 600, 674, 2346 | `stage-17/paper_draft.md` | sequential, optional parallel writer behind `BERB_EXPERIMENTAL_PARALLEL_WRITER` (2281) | user (final paper), agent | yes | A | On a per-part LLM failure the stage substitutes a stub and returns DONE; grep found no downstream check for the stub text, so a paper with placeholder sections can pass stage 20 and be exported. Verified by grep of stage_impls only. |
| SI-12 | _paper_writing.py:2508, 2618, 2628, 2630, 2710; _review.py:771-780 | `ClaimVerdict` on claim manifest | `NOT_CHECKED`, `SUPPORTED`, `UNSUPPORTED`; adjudication `"unsupported"` (780) | set once at _paper_writing.py:2508, 2618, 2628, 2630, 2710; no later transition in stage_impls | claim manifest and `claim_adjudication.json` | sequential | agent, developer | yes | C | Missing evidence registry: `VerifiedEvidenceRegistry.load` returns an empty registry for a missing file (`berb/integrity/registry.py:157-159`), so all empirical or comparative claims would become UNSUPPORTED; unverified that the call site passes a missing path in a normal run. |
| SI-13 | _export.py:959-1025, 192-314, 394-434, 1126, 1294-1524; _paper_writing.py:2165-2190 | gate outcome of stage 22 | FAILED on `invalid_citations.json` (960); FAILED when `_export_report.hallucinated > 0` (998-1020); proceed without gate on exception (1021-1025); `severity == "REJECT"` sanitization (1126); cross-model verdict via `verdict.verdict.value` (309) | _export.py:292, 295, 309, 960, 998-1025, 1126 | `invalid_citations.json`, `hallucination_report.json`, `cross_model_findings.json` in stage_dir | sequential | user, runner | yes | A | Outage is treated both ways: a verification exception fails open ("proceeding without gate", 1021-1025), while an empty pre-verification result in stage 17 marks every cite HALLUCINATED (_paper_writing.py:2175-2190, depends on seed IN-1) and stage 22 then fails closed; also `.is_file()` at 960 can see a stale `invalid_citations.json` left in the same stage_dir by an earlier attempt. Stale part unverified. |
| SI-14 | _citations.py:505-506, 613, 647-658 | stage 23 verify and filter | `VerifyStatus` values consumed (613); `RELEVANCE_THRESHOLD = 0.5`, `_DEFAULT_RELEVANCE = 0.7`, `MAX_CITATIONS = 60` | _citations.py:505, 613, 647-658 | `retraction_findings.json`, `anchor_findings.json`, filtered bib | sequential | user | yes | C | Retraction lookup failure is swallowed (505-506, seed IN-12), so an outage looks like no retractions; BUG-26 fallback keeps the original bib when more than 50 percent would be stripped. Noted, no concrete failure shown. |
| SI-15 | _code_generation.py:770-860, 943, 1217-1436, 1535-1552 | loop locals `repair_attempt`, `attempt`, `alignment_ok`, `alignment_note`; marker `validation_report.md` | `max_repair = 5`, `_max_regen = 2`; marker present/absent | _code_generation.py:770-817, 831-860, 849, 943, 1217-1436, 1535, 1540-1552 | `stage-10/validation_report.md` | sequential | developer | yes | C | Loop-local counters are correct; `validation_report.md` is used as a presence flag (1535) and may be stale across attempts in the same stage_dir. Unverified. |
| SI-16 | _archive.py:159-168; _paper_writing.py:1479; iterative.py:214 (writer, outside cluster) | marker `experiment_summary_best.json`, `analysis_best.md` | absent / present | read _archive.py:159-168, _paper_writing.py:1479 | run_dir | sequential | agent | yes | C | Producer is outside this cluster (core owner); readers prefer it over the live summary. Not read at the writer, so no defect claimed. |
| SI-17 | _topic.py:220-243 | `config.research.topic` mutated by auto-refine (IMP-35) | original topic / suggestion | _topic.py:232 (mutate), 234-238 (rewrite goal) | in-memory config; `goal.md` only if `run_dir/goal.md` exists | sequential | user, agent | yes | C | Stage 1 writes `goal.md` into `stage_dir` (line 97) while stage 2 rewrites `run_dir / "goal.md"` only if it exists, so the goal file may keep the old topic. Unverified (depends on whether anything writes `run_dir/goal.md`). |
| SI-18 | _code_generation.py:451-452, 557-558 | local flags `_beast_mode_used`, `_code_agent_active` | bool | _code_generation.py:451, 452, 557, 558 | none | sequential | developer | yes | C | none |
| SI-19 | _analysis.py:730 | `figure_plan.json` shape | dict (stage 14) vs list (orchestrator) | _analysis.py:730 | `stage-14/figure_plan.json` | sequential | developer | yes | C | Shape differs between writers; no failing reader verified. Unverified. |
| SI-20 | _paper_writing.py:443 | cwd-relative cache `.berb_cache/writing_patterns.json` | present / absent | _paper_writing.py:443 | cwd | none | developer | yes | C | none |
| SI-21 | _paper_writing.py:841-878 | per-section `status` and `bullet_status` | `"severely_short"`, `"short"`, `"long"`, `"ok"`; `"high"`, `"ok"` | _paper_writing.py:841, 849, 857, 859, 876-878 | `stage-17/draft_quality.json` (read at _review.py 167, 288) | sequential | agent | yes | C | Stateless per-section analysis, recomputed each run; none. |
| SI-22 | _code_generation.py:1151-1162 | code review verdict | default `"unknown"`, else LLM string | _code_generation.py:1151, 1157, 1162 | `stage-10/code_review.json` | sequential | developer | yes | C | Free-string verdict with no reader found in the lines read; none claimed. |

## Seed verification

- PC-8 (run status vocabularies): PARTLY. `_execution.py:223-237` uses `"rejected"`, `"completed"`, `"partial"`, `"failed"` (plus `"simulated"` at 358); `experiment_repair.py:916` uses only `"completed"`/`"failed"`. The vocabularies overlap but the only consumers compare to `"failed"` (_review.py:570, 673), so damage is low.
- PC-9 (ensemble veto marker): CONFIRMED at `_review.py:864-881`. Correction: it is written whenever the ensemble rejects and the marker is absent, even when the score also failed, and nothing resets it.
- PC-4 / PC-5 / PC-6 (iterative and runner rollback): out of scope for this cluster; the read side in stage_impls is SI-03.
- ClaimVerdict (IN-13): PARTLY. Values are set once at `_paper_writing.py:2508, 2618, 2628, 2630, 2710` with no coercion or transition in stage_impls.
- IN-1 (empty verification result): CONFIRMED as consumer effect at `_paper_writing.py:2175-2190` (all cites HALLUCINATED, `verified_keys = set()`) and `_export.py:998-1020` (FAILED).
- IN-12 (swallowed retraction lookup): CONFIRMED at `_citations.py:505-506`.

## Census mapping

Rows are `signal file:line`. All 83 rows of `cluster_pipeline_stage_impls.tsv`.

S1:
- S1 _analysis.py:1003 -> SI-04
- S1 _analysis.py:181 -> SI-01
- S1 _code_generation.py:1157 -> SI-22
- S1 _execution.py:259 -> SI-01
- S1 _execution.py:358 -> SI-01
- S1 _execution.py:378 -> SI-01
- S1 _execution.py:509 -> dismissed: `context={"phase": "baseline"}` is a call argument label, not state
- S1 _execution.py:539 -> SI-01
- S1 _execution.py:635 -> dismissed: descriptive `"mode"` label in a payload, no reader found in stage_impls
- S1 _execution.py:872 -> dismissed: `config.experiment.mode` copied into a payload, config value not a transitioning state
- S1 _export.py:309 -> SI-13
- S1 _literature.py:213 -> SI-10
- S1 _literature.py:222 -> SI-10
- S1 _literature.py:231 -> SI-10
- S1 _literature.py:236 -> SI-10
- S1 _paper_writing.py:841 -> SI-21
- S1 _paper_writing.py:849 -> SI-21
- S1 _paper_writing.py:857 -> SI-21
- S1 _paper_writing.py:859 -> SI-21
- S1 _review.py:771 -> SI-12
- S1 _review.py:915 -> SI-05
- S1 _synthesis.py:367 -> SI-08

S3:
- S3 _execution.py:242 -> SI-01
- S3 _review.py:570 -> SI-01
- S3 _review.py:673 -> SI-01

S4:
- S4 _code_generation.py:177 -> dismissed: network-policy config comparison choosing prompt text
- S4 _code_generation.py:197 -> dismissed: `tier` config comparison choosing prompt text
- S4 _code_generation.py:243 -> dismissed: network-policy config comparison choosing prompt text
- S4 _code_generation.py:784 -> dismissed: stateless filter of validator issue severity
- S4 _code_generation.py:837 -> dismissed: stateless validator severity check
- S4 _execution.py:242 -> SI-01
- S4 _export.py:1000 -> SI-13
- S4 _export.py:1423 -> dismissed: `text_without_insight` is a log-only branch
- S4 _paper_writing.py:936 -> dismissed: `hl == "abstract"` word-count check, stateless
- S4 _review.py:570 -> SI-01
- S4 _review.py:673 -> SI-01
- S4 _review.py:780 -> SI-12

S6:
- S6 _code_generation.py:1535 -> SI-15
- S6 _export.py:394 -> SI-07
- S6 _export.py:960 -> SI-13
- S6 _literature.py:627 -> SI-09
- S6 _literature.py:720 -> SI-09
- S6 _review.py:865 -> SI-06
- S6 _review.py:871 -> SI-06
- S6 _review.py:901 -> SI-05
- S6 _review.py:903 -> SI-05
- S6 _review.py:946 -> SI-05
- S6 _review.py:948 -> SI-05
- S6 _topic.py:235 -> SI-17

S7:
- S7 _execution.py:1136 -> SI-02
- S7 _execution.py:1161 -> SI-02
- S7 _execution.py:1263 -> SI-02
- S7 _execution.py:1285 -> SI-02
- S7 _execution.py:619 -> SI-03
- S7 _execution.py:626 -> SI-03

S9:
- S9 _analysis.py:1009 -> SI-04
- S9 _archive.py:107 -> dismissed: one-shot `bundle_index.json` written once by stage 21, never read back as state
- S9 _code_generation.py:1162 -> SI-22
- S9 _execution.py:279 -> SI-01
- S9 _execution.py:546 -> SI-01
- S9 _review.py:922 -> SI-07

S11:
- S11 _analysis.py:1003 -> SI-04
- S11 _analysis.py:1018 -> SI-04
- S11 _analysis.py:988 -> SI-04
- S11 _archive.py:57 -> dismissed: `decision.md` text read as pass-through to the stage result
- S11 _archive.py:66 -> dismissed: `decision.md` text pass-through
- S11 _code_generation.py:1151 -> SI-22
- S11 _code_generation.py:1157 -> SI-22
- S11 _execution.py:223 -> SI-01
- S11 _execution.py:229 -> SI-01
- S11 _execution.py:231 -> SI-01
- S11 _execution.py:237 -> SI-01
- S11 _execution.py:242 -> SI-01
- S11 _execution.py:259 -> SI-01
- S11 _export.py:292 -> SI-13
- S11 _export.py:295 -> SI-13
- S11 _export.py:309 -> SI-13
- S11 _paper_writing.py:111 -> dismissed: `decision.md` text pass-through
- S11 _paper_writing.py:68 -> dismissed: `decision.md` text pass-through
- S11 _review.py:656 -> SI-05
- S11 _review.py:915 -> SI-05
- S11 _review.py:929 -> SI-05

## Module coverage

- `__init__.py`: none: re-export only.
- `_analysis.py`: SI-04, SI-01 (hard-coded best_run status), SI-03 (reader at 68), SI-19.
- `_archive.py`: none for the stage itself (one-shot bundle, text pass-through); reads SI-16 marker.
- `_citations.py`: SI-14.
- `_code_generation.py`: SI-15, SI-18, SI-22; SI-03 reader at 156, 278.
- `_execution.py`: SI-01, SI-02, SI-03 (790-812, 619, 626).
- `_experiment_design.py`: SI-08 (consumer), SI-03 reader.
- `_export.py`: SI-13, SI-07, SI-03 readers at 466, 1235.
- `_literature.py`: SI-09, SI-10.
- `_paper_writing.py`: SI-11, SI-12, SI-21, SI-20, SI-16 reader, SI-03 readers.
- `_review.py`: SI-05, SI-06, SI-07, SI-12.
- `_synthesis.py`: SI-08.
- `_topic.py`: SI-17.

## Unread / uncertain

- `_paper_writing.py` partly unread: 147-340 (raw metrics), 340-505 (partly), 890-1060, 1101-1450 (`_review_compiled_pdf`, `_check_ablation_effectiveness`, `_detect_result_contradictions`, `_resolve_draft_anchors`), 1560-1805, 1984-2020.
- `_literature.py` 1-60 (imports and head of `_expand_search_queries`) not read.
- Not verified: whether anything writes `run_dir/goal.md` (SI-17); whether a normal run hands `VerifiedEvidenceRegistry.load` a missing path (SI-12); whether stage dirs are cleared between attempts (SI-13, SI-15 stale markers).
- No pipeline run: pivot and refine behaviour (SI-03), non-sandbox refine loop (SI-02) and zero-run misreport (SI-01) are reasoned from code only.
- Whether the runner honours contract `max_retries` was not checked.
- Writers of `experiment_summary_best.json` and `analysis_best.md` are in `iterative.py` (core owner); only readers were read here.
- No parked or dead modules found inside `stage_impls`.
