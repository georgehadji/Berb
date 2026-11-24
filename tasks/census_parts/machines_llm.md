# P1b cluster read: llm (prefix LL-)

Method: read fully `client.py`, `cost_tracker.py`, `model_cascade.py`, `smart_client.py`, `nadirclaw_router.py`, `prompt_cache.py`, `anthropic_adapter.py`, `acp_client.py`, `deep_query_client.py`, `output_limits.py`, `pricing.py` (code part), `cross_model.py` (lines 80-265); read the stateful parts of `openrouter_adapter.py`; grep-skimmed `registry.py`, `presets.py`, `vision.py`, `openrouter_models_data.py` and the parked modules. Callers checked in `berb/pipeline/executor.py`, `pipeline/runner.py`, `experiment/search/runner.py`, `pipeline/citation_verification.py`, `pipeline/stage_impls/_export.py`, `review/ensemble.py`.

Scope summary (answers the brief's "who holds it"):
- `LLMClient` breaker, rate limiter, Anthropic httpx client, cascade stats, NadirClaw cache, TokenTracker connection: **per client instance**. `executor.py:201` calls `create_llm_client(config)` on every stage execution, so each is **per stage execution**, not per run. A second run inherits nothing from them.
- `llm.cost_tracker._tracker` singleton (`cost_tracker.py:302-319`): **per process**. Nothing in `berb/` calls `close()` or `reset()` on it, so a second run in the same process (server: `server/routes/pipeline.py:115-121`) inherits every event of run 1.
- `deep_query_client` breaker and rate limiter (`deep_query_client.py:76, 90-95`): **per process module globals**; only `_reset_circuit_breaker()` (docstring "for tests") resets them. A second run inherits breaker state, cooldown and trip count.
- Cost attribution (`_current_stage`, `_current_phase`): **per asyncio task / thread context**.
- ACP named session `"berb"`: lives in an external `acpx` process, shared by name across client instances.

## Machines

| id | file:line | holder | states (exact literals) | transition sites (file:line each) | persisted where | concurrency | who sees it (user/developer/agent) | wired? | class (A/B/C/D/E) | suspected defect (or "none") |
|---|---|---|---|---|---|---|---|---|---|---|
| LL-1 | berb/llm/client.py:304-423 | `CircuitBreaker._state` (`CircuitBreakerState`) held on `LLMClient._circuit_breaker` (client.py:457-463) | `"closed"`, `"open"`, `"half_open"` (comment at 310) | closed->open client.py:411-412; open->half_open 377-380; half_open->closed 391-396; half_open->open 407-410; reset of failure_count on success while closed 397-398; entry gate `__enter__` 343-346; recorded by `__exit__` 362-365 | memory only | `threading.Lock` per breaker (339), `_can_execute`/`_on_*` locked; half_open admits every caller (383-384), no single-probe gate | nobody: `get_circuit_breaker_status` (471-475) and `get_status` (414-423) have zero callers in `berb/` | yes | A | One breaker wraps `_raw_call` for the whole model chain (client.py:767-777) and counts every exception including non-transient 400/403 "not allowed to use model", so 5 failures of one unavailable fallback model open the breaker for the healthy primary and `chat()` reports "All models failed. Last error: Circuit breaker open..." (chat 700-704). |
| LL-2 | berb/llm/client.py:676-704, 764-865, 706-745 | `chat()` model loop, `_call_with_retry` attempt counter, `preflight` status mapping | loop counters `attempt`, `last_error`; retryable HTTP set `(400, 429, 500, 502, 503, 504, 529)` (837) | next-model on `except Exception` 700-702; retry `continue` 801, 852, 859; exhausted `raise RuntimeError(...)` 863-865 (no `from`) | none | per call, loop-local | developer via `preflight` message; user via CLI preflight (cli.py:285) | yes | A | When retries are exhausted on 429/5xx the `RuntimeError` at 863 carries no `__cause__`, so `preflight` (733-745) sees no `HTTPError` and reports "All models failed" instead of "Rate limited - try again in a moment"; the final HTTP status is lost. |
| LL-3 | berb/llm/client.py:210-300 (use 449-454, 633-656, 561, 1355) | `TokenBucketRateLimiter._request_tokens` / `_token_tokens` / `_last_update` on `LLMClient._rate_limiter` | float buckets; allowed `(True, 0.0)` / denied `(False, wait)` | refill 245-260; consume 285-287; `chat` acquire 641, re-acquire 654, raise 645/656 | none | `threading.Lock` (239) | nobody (`get_rate_limiter_status` has no callers outside `MultiProviderLLMClient` delegate 1428-1430) | yes: primary path disables it (`rate_limit_enabled=False`, 561) but fallback clients built at 1355 get the default `rate_limit_enabled: bool = True` (197) | A | On a fallback-provider client the token bucket is capped at `tokens_per_minute` (255-258, default 90000), so any request whose estimate (prompt chars//4 + max_tokens, 635-639) exceeds 90000 can never be acquired and always raises "Rate limit still exceeded after waiting." (656); the primary has no such limit, so failover fails exactly on large-context calls. |
| LL-4 | berb/llm/client.py:1253-1438 | `MultiProviderLLMClient._current_provider_idx` | `0` only | init 1277; never reassigned (grep over repo: only 1277 and 1436); loop index `idx` is local 1385 | none | none | `get_provider_status` 1432-1438 (no callers) | yes | A | After failover to provider 2, `get_provider_status()` still reports `current_provider` = primary because the index is never updated; no provider health memory, so every call re-tries the failed primary first (and its per-client breaker, LL-1). |
| LL-5 | berb/llm/cost_tracker.py:111-132, 138-150, 208-290, 301-319 | process singleton `_tracker` (`CostTracker._events`) | event list grows only; `reset()` clears (275-278) | append 150; clear 278; singleton create 317-318 | memory; dumped to `<run_dir>/cost_report.json` (pipeline/runner.py:531-538) | `RLock` (129, 303) | user via cost_report.json; stage 12 budget gate (experiment/search/runner.py:85-87, tracker taken at 152) | yes | A | No code calls `close()` or `reset()`, so in server mode run 2 starts with run 1's events: run 2's `cost_report.json` reports run 1+2 spend and `BudgetGovernor.check` (search/runner.py:85-87) sees run 1's cost already consumed, ending run 2's stage-12 search early (unverified whether server code resets elsewhere: grep found no caller). |
| LL-6 | berb/llm/cost_tracker.py:132, 147-149, 289, 317 | `CostTracker._closed` | `False`, `True` | set True 289 (`close`); read 147, 317 | none | under `_lock` | nobody | yes | C | none: seed IN-6 is WRONG, `get_cost_tracker` replaces a closed singleton (317) and `_record_llm_cost` re-fetches it per call (client.py:1060), so events are not dropped; the flag is effectively unreachable because nothing calls `close()` (the real defect is LL-5). |
| LL-7 | berb/llm/cost_tracker.py:57-79 (set at pipeline/runner.py:198) | `ContextVar`s `_current_stage`, `_current_phase` | `None` or `int` / `str` | set 68-69, reset 72-74 | none | per asyncio task; copied by `to_thread` | developer (cost breakdown) | yes | C | none |
| LL-8 | berb/llm/pricing.py:418-442; cost_tracker.py:180-187 | implicit "price known / unknown" encoded as `cost_usd == 0.0` | known price, `None` (unknown) coerced to `0.0` | `get_price` returns None 442; coerced 187; recorded 189-201 | cost_report.json, in-memory events | none | user (cost_report), BudgetGovernor | yes | A | Unpriced models are recorded at $0.00 with only a log warning, so unknown looks free: I ran `PricingTable().get_price` and `"deepseek-v4-flash"` (the DeepSeek preset default, llm/__init__.py:123-126), `"gpt-5.2"`, `"MiniMax-M2.5"` all return `None`, hence a run on the DeepSeek preset reports $0 and never trips `budget_usd`. |
| LL-9 | berb/llm/model_cascade.py:92-247 | `CascadingLLMClient.chat` rung walk (`step_idx`, `last_response`, `last_error`) | rung index 0..n-1; outcomes: accepted, below-threshold, raised | accept 199-200 / 203-212; reject 220; error 193-196; end-of-loop return 224-226; fallback 228-247 | none | stateless per call | developer | yes, behind `cascade.enabled` (llm/__init__.py:206-234) | A | Seed IN-5 CONFIRMED: when rung 1 answers below threshold and the last rung raises, `last_response` (the cheap rejected answer) is returned at 224-226 with log "All cascade steps below threshold", the fallback model at 228 is never tried and the error is dropped; additionally a whitespace-only response passes `if not content` (296) then `stripped[-1]` (331) raises IndexError outside any try (202), aborting the cascade instead of escalating. |
| LL-10 | berb/llm/model_cascade.py:133-135, 274-276, 253-272 | `_total_requests`, `_cascade_exits` | counters | 177; 276 | none | `_stats_lock` | nobody: `get_stats()` has no caller in `berb/` (only a docstring in config.py:929) | yes | A | The documented calibration measure (exit distribution) is lost twice: the wrapper is rebuilt per stage execution (executor.py:201 -> `_maybe_wrap_cascade`) and nothing reads `get_stats()`, so the evaluator can never be calibrated from a run. |
| LL-11 | berb/llm/nadirclaw_router.py:195-225, 498-554; smart_client.py:239-255 | free-string `tier` on `ModelSelection` / `SmartLLMResponse` | `"simple"`, `"complex"` (analyze 209-214); `"mid"` (checked 526 only); `"explicit"`, `"default"` (smart_client 241, 254) | produced 209-214; consumed 524-529 | none | stateless | developer | yes, behind `nadirclaw.enabled` | A | `analyze` never returns `"mid"` (209-214), so the `tier == "mid"` branch (526) and `mid_model` config (smart_client.py:98) are unreachable and `tier_thresholds` (stored at 481, passed at smart_client.py:104) is read nowhere; a user setting `nadirclaw.mid_model` gets no effect. |
| LL-12 | berb/llm/nadirclaw_router.py:486-491, 581-611 | `NadirClawRouter._cache`, `_cache_times` | key present / expired / evicted | get+expire 583-591; set 598-611; clear 619-621 | none | no lock; dual-dict mutation | nobody | yes, behind `nadirclaw.enabled` | A | `_cache_get` does `self._cache_times[key]` (587) after `key in self._cache` (583) with no lock while `_cache_set` evicts with `min(self._cache_times, ...)` (599) during other threads' mutation, giving KeyError / "dictionary changed size during iteration"; unverified whether two threads share one router (`SmartLLMClient.complete` uses `to_thread`, smart_client.py:215; router is per stage). |
| LL-13 | berb/llm/smart_client.py:86-126, 392-396 (TokenTracker: utils/token_tracker.py:162-200, 269-274) | `SmartLLMClient._nadirclaw_enabled`, `_tracking_enabled`, `_tracker` (sqlite conn) | bool flags set once; conn `None` / open / closed | set 110/113, 123/126; `close()` 392-395 | `tracking.db` (sqlite) | `_db_lock` RLock in TokenTracker | nobody | yes, behind `token_tracking.enabled` | A | `SmartLLMClient.close()` has no caller (grep: none), and a client is built per stage, so one sqlite connection per stage execution is left open until GC (unverified impact). |
| LL-14 | berb/llm/__init__.py:153-203; pipeline/executor.py:192-225 | client ownership: `create_llm_client` called per stage; `llm = None` on failure or missing base_url/api_key | `llm = None`, `llm = candidate` | create 201; None on exception 218-220 or missing config 211-217; `adapters.llm = llm` 225 | none | stage threads | agent / developer | yes | A | Because every stage gets a fresh client, LL-1's breaker (and LL-3, LL-10, LL-12) never carries failure memory across stages, so during an outage each of the 23 stages burns full retries x models x backoff before failing; and a construction exception silently turns into `llm=None` (warning only). |
| LL-15 | berb/llm/deep_query_client.py:82-172, 450-501 | module globals `_cb_state`, `_cb_consecutive_429s`, `_cb_cooldown_sec`, `_cb_open_since`, `_cb_trip_count` | `"closed"`, `"open"`, `"half_open"` (86-88) | closed/half_open->open `_cb_on_429` 150, 161; open->half_open `_cb_should_allow` 119; ->closed `_cb_on_success` 137; test reset 98-107 | memory, process lifetime | `_cb_lock` (95); half_open allows all callers (127) | nobody | yes (citation_verification.py:563, novelty.py:243, cli.py:1195) | A | Same shape as seed IN-2: only 429 moves the machine, so a half_open probe that fails with a non-429 (return None at 487 or exhausted retries 500-501) leaves it `half_open`, and the state/cooldown are never reset between runs (only a test hook), so run 2 in the same process starts with run 1's open breaker and up to 600s cooldown. |
| LL-16 | berb/llm/deep_query_client.py:71-76, 454 | module `_rate_limiter` (`literature._rate_limiter.RateLimiter._last_call`) | `None` / timestamp | `wait_sync` once per `_post_with_retry` (454), not per retry | none | `threading.Lock` inside limiter | nobody | yes | C | none |
| LL-17 | berb/llm/deep_query_client.py:348-390 (consumer pipeline/citation_verification.py:566-567) | `verify_citation` result `status` | `"verified"`, `"inaccurate"`, `"unverified"` | derived 378-384 from `"VERIFIED" in content` | returned to caller | none | agent / user (citation report) | yes | A | `content = result.content.upper()` then `"VERIFIED" in content and "INACCURATE" not in content` (379) is true for the model answer "UNVERIFIED", so an unverified citation is returned as `"verified"`. |
| LL-18 | berb/llm/deep_query_client.py:571-667 | `DeepMindAIClient._client` (`httpx.AsyncClient` built in `__init__` 603-609) | open, closed (`aclose`) | closed in `finally` 666-667 after every `chat` | none | async | nobody (no non-test caller; deepmind_client.py is a parked re-export) | module wired, class has no production caller | A | `chat()` closes the shared `AsyncClient` in `finally` (667), so the second `chat`/`analyze_full_paper`/`synthesize_papers` call on the same instance raises "client has been closed" (latent: no production caller). |
| LL-19 | berb/llm/deep_query_client.py:424-446 vs cost_tracker.py:306-319 | second module-global ledger `berb.metrics.reasoning_cost_tracker.get_cost_tracker` | event list | `tracker.track` 435 | memory | n/a (metrics cluster) | user | yes | B | Perplexity spend goes to a different tracker than `llm.cost_tracker`, so `cost_report.json` (runner.py:534) and `BudgetGovernor` never include DeepQuery spend. |
| LL-20 | berb/llm/anthropic_adapter.py:56-65, 214-217 | `AnthropicAdapter._client` (`httpx.Client`) | `None`, open | lazy open 216; `close()` 58-65 | none | none | nobody | yes | A | `close()` ("prevent fd leaks") has no caller and `LLMClient` has no `close()`, so the pool of every per-stage client is left to GC (unverified impact). |
| LL-21 | berb/llm/anthropic_adapter.py:25-30, 182-183 | `_STOP_REASON_MAP` stop_reason to finish_reason | `"end_turn"`, `"max_tokens"`, `"stop_sequence"`, `"tool_use"` to `"stop"`, `"length"`, `"tool_calls"`; default `"stop"` | `.get(raw_stop_reason, "stop")` 183 | in `LLMResponse.finish_reason` | none | agent | yes | B | Any other stop_reason (e.g. a refusal) maps to `"stop"` and `truncated` is only set for `"length"` (client.py:1161), so a refused/cut-off generation reads as a normal completion (unverified which values the API returns for the configured models). |
| LL-22 | berb/llm/acp_client.py:73, 155-187, 215-267, 306-378 | `ACPClient._session_ready` + external acpx session `"berb"` | `False`, `True` | set True 266; `close()` 155-180 sets False 180; `_force_reconnect` 372-378; `__del__` 182-187 | external acpx session (by name) | none; reconnect loop max 2 (294) | developer | yes (provider `acp`) | A | `__del__` calls `close()` which closes the shared named session; a new client per stage (executor.py:201) means the previous client's GC closes session `"berb"`, breaking the documented "single persistent session across all 23 stages" (lines 6-8) and risking a close of the session the new client has marked `_session_ready=True` (recovered only by the 2-attempt reconnect, 361-368); unverified (depends on when `adapters.llm` drops the old client). Also `ACPClient.chat` has no `stage` parameter and records no tokens/cost (LLMResponse tokens 0, 130-134). |
| LL-23 | berb/llm/acp_client.py:67-79, 190-199 | class attrs `_live_instances`, `_atexit_registered` | list of weakrefs; bool | append 76; register 78-79; clear 199 | none | none | nobody | yes | C | none |
| LL-24 | berb/llm/cross_model.py:98-111, 218-222, 232-251; pipeline/stage_impls/_export.py:229-290 | enable gate (two bools), local `spent_usd`, `CrossModelVerdict` | `"agrees"`, `"disagrees"`, `"uncertain"`; unverified finding on any failure | ceiling check _export.py:236; accumulate 290; parse 292-301 | `cross_model_findings.json` (_export.py:1377) | none | user (paper disclosure, findings) | yes, behind two config flags (default off) | C | none: fails closed on missing config or budget <= 0 (cross_model.py:109-110); documented best-effort `$0` for unpriced models (_export.py:202-206, same cause as LL-8). |
| LL-25 | berb/llm/openrouter_adapter.py:182-433 | `OpenRouterProvider._client` (`httpx.AsyncClient`) | open, closed (`close` 422-424) | open 224; `with_variant` builds a second one 414-420 | none | async | nobody (no construction outside the file) | module reachable via `berb.llm.__all__`; no pipeline caller | C | none (`with_variant` opens a client that is never closed unless the caller does; no caller, unverified). |
| LL-26 | berb/llm/client.py:983-1009 | MetaClaw primary-to-`fallback_url` failover per call | primary, fallback | `except (URLError, OSError)` 986-1007 | none | none | developer (warning log) | yes (bridge enabled) | C | none: no health memory, each call retries the proxy first. |
| LL-27 | berb/llm/output_limits.py:21-61, 69-101, 107-137 | `Stage` IntEnum (second copy of pipeline stage identity) | 23 names, values 1-23 | lookup 125-134 | none | none | developer | yes (client.py:659-663) | B | none now: I diffed it against `berb.pipeline.stages.Stage` with python, names and numbers are identical; a second copy can drift (unknown `stage` silently gets `DEFAULT_TOKEN_LIMIT` 4000, 129/134). |
| LL-D1 | berb/llm/batch_api.py:43-62, 206-279 | `BatchStatus`, `BatchPriority` enums, `job.status` | `PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED`, `CANCELLED` | 206, 208, 214, 279 | memory | n/a | nobody | parked (.reachability-allowlist:139) | D | none |
| LL-D2 | berb/llm/speculative_gen.py:39 | `SpeculativeOutcome` | StrEnum | n/a | n/a | n/a | nobody | parked (allowlist:140) | D | none |
| LL-D3 | berb/llm/speculative_router.py:39 | `SpeculativeOutcome` (duplicate of D2) | StrEnum | n/a | n/a | n/a | nobody | parked (allowlist:114) | D | none |
| LL-D4 | berb/llm/adaptive_temp.py:37, 142, 227 | `RetryStage` StrEnum, `_retry_counts` histogram | n/a | 227 | memory | n/a | nobody | parked (allowlist:143) | D | none |
| LL-D5 | berb/llm/structured_outputs.py | none found (grep for state words empty) | n/a | n/a | n/a | n/a | nobody | parked (allowlist:142) | D | none |
| LL-D6 | berb/llm/eval_dataset.py:233 | dataset record key `"stage"` | n/a | n/a | n/a | n/a | nobody | parked (allowlist:141) | D | none |

## Seed verification

- IN-3 `llm/client.py:304-412, 764-863`: **CONFIRMED, with corrections.** Breaker is `client.py:304-423` (not module global: per `LLMClient`, which is per stage execution, so W3's "reset module-global breaker state per run" does not apply to it, only to LL-15). "Shared breaker across fallback chain": CONFIRMED (767-777, one breaker for all models; LL-1). "Final status lost": CONFIRMED for the retry-exhausted path only (863-865 raises without `from`; LL-2). Extra finding: half_open admits all callers (383-384) and `CircuitBreakerOpenError` is not retried or distinguished (343-346).
- IN-4 `llm/client.py:1277`: **CONFIRMED**, upgrade C/A to A (LL-4); `_current_provider_idx` read only at 1436, never written after init.
- IN-5 `llm/model_cascade.py:182-247`: **CONFIRMED** at 220/224-226 (LL-9). Rung index is a loop local, not held state.
- IN-6 `llm/cost_tracker.py:132-317`: **PARTLY WRONG.** "Events dropped silently after close": `get_cost_tracker()` replaces a closed singleton (317) and the choke point re-fetches every call (client.py:1060), so no live drop (LL-6). The real defect is the opposite: no `close()`/`reset()` caller, so state leaks across runs (LL-5). "No budget state": true, no budget lives in the tracker; the budget gate is `BudgetGovernor` in experiment/search (reads `total_usd`). New related defect LL-8 (unknown price = $0).
- IN-7 `llm/nadirclaw_router.py:490-595`: **PARTLY.** Unlocked dual-dict mutation CONFIRMED at 581-611 (LL-12), real line range is 486-491 and 581-611. Concurrency sharing unverified. Additional finding LL-11 (`"mid"` tier dead).
- IN-2 (llm half, `deep_query_client` breaker is "same shape as semantic_scholar", line 79): **CONFIRMED** (LL-15): stuck `half_open` on non-429 failure, never reset per run.
- W3 rule-of-three: three breakers in scope within llm alone (LL-1 count-based, LL-15 429-based, plus literature ones); their transition semantics differ (LL-1 trips on any exception, LL-15 only on 429), so a shared class needs a policy parameter.

## Census mapping

S1 rows
- batch_api.py:206 -> LL-D1; :208 -> LL-D1; :214 -> LL-D1; :279 -> LL-D1
- client.py:378 -> LL-1; :394 -> LL-1; :409 -> LL-1; :412 -> LL-1; :419 -> LL-1 (`get_status` dict key, no callers)
- deep_query_client.py:387 -> LL-17
- eval_dataset.py:233 -> LL-D6
- nadirclaw_router.py:253 -> dismissed: `ContextOptimizer.mode` ("off"/"safe"/"aggressive") is an immutable constructor option, never reassigned

S2 rows
- cost_tracker.py:289 -> LL-6

S3 rows
- anthropic_adapter.py:163 -> dismissed: stateless error-payload shape check (response parse)
- client.py:105 -> dismissed: provider-prefix lookup, stateless

S4 rows
- acp_client.py:517 -> dismissed: message role literal, stateless prompt formatting
- adaptive_temp.py:37 -> LL-D4
- anthropic_adapter.py:163 -> dismissed (as S3); anthropic_adapter.py:90 -> dismissed: message role literal
- batch_api.py:43 -> LL-D1; :53 -> LL-D1
- client.py:105 -> dismissed (as S3); client.py:1090 -> dismissed: role literal; client.py:956 -> dismissed: role literal
- client.py:1342 -> dismissed: provider-name branch building the chain, no state
- client.py:47 -> dismissed: static provider taxonomy, no transitions (LLMProvider)
- client.py:542 -> dismissed: provider-name branch, no state
- cross_model.py:218 -> LL-24
- nadirclaw_router.py:330 -> dismissed: role literal; :342 -> dismissed: role literal
- nadirclaw_router.py:526 -> LL-11
- openrouter_adapter.py:81 -> dismissed: `ModelVariant` is a static model-id suffix enum used by `apply()`, no transitions
- output_limits.py:21 -> LL-27
- speculative_gen.py:39 -> LL-D2; speculative_router.py:39 -> LL-D3

S5 rows
- cost_tracker.py:315 -> LL-5
- deep_query_client.py:100 -> LL-15; :101 -> LL-15; :112 -> LL-15; :132 -> LL-15; :143 -> LL-15; :144 -> LL-15

S8 rows
- adaptive_temp.py:227 -> LL-D4
- client.py:378 -> LL-1; :404 -> LL-1; :412 -> LL-1
- client.py:451 -> LL-3
- deep_query_client.py:146 -> LL-15; :149 -> LL-15; :161 -> LL-15; :163 -> LL-15
- deep_query_client.py:76 -> LL-16

Census rows: 52 data rows, 52 mapped, 0 unmapped (13 dismissed with reason).
Machines the census missed (found by reading): LL-2, LL-4, LL-7, LL-8, LL-9, LL-10, LL-11 (partly census), LL-12, LL-13, LL-14, LL-18, LL-19, LL-20, LL-21, LL-22, LL-23, LL-25, LL-26.

## Module coverage

Wired (from tasks/baseline/wired_modules.txt):
- berb.llm (`__init__`) — LL-14 (factory), LL-9 wiring at 206-234; `PROVIDER_PRESETS` static dict (source of the LL-8 unpriced default)
- berb.llm.acp_client — LL-22, LL-23
- berb.llm.anthropic_adapter — LL-20, LL-21
- berb.llm.client — LL-1, LL-2, LL-3, LL-4, LL-26
- berb.llm.cost_tracker — LL-5, LL-6, LL-7
- berb.llm.cross_model — LL-24
- berb.llm.deep_query_client — LL-15, LL-16, LL-17, LL-18, LL-19
- berb.llm.model_cascade — LL-9, LL-10
- berb.llm.nadirclaw_router — LL-11, LL-12
- berb.llm.openrouter_adapter — LL-25
- berb.llm.openrouter_models_data — none: static generated catalogue data (4430 lines), no mutable state
- berb.llm.output_limits — LL-27
- berb.llm.presets — none: static preset dicts and lookup functions
- berb.llm.pricing — LL-8 (otherwise static table)
- berb.llm.prompt_cache — none: stateless helpers (the old in-process cache was deleted, file header 11-15)
- berb.llm.registry — none: frozen task-profile tables and pure resolution functions
- berb.llm.smart_client — LL-11, LL-13
- berb.llm.vision — none: stateless encoding and a read-only catalogue lookup (`model_supports_vision` returns True/False/None, fails open for None)

Parked (class D, one line each):
- berb.llm.batch_api — LL-D1
- berb.llm.speculative_gen — LL-D2
- berb.llm.speculative_router — LL-D3
- berb.llm.adaptive_temp — LL-D4
- berb.llm.structured_outputs — LL-D5
- berb.llm.eval_dataset — LL-D6
- berb.llm.deepmind_client — none: parked 19-line re-export of LL-18 (allowlist:116)

## Unread / uncertain

- `presets.py`, `registry.py`, `vision.py`, `openrouter_models_data.py`, `structured_outputs.py`, `eval_dataset.py`, `speculative_*`, `adaptive_temp.py`, `batch_api.py`: grep-skimmed only (state words, globals, caches). A hidden module-level cache in those would be missed.
- `cross_model.py` lines 1-80 not read.
- `review/ensemble.py:358` reaches `getattr(self._llm_client, "_anthropic", None)`; when the client is a `SmartLLMClient` or `CascadingLLMClient` wrapper that attribute is absent and Anthropic batching is silently skipped. Belongs to the review cluster (IN-11); not traced.
- LL-5 server-mode claim rests on `server/routes/pipeline.py:115-121` calling `execute_pipeline` in-process and on a grep finding no `close()`/`reset()` caller; whether the server resets the tracker through another path was not traced.
- LL-12 and LL-22 depend on thread sharing / object lifetime that was not traced; LL-13, LL-20, LL-21 impact is unverified.
- Free-text `LLMResponse.finish_reason` consumers (stage impls that branch on `"length"`/`truncated`) not traced.
