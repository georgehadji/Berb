# Objects index

One line per noun: `name` — owner — universe — status. `pipeline-core` and `llm` are verified (cards in their folders); other clusters are stubs whose universe comes from root `CLAUDE.md` and `.reachability-allowlist`, unverified against source.

## pipeline-core
Cards verified 2026-10-22 @ f2b4be7.
- [[stage]] `Stage` enum, status, gate/rollback tables — `berb/pipeline/stages.py` — live — verified
- [[runner]] `execute_pipeline` (DAG levels, pivot) — `berb/pipeline/runner.py` — live — verified
- [[executor]] `execute_stage` (I/O validation, gates) — `berb/pipeline/executor.py` — live — verified
- [[stage-impls]] 23 stage functions + registry — `berb/pipeline/stage_impls/`, `registry.py` — live — verified
- [[checkpoint]] checkpoint and heartbeat — `berb/pipeline/checkpoint.py` — live — verified
- [[contract]] `StageContract` / `CONTRACTS` (order and I/O) — `berb/pipeline/contracts.py` — live — verified

## llm
Cards verified 2026-10-22 @ f2b4be7. Two defects found by this audit are fixed (uncommitted): [[model-cascade]] kwarg collision, [[llm-factory]] `preflight` missing on wrappers.
- [[llm-client]] `LLMClient`, `MultiProviderLLMClient` — `berb/llm/client.py` — live — verified
- [[llm-factory]] `create_llm_client` and wrapper order — `berb/llm/__init__.py` — live — verified
- [[smart-client-router]] `SmartLLMClient` + `NadirClawRouter` (only live router) — `berb/llm/smart_client.py`, `nadirclaw_router.py` — live — verified
- [[model-cascade]] `CascadingLLMClient` (off by default) — `berb/llm/model_cascade.py` — live — verified
- [[vision]] image input and capability gate — `berb/llm/vision.py` — live — verified
- [[cost-tracker]] real spend accounting — `berb/llm/cost_tracker.py` — live — verified
- [[public-api]] `berb.llm.__all__` contract — `berb/llm/__init__.py` — live (contract) — verified
- parked (revisit 2026-12-01, strike 1, per `.reachability-allowlist`): `batch_api`, `speculative_gen`, `speculative_router`, `adaptive_temp`, `structured_outputs`, `eval_dataset`, `deepmind_client` — `berb/llm/` — leftover — stub
- `extended_router` — deleted 2026-09-02 — ghost — stub
- not carded: `acp_client`, `deep_query_client`, `anthropic_adapter`, `openrouter_adapter`, `presets`, `registry`, `pricing`, `output_limits`, `prompt_cache`, `cross_model` — stub

## literature
- public API `berb.literature.__all__` — `berb/literature/__init__.py` — live (contract) — stub
- parked: `searxng_client`, `grey_search`, `multimodal_search` — `berb/literature/` — leftover — stub

## experiment
- sandboxes (local, docker, ssh, colab) — `berb/experiment/sandbox.py`, `docker_sandbox.py`, `ssh_sandbox.py`, `colab_sandbox.py` — live — stub
- tree search — `berb/experiment/search/` — live — stub
- `validator` — `berb/experiment/validator.py` — live — stub
- `plot_verdict` — `berb/experiment/plot_verdict.py` — live — stub
- code agent (live seam) — `berb/pipeline/code_agent.py` — live — stub
- experiment repair — `berb/pipeline/experiment_repair.py` — live — stub
- parked: `compute_guard`, `progress`, `evolutionary_search`, `self_correcting`, `harness_template`, `evaluators/` — `berb/experiment/` — leftover — stub
- `react_agent` — `berb/experiment/react_agent.py` — ghost (dead and broken) — stub
- `experiment/code_agent.py` — deleted 2026-09-02 — ghost — stub

## integrity-review
- 5 reviewers + Area Chair ensemble — `berb/review/ensemble.py` — live — stub
- claim manifests, evidence, citation anchors — `berb/integrity/` — live — stub
- `paper_verifier`, `hallucination_detector`, `citation_verification` — `berb/pipeline/` — live — stub
- `integrity/eval/hidden_eval.py` (HCE) — leftover — stub

## config-prompts
- `load_config` and config schema — `berb/config.py` — live — stub
- prompt catalogue — `prompts.default.yaml` — live — stub
- config examples — `configs/`, `config.berb.yaml` — live — stub

## surfaces
- CLI (`berb` entry point) — `berb/cli.py` — live — stub
- server — `berb/server/` — live — stub
- MCP — `berb/mcp/` — live — stub
- dashboard — `berb/dashboard/` — live — stub
- copilot mode — `berb/copilot/` — unverified — stub
- discovery loop (stages 7-15, off by default) — `berb/research/discovery_loop.py`, `berb/pipeline/discovery.py` — live — stub
- iterative loop (stages 16-22) — `berb/pipeline/iterative.py` — live — stub
- bridges: `metaclaw_bridge` live; `mnemo_bridge`, `reasoner_bridge` parked — `berb/` — mixed — stub
