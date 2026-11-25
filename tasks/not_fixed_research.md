# Research: the four items wave 7 left unfixed (2026-11-25)

Scope: the "Not fixed" list in `tasks/todo.md` wave 7. Each section says what
is true today (traced in code), the fix, its cost, and what it does not cover.

## 0. Root finding: the OpenClaw adapter flags have no real backend at all

No entry point can ever hand the pipeline a real adapter.

- `berb run` (`berb/cli.py:361`) and `POST /pipeline/start`
  (`berb/server/routes/pipeline.py:130`) build a bare `AdapterBundle()`, which
  holds only the `Recording*` stubs.
- Only `berb literature` (`cli.py:1000`) calls `create_adapters(config)`, and
  that only swaps in `MCPMessageAdapter` / `MCPWebFetchAdapter`. Those are also
  stubs: they return an id or a fake response and call nothing.
- There is no host-injection path. Nothing outside the package constructs an
  `AdapterBundle` and passes it in.

So every `openclaw_bridge.use_*` flag changes behaviour only between "do
nothing" and "record into an in-process list". This is the RI-12 defect class.
Whatever is decided per adapter below, `cmd_run` and the server route should
call `create_adapters(config)`, so that one factory decides what is real.

## 1. Message and memory adapters (BR-26 remainder)

**Today.** `executor.py:183-190, 368-387` calls `adapters.message.notify(...)`
at stage start and on gate events, and `adapters.memory.append(...)` for stage
and gate transitions. Both land in in-process lists and are dropped at exit.
`notifications.channel` is a required config field, but no code sends to it.
`notifications.on_stage_fail` is parsed (`config.py:1070`) and never read.

**Message: fix (recommended).** Add two real `MessageAdapter`s in
`berb/adapters.py`, selected in `AdapterBundle.from_config` by
`notifications.channel`:

- `console` (the default, and what the example config ships): log subject and
  body through `logging`. No dependencies.
- `webhook`: POST JSON to `notifications.target` with `httpx` (already a
  dependency). Send both `text` (Slack) and `content` (Discord) keys.
  - Short timeout. Never raise into the stage: a notification failure must not
    fail a stage.
  - Run `check_url_ssrf` (`berb/web/_ssrf.py`) on the target.
  - The webhook URL is a secret: keep it out of logs and run artifacts.

Also wire `on_stage_fail` (one `notify` call in the executor's failure path),
and validate `notifications.channel` in `validate_config` against the
implemented set, the way `integrity.mode` is validated now.

Cost: about 60 lines plus tests. Risk: low.

**Memory: fix (recommended: do not build a backend).** The appended records
(`run_id:stage:status`, gate decisions) are what the wave 5 event log
(`berb/pipeline/run_status.py`, `event_log.json`) already persists per run. A
file-backed memory adapter would be a second, weaker copy, and nothing reads
it back. Recommended: retire `use_memory` with the RI-12 pattern (drop the flag
and the call sites; warn "no effect" if a config still sets it).

Alternative: `JsonlMemoryAdapter` writing `run_dir/bridge_memory.jsonl`
(about 20 lines). Build it only if someone names a reader.

## 2. A real web-fetch adapter

**Today.** With `use_web_fetch`, stage 3 calls `adapters.web_fetch.fetch(url)`
on each literature source; wave 7 made the stubs record `unverified`.

**Fix (recommended).** Add `HttpWebFetchAdapter` to `berb/adapters.py`, and
make `from_config` select it when `use_web_fetch` is on. Reuse the
redirect-safe pattern in `berb/literature/full_text.py:374-395`:
`follow_redirects=False`, at most 5 hops, `check_url_ssrf` before every hop.

The SSRF check is mandatory. The sources list can come from the LLM's stage-3
JSON, so model output (or a prompt injection reaching it) can name
`http://169.254.169.254/...` or an intranet host. Other details:

- `HEAD` first; fall back to streamed `GET` (no body read) on 405/501. 10 s
  timeout.
- Return `FetchResponse(fetched=True, status_code=...)`. On a connection
  error, raise, so the stage's existing `except` records `unknown`.

**Status semantics need a decision.** The built-in sources are API endpoints.
A parameterless request to `export.arxiv.org/api/query` answers 200; the
Semantic Scholar search endpoint without `query` answers 400. The current
mapping (only 200/301/302/405 count as `verified`) would mark a healthy S2 as
`unreachable`. Recommended: any answer below 500 except 404/410 means
`reachable`; connection errors, timeouts, 404/410 and 5xx mean `unreachable`.
Rename `verified` to `reachable`: a live endpoint says nothing about the
papers. Nothing downstream reads `"verified"` today.

Delete `MCPWebFetchAdapter` and `MCPMessageAdapter`. They swap one stub for
another, and `mcp.server_enabled` describes Berb *serving* MCP, not consuming
an MCP fetch tool.

Cost: about 50 lines plus `httpx.MockTransport` tests (no network). Residual
risk: the DNS-rebinding window between check and request, the same accepted
trade-off `full_text.py` makes.

## 3. ACP against a real acpx

**Verified against the acpx docs** (`openclaw/acpx` README,
`docs/sessions.md`, `docs/prompting.md`):

- `sessions ensure --name N` is find-or-create.
- `sessions close N` is a soft-close; a later `ensure` creates a *fresh*
  session, so context is lost. This confirms LL-22: the old `__del__` close
  wiped the agent's context every stage.
- `--ttl 0` keeps the queue owner alive indefinitely, so the wave 7 close at
  exit is required.
- A prompt to a missing session exits with code 4.

**Three client defects the docs expose** (`berb/llm/acp_client.py`):

1. **The long-prompt path is unnecessary and unsafe.** `_send_prompt_via_file`
   writes the prompt to a temp file and tells the agent to read it "and follow
   ALL instructions contained in that file". acpx supports `--file -` (stdin)
   natively. Fix: always send the prompt on stdin. This removes the
   argument-length fallback, the temp file, and the extra turn that told the
   agent to treat file content as instructions.
2. **Output parsing is heuristic.** `_extract_response` strips the
   human-readable stream. acpx `--format quiet` prints only the final
   assistant text. Fix: pass it and drop the heuristics.
3. **`--approve-all` is a security decision, not a default.** Every prompt
   runs with every tool permission approved, and prompt text partly derives
   from third-party abstracts and PDFs. This is the concern that got
   `agentic_sandbox` deleted (D-10). Fix: a config field
   (`llm.acp.permission_mode`, defaulting to the narrower mode) with the risk
   documented. This is a product decision.

**Verification plan.** acpx is not installed here; installing it means
downloading the npm package (needs an explicit OK).

- **Offline, runs in CI:** a fake `acpx` script put on `PATH` by the test,
  recording argv and stdin. It asserts the command shapes for ensure, prompt,
  close, exit code 4 and quiet output.
- **Real, opt-in:** an `e2e` test skipped unless `acpx` is on PATH and
  `BERB_ACP_E2E=1`. Two turns in one session; the second must see the first
  (context survives across stages). Then close. Needs agent credentials, so
  it never runs in CI.

Cost: defects 1-2 remove about 40 lines and add about 10, plus the fake-acpx
test. Defect 3 is a config field plus validation.

## 4. Parallel writer that is actually parallel

**Today.** `_write_section` is `async` but calls the synchronous
`self._llm_client.chat(...)` directly (`parallel_writer.py:345`), so
`asyncio.gather` runs the calls one after another on the event loop.
`_verify_coherence` (line 378) does the same, which is harmless (one call).

**Fix.** `await asyncio.to_thread(self._llm_client.chat, messages=...,
system=...)` at line 345. `LLMClient` is safe for this: its circuit breaker
takes `self._lock`, and `cost_tracker.py` is lock-guarded. `max_parallel=3`
caps concurrent calls (provider rate limits); the RI-16 bounded retry is the
backstop for 429s. Test: a fake client whose `chat` sleeps 0.2 s; three
independent sections must finish in well under 0.6 s.

**Low value on its own.** The writer plans a fixed 7-section structure
whatever the outline says, so it is lower quality than the default sequential
path. Recommended: do the `to_thread` change (cheap, makes the flag mean what
it says); build an outline adapter only if the parallel path is wanted for
real. Keep it behind `BERB_EXPERIMENTAL_PARALLEL_WRITER` until then.

## Recommended order

| # | Change | Size |
|---|--------|------|
| 1 | `cmd_run` and server use `create_adapters(config)` | XS |
| 2 | `HttpWebFetchAdapter` with SSRF checks and `reachable` semantics; delete MCP stubs | S-M |
| 3 | ACP: `--file -` on stdin, `--format quiet`; fake-acpx contract test | S |
| 4 | Console and webhook `MessageAdapter`, `on_stage_fail`, validate `channel` | M |
| 5 | Retire `use_memory` (warn "no effect") | XS |
| 6 | Parallel writer `to_thread` | XS |
| 7 | Opt-in real-acpx e2e test | S (needs acpx installed and agent credentials) |

Decisions needed before building:
- ACP permission mode (section 3, defect 3).
- Retire `use_memory` or back it with a file (section 1).
- `reachable` status semantics (section 2).
