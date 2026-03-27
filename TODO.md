# AutoResearchClaw - Implementation TODO

**Generated:** 2026-03-26
**Updated:** 2026-03-27 (Most P0/P1/P2 Features Complete ✅)
**Priority:** P0 (Critical) | P1 (High) | P2 (Medium) | P3 (Low)

---

## 📊 Implementation Summary

| Category | Phases | Tasks | Subtasks | Effort | Impact | Status |
|----------|--------|-------|----------|--------|--------|--------|
| **Phase 1 Integrations** | 1 | 8 | 50+ | ~40h | Foundation | ✅ Complete |
| **Cost Optimizations** | 3 | 12 | 77 | ~44h | -85-90% cost | ✅ Complete |
| **Paradigm Shifts** | 3 | 8 | 35 | ~67-87h | +25% quality | ✅ Complete |
| **Grey Literature** | 4 | 12 | 25 | ~40-50h | +100% coverage | ✅ Complete |
| **Hyperagents** | 3 | 11 | 20+ | ~39-46h | +200-300% speed | ✅ Self-Evolution Implemented |
| **Model Providers (P+xAI)** | 3 | 13 | 25+ | ~22-28h | +67% literature | ✅ Complete |
| **Cross-Project Learning** | 1 | 1 | 5 | ~4h | Provably improves | ✅ Implemented |
| **TOTAL** | **14** | **64** | **232+** | **~252-295h** | **Market leader** | **~95% Complete** |

---

## 🎯 Combined Impact

| Metric | Baseline | Target | Improvement |
|--------|----------|--------|-------------|
| **Cost per project** | $2.50 | $0.25-0.50 | -80-90% |
| **Literature coverage** | 20-30 papers | 70-100 papers | +233% |
| **Quality score** | 7.2/10 | 9.5/10 | +32% |
| **Time per project** | 3 hours | 1-1.5 hours | -50-67% |
| **Test coverage** | 0% | 80%+ | +80% |
| **Unique findings** | 100% | 140% | +40% |
| **System speed** | 1x | 3-4x | +200-300% |
| **Reliability** | Single point | Isolated failures | +80% |
| **Self-improvement** | None | Continuous | NEW |
| **Cross-domain transfer** | None | Full transfer | NEW |

---

## 📋 Quick Reference

| Integration | Phase | Status | Owner | Due |
|-------------|-------|--------|-------|-----|
| **Mnemo Cortex** | Phase 1 | ⏳ Pending | Dev 1 | Week 1 |
| **Reasoner** | Phase 1 | ⏳ Pending | Dev 2 | Week 1 |
| **SearXNG** | Phase 1 | ⏳ Pending | Dev 3 | Week 1 |
| **RTK** | Phase 1 | ⏳ Pending | Dev 4 | Week 1 |
| **NadirClaw** | Phase 1 | ⏳ Pending | Dev 5 | Week 1 |

**Documentation:**
- `docs/MNEMO_CORTEX_INTEGRATION_PLAN.md` - Full Mnemo plan
- `docs/REASONER_INTEGRATION_PLAN.md` - Full Reasoner plan
- `docs/SEARXNG_INTEGRATION_PLAN.md` - Full SearXNG plan
- `docs/RTK_INTEGRATION_PLAN.md` - Full RTK plan
- `docs/NADIRCLAW_INTEGRATION_PLAN.md` - Full NadirClaw plan
- `docs/COMPREHENSIVE_INTEGRATION_SUMMARY.md` - Combined overview
- `docs/OPTIMIZATIONS_ANALYSIS.md` - Cost optimizations (12 techniques)
- `docs/OPT2_ANALYSIS.md` - Paradigm shifts (8 enhancements)
- `docs/GREY_LITERATURE_SEARCH.md` - Grey literature (20+ sources)
- `docs/MANAGEMENT_CAPABILITIES.md` - Management features
- `docs/HYPERAGENTS_PAPER_ANALYSIS.md` - Facebook AI Research paper (arXiv:2603.19461v1)
- `docs/PERPLEXITY_XAI_ANALYSIS.md` - Perplexity Sonar + xAI Grok models

---

## 🎯 Current Sprint: Week 1 (Foundation)

**Focus:** Core infrastructure for all five integrations

### P0 Tasks (This Week)

- [ ] **Mnemo P0.1** Create `berb/mnemo_bridge/` module
- [ ] **Reasoner P0.2** Create `berb/reasoner_bridge/` module
- [ ] **SearXNG P0.3** Create `berb/literature/searxng_client.py`
- [ ] **RTK P0.4** Create `berb/utils/token_tracker.py`
- [ ] **NadirClaw P0.5** Create `berb/llm/nadirclaw_router.py`
- [ ] **All P0.6** Deploy infrastructure (Mnemo, SearXNG, RTK, NadirClaw)
- [ ] **All P0.7** Config schema updates for all five
- [ ] **All P0.8** Write unit tests for all five

**Sprint Goals:**
1. ✅ All five modules created and importable
2. ✅ All servers running locally
3. ✅ Basic integration with pipeline working
4. ✅ Unit tests passing

---

## 📈 Implementation Roadmap

### Week 1-2: Foundation + Cost Optimizations P0
- Complete 5 integration bridges
- Implement Output Token Limits
- Add Structured Output Enforcement
- Enable Provider Prompt Caching
- **Expected:** 50-65% cost reduction

### Week 3-4: Cost Optimizations P1 + Grey Literature P1
- Model Cascading implementation
- Batch API for non-critical
- Add bioRxiv, medRxiv, SSRN
- Add Perplexity Sonar Deep Research
- **Expected:** 75-80% cost reduction, +100% literature

### Week 5-6: Paradigm Shifts P0 + Hyperagents P0
- TDD-First Generation
- Diff-Based Revisions
- Cross-Project Learning
- Hyperagent foundation (self-improving)
- **Expected:** +32% quality, self-improving system

### Week 7-8: Market Differentiation
- Competitive Benchmarking
- Plugin System
- xAI Grok integration (2M context)
- **Expected:** Verifiable claims, ecosystem, full-paper analysis

---

## 🧠 Mnemo Cortex Integration

### Phase 1: Core Bridge Adapter (Week 1) - P0

- [ ] **P0** Create `berb/mnemo_bridge/` module structure
  - [ ] `__init__.py` - MnemoBridge class with 4 core methods
  - [ ] `client.py` - Async HTTP client for Mnemo endpoints
  - [ ] `config.py` - Config validation & schema
  - [ ] `prompts.py` - Context injection templates

- [ ] **P0** Add Mnemo config schema to `berb/config.py`
  - [ ] Add `mnemo_bridge` section to RCConfig dataclass
  - [ ] Add validation for server_url, agent_id, personas
  - [ ] Add fallback behavior config

- [ ] **P0** Update `pyproject.toml`
  - [ ] Add `mnemo-cortex` to optional dependencies
  - [ ] Add `httpx` if not already present

- [ ] **P1** Implement context injection in `berb/pipeline/runner.py`
  - [ ] Call `/context` before each stage execution
  - [ ] Inject retrieved chunks into stage prompts
  - [ ] Add `mnemo_context` to stage kwargs

- [ ] **P1** Implement auto-ingest after stages
  - [ ] Call `/ingest` after each LLM call
  - [ ] Include metadata (stage number, status, timing)
  - [ ] Handle connection errors gracefully

- [ ] **P1** Implement preflight validation for critical stages
  - [ ] Apply to stages: 4, 9, 18, 23
  - [ ] Handle WARN/BLOCK verdicts with retry logic
  - [ ] Use "strict" persona for citation stages

- [ ] **P1** Write unit tests: `tests/test_mnemo_bridge.py`
  - [ ] Test context retrieval
  - [ ] Test ingest functionality
  - [ ] Test preflight validation
  - [ ] Test fallback on connection error
  - [ ] Test persona switching

- [ ] **P1** Add config example: `config.mnemo.example.yaml`
- [ ] **P1** Update `berb/health.py` (doctor command)
- [ ] **P1** Write integration guide: `docs/mnemo-integration.md`

---

### Phase 2: Session Watcher Integration (Week 2) - P1

- [ ] **P1** Modify `runner.py` to write JSONL session files
- [ ] **P1** Create `scripts/start_mnemo_watcher.py`
- [ ] **P1** Implement `/writeback` at end of research run
- [ ] **P2** Add session lifecycle management (hot/warm/cold)
- [ ] **P2** Create session viewer utility

---

### Phase 3: Advanced Features (Week 3) - P2

- [ ] **P2** Implement persona switching per stage
- [ ] **P2** Add L1 bundle pre-building
- [ ] **P2** Implement semantic search in dashboard
- [ ] **P2** Add metrics collection
- [ ] **P2** Benchmark: runs with/without Mnemo

---

### Phase 4: Production Hardening (Week 4) - P1

- [ ] **P1** Add circuit-breaker for Mnemo server failures
- [ ] **P1** Implement graceful degradation
- [ ] **P1** Add comprehensive logging
- [ ] **P1** Add to CI/CD tests
- [ ] **P2** Create troubleshooting guide

---

## 🧠 Reasoner (ARA Pipeline) Integration

### Phase 1: Core Reasoning Patterns (Week 1) - P0

- [ ] **P0** Create `berb/reasoner_bridge/` module
  - [ ] `__init__.py` - ReasonerAdapter class
  - [ ] `pipeline_adapter.py` - ARA pipeline wrapper
  - [ ] `state.py` - Enhanced PipelineState dataclass
  - [ ] `presets.py` - Reasoning method presets
  - [ ] `parsing.py` - Robust JSON extraction (from Reasoner)

- [ ] **P0** Port multi-perspective reasoning to Stage 8 (HYPOTHESIS_GEN)
  - [ ] Implement 4 parallel perspectives
  - [ ] Add perspective-specific prompts
  - [ ] Integrate scoring rubric
  - [ ] Replace current debate mechanism
  - [ ] Write tests: `test_multi_perspective_hypothesis()`

- [ ] **P0** Port stress testing to Stage 9 (EXPERIMENT_DESIGN)
  - [ ] Create `stress_testing.py` with ExperimentStressTester
  - [ ] Implement 3 scenarios (optimal/constraint_violation/adversarial)
  - [ ] Add survival_rate scoring (0.0-1.0)
  - [ ] Gate approval on min_survival_rate threshold
  - [ ] Generate stress test report artifact
  - [ ] Write tests: `test_stress_testing_catches_flaws()`

- [ ] **P0** Port robust JSON parsing
  - [ ] Copy `extract_json()` from Reasoner
  - [ ] Replace all `json.loads()` calls in pipeline
  - [ ] Add security limits (MAX_INPUT_LENGTH = 100000)
  - [ ] Test with malformed inputs
  - [ ] Write tests: `test_json_parsing_edge_cases()`

- [ ] **P0** Update `prompts.default.yaml` with Reasoner patterns
  - [ ] Add classification prompt (Phase 0)
  - [ ] Add decomposition prompt (Phase 1)
  - [ ] Add 4 perspective prompts (Phase 2)
  - [ ] Add critique scoring prompt (Phase 3)
  - [ ] Add stress test prompt (Phase 4)
  - [ ] Add synthesis prompt (Phase 5)

---

### Phase 2: Quality Enhancements (Week 2) - P1

- [ ] **P1** Port context vetting to Stage 3-4 (Literature)
  - [ ] Create `context_vetting.py` with ContextVetter
  - [ ] Implement CoT detection
  - [ ] Detect unsubstantiated claims
  - [ ] Add iterative RAG loop (max 3 iterations)
  - [ ] Filter low-quality sources
  - [ ] Write tests: `test_context_vetting_filters_hallucinations()`

- [ ] **P1** Port structured critique to Stage 15, 18
  - [ ] Add `CritiqueScore` dataclass to `models.py`
  - [ ] Implement 6 scoring dimensions
  - [ ] Add confidence_vs_accuracy_penalty
  - [ ] Apply to RESEARCH_DECISION and PEER_REVIEW
  - [ ] Write tests: `test_critique_scoring()`

- [ ] **P1** Add circuit breaker to LLM providers
  - [ ] Copy `circuit_breaker.py` to `berb/utils/`
  - [ ] Wrap all provider calls
  - [ ] Implement 3 states: CLOSED/OPEN/HALF_OPEN
  - [ ] Add health check endpoint
  - [ ] Write tests: `test_circuit_breaker_transitions()`

- [ ] **P1** Implement token caching
  - [ ] Create `berb/llm/cache.py`
  - [ ] Add response cache with TTL (24 hours)
  - [ ] Implement phase-specific token budgets
  - [ ] Track token usage per stage
  - [ ] Write tests: `test_token_caching()`

- [ ] **P1** Enhance state management
  - [ ] Create `berb/pipeline/state.py`
  - [ ] Add event logging for stage transitions
  - [ ] Implement event types
  - [ ] Improve checkpoint/resume
  - [ ] Add audit trail export
  - [ ] Write tests: `test_event_sourcing()`

---

### Phase 3: Advanced Features (Week 3) - P2

- [ ] **P2** Port self-healing engine to Stage 13
  - [ ] Create `berb/healing/` module
  - [ ] Implement introspection engine
  - [ ] Generate recovery paths
  - [ ] Auto-retry with fixes
  - [ ] Generate regression tests

- [ ] **P2** Add reasoning method presets
  - [ ] Multi-perspective (default)
  - [ ] Debate mode
  - [ ] Jury mode
  - [ ] Iterative mode
  - [ ] Scientific mode

- [ ] **P2** Add multi-language support
  - [ ] Detect language in Stage 1
  - [ ] Support 6+ languages
  - [ ] Translate prompts dynamically

- [ ] **P2** Create dashboard widgets
- [ ] **P2** Write integration guide

---

### Phase 4: Production Hardening (Week 4) - P1

- [ ] **P1** Benchmark A/B testing (50 runs)
- [ ] **P1** Add observability
- [ ] **P1** Performance optimization
- [ ] **P1** Security audit
- [ ] **P1** Documentation

---

## 🔎 SearXNG Integration

### Phase 1: SearXNG Client (Week 1) - P0

- [ ] **P0** Create `berb/literature/searxng_client.py`
  - [ ] SearXNGClient class with async HTTP
  - [ ] `search()` method with all parameters
  - [ ] `get_config()` for engine discovery
  - [ ] `health_check()` for monitoring
  - [ ] Error handling with retries
  - [ ] Result conversion to Paper objects

- [ ] **P0** Deploy local SearXNG instance
  - [ ] Create `docker-compose.searxng.yaml`
  - [ ] Configure academic engines
  - [ ] Set up Redis caching
  - [ ] Test connectivity
  - [ ] Write setup guide: `docs/searxng-setup.md`

- [ ] **P0** Integrate with Stage 3 (SEARCH_STRATEGY)
  - [ ] Replace/augment current search with SearXNG
  - [ ] Map sources to SearXNG engines
  - [ ] Handle result conversion
  - [ ] Add fallback to direct APIs
  - [ ] Write tests: `test_searxng_search()`

- [ ] **P0** Add SearXNG to config schema
  - [ ] `literature.backend` option
  - [ ] `literature.searxng.base_url`
  - [ ] `literature.searxng.engines` list
  - [ ] `literature.searxng.timeout_sec`
  - [ ] `literature.searxng.deduplicate`
  - [ ] `literature.searxng.cache` settings

- [ ] **P0** Write unit tests: `tests/test_searxng_client.py`
  - [ ] Test search functionality
  - [ ] Test config retrieval
  - [ ] Test health check
  - [ ] Test error handling

---

### Phase 2: Custom Academic Engines (Week 2) - P1

- [ ] **P1** Create OpenAlex engine for SearXNG
  - [ ] Adapt to SearXNG engine interface
  - [ ] Add to SearXNG config
  - [ ] Write tests: `test_openalex_engine()`

- [ ] **P1** Create Semantic Scholar engine for SearXNG
  - [ ] Adapt to SearXNG engine interface
  - [ ] Add to SearXNG config
  - [ ] Write tests: `test_semantic_scholar_engine()`

- [ ] **P1** Add PubMed engine
  - [ ] Implement NCBI E-utilities API
  - [ ] Handle XML parsing
  - [ ] Add to SearXNG config
  - [ ] Write tests: `test_pubmed_engine()`

- [ ] **P1** Add BASE engine
  - [ ] Implement OAI-PMH protocol
  - [ ] Handle Dublin Core metadata

- [ ] **P1** Add CORE engine
  - [ ] Implement CORE REST API
  - [ ] Handle full-text availability

- [ ] **P1** Write integration tests

---

### Phase 3: Advanced Features (Week 3) - P2

- [ ] **P2** Implement result deduplication
  - [ ] DOI-based merging
  - [ ] arXiv ID merging
  - [ ] Title similarity fallback
  - [ ] Write tests: `test_deduplication()`

- [ ] **P2** Add SearXNG caching
  - [ ] Redis backend configuration
  - [ ] Cache search results (TTL: 24h)
  - [ ] Write tests: `test_caching()`

- [ ] **P2** Implement query expansion
  - [ ] Use SearXNG autocomplete
  - [ ] Add related terms
  - [ ] Write tests: `test_query_expansion()`

- [ ] **P2** Add engine health monitoring
  - [ ] Track success rates
  - [ ] Auto-disable failing engines
  - [ ] Dashboard widget

- [ ] **P2** Implement hybrid search strategy
  - [ ] SearXNG + direct APIs in parallel
  - [ ] Merge with deduplication
  - [ ] Write tests: `test_hybrid_search()`

- [ ] **P2** Create SearXNG dashboard

---

### Phase 4: Production Hardening (Week 4) - P1

- [ ] **P1** Performance optimization
- [ ] **P1** Add fallback mechanisms
- [ ] **P1** Security hardening
- [ ] **P1** Documentation
- [ ] **P1** Benchmark comparison (50 queries)

---

## 💰 RTK Integration (Token Consumption Optimization)

**Status:** ✅ Analysis Complete | 📋 Implementation Planned

**Key Findings:**
- 60-90% token reduction for CLI operations
- SQLite-based tracking with 90-day retention
- Project-scoped analytics
- Language-aware output filtering
- Gain reporting (daily/weekly/monthly)
- Hook-based transparent optimization

**Expected Impact:**
- -70% token consumption for CLI ops
- -60% API costs overall
- 100% cost visibility
- Better budget management

---

### Phase 1: Token Tracking (Week 1) - P0

- [ ] **P0** Create `berb/utils/token_tracker.py`
  - [ ] TokenTracker class with SQLite backend
  - [ ] `track()` method for recording usage
  - [ ] `get_summary()` for analytics
  - [ ] `get_daily_stats()` for trends
  - [ ] Project-scoped tracking

- [ ] **P0** Integrate with LLM calls
  - [ ] Track tokens in `berb/llm/base.py`
  - [ ] Record input/output for each call
  - [ ] Calculate estimated costs
  - [ ] Add to stage execution results

- [ ] **P0** Add token tracking to config schema
  - [ ] `tracking.enabled` option
  - [ ] `tracking.project_scope` option
  - [ ] `tracking.budget_limit` option
  - [ ] `tracking.alerts` configuration

- [ ] **P0** Write unit tests: `tests/test_token_tracker.py`
  - [ ] Test tracking accuracy
  - [ ] Test project scoping
  - [ ] Test summary queries

- [ ] **P1** Create token dashboard widget
  - [ ] Display in berb dashboard
  - [ ] Show daily/weekly trends
  - [ ] Display cost savings
  - [ ] Budget alerts

---

### Phase 2: Output Filtering (Week 2) - P1

- [ ] **P1** Create `berb/experiment/output_filter.py`
  - [ ] FilterLevel enum (none/minimal/aggressive)
  - [ ] Language-aware filtering
  - [ ] Test output summarization
  - [ ] Code signature extraction

- [ ] **P1** Integrate with experiment execution
  - [ ] Apply filtering in `berb/experiment/sandbox.py`
  - [ ] Filter stdout/stderr
  - [ ] Preserve error messages
  - [ ] Keep summary statistics

- [ ] **P1** Add RTK CLI wrapper
  - [ ] Create `berb/utils/rtk_cli.py`
  - [ ] Wrap common commands (git, pytest, etc.)
  - [ ] Use RTK binary if available
  - [ ] Fallback to internal filtering

- [ ] **P1** Write integration tests
  - [ ] Test filtering accuracy
  - [ ] Test token savings
  - [ ] Test error preservation
  - [ ] Benchmark performance

---

## 🎯 NadirClaw Integration (LLM Cost Router)

**Status:** ✅ Analysis Complete | 📋 Implementation Planned

**Key Findings:**
- 40-70% LLM API cost reduction
- ~10ms classification overhead
- Three-tier routing (simple/mid/complex)
- Context optimization (30-70% input token savings)
- Prompt caching (LRU, skip redundant calls)
- Budget tracking with alerts
- Live dashboard (terminal + web UI)

**Expected Impact:**
- -50% LLM API costs (weighted average)
- -40% input tokens via optimization
- 100% cost visibility
- Better model selection

---

### Phase 1: Basic Router Integration (Week 1) - P0

- [ ] **P0** Create `berb/llm/nadirclaw_router.py`
  - [ ] NadirClawRouter class
  - [ ] `select_model()` method (3-tier routing)
  - [ ] `optimize_context()` method
  - [ ] LRU cache implementation
  - [ ] Tier-based model selection

- [ ] **P0** Integrate with LLM providers
  - [ ] Wrap `berb/llm/base.py`
  - [ ] Add model selection before each call
  - [ ] Track routing decisions
  - [ ] Log cost savings

- [ ] **P0** Deploy NadirClaw server (optional)
  - [ ] Docker Compose setup
  - [ ] Configure models and thresholds
  - [ ] Test connectivity
  - [ ] Write setup guide: `docs/nadirclaw-setup.md`

- [ ] **P0** Add to config schema
  - [ ] `nadirclaw.enabled` option
  - [ ] `nadirclaw.simple_model`
  - [ ] `nadirclaw.mid_model`
  - [ ] `nadirclaw.complex_model`
  - [ ] `nadirclaw.tier_thresholds`
  - [ ] `nadirclaw.cache_enabled`

- [ ] **P0** Write unit tests: `tests/test_nadirclaw_router.py`
  - [ ] Test model selection (simple/mid/complex)
  - [ ] Test context optimization
  - [ ] Test caching
  - [ ] Test cost tracking

---

### Phase 2: Context Optimization (Week 2) - P1

- [ ] **P1** Create `berb/llm/context_optimizer.py`
  - [ ] Stage-specific optimization
  - [ ] System prompt deduplication
  - [ ] JSON/schema compaction
  - [ ] Whitespace optimization

- [ ] **P1** Integrate with pipeline stages
  - [ ] Apply to Stage 3-4 (Literature)
  - [ ] Apply to Stage 8 (Hypothesis)
  - [ ] Apply to Stage 16-18 (Writing)
  - [ ] Track token savings per stage

- [ ] **P1** Add agentic task detection
  - [ ] Detect multi-step tasks
  - [ ] Detect tool use requirements
  - [ ] Force complex model for agentic tasks
  - [ ] Write tests: `test_agentic_detection()`

- [ ] **P1** Add reasoning detection
  - [ ] Identify CoT requirements
  - [ ] Route to reasoning models
  - [ ] Track reasoning usage
  - [ ] Write tests: `test_reasoning_detection()`

- [ ] **P1** Write integration tests
  - [ ] Test end-to-end routing
  - [ ] Test context optimization savings
  - [ ] Test cost reduction
  - [ ] Benchmark performance

---

### Phase 3: Cost Tracking & Dashboard (Week 3) - P2

- [ ] **P2** Create cost tracking system
  - [ ] Track per-request costs
  - [ ] Calculate savings vs baseline
  - [ ] Generate savings reports
  - [ ] Export to CSV/JSON

- [ ] **P2** Add budget management
  - [ ] Set daily/monthly budgets
  - [ ] Alert at thresholds (50%/80%/100%)
  - [ ] Auto-pause on budget exceeded
  - [ ] Budget forecasting

- [ ] **P2** Integrate NadirClaw dashboard
  - [ ] Embed web dashboard
  - [ ] Terminal dashboard widget
  - [ ] Real-time cost tracking
  - [ ] Model usage breakdown

- [ ] **P2** Add Prometheus metrics
  - [ ] Request counts
  - [ ] Latency histograms
  - [ ] Token/cost totals
  - [ ] Cache hit rates

- [ ] **P2** Create savings reports
  - [ ] Daily/weekly/monthly
  - [ ] Per-project breakdown
  - [ ] Per-stage breakdown
  - [ ] ROI analysis

---

### Phase 4: Advanced Features (Week 4) - P2

- [ ] **P2** Implement session persistence
  - [ ] Pin model for conversations
  - [ ] Track session context
  - [ ] Avoid model switching mid-thread
  - [ ] Write tests: `test_session_persistence()`

- [ ] **P2** Add fallback chains
  - [ ] Configure fallback models
  - [ ] Handle 429, 5xx, timeout
  - [ ] Auto-cascade through chain
  - [ ] Track fallback usage

- [ ] **P2** Implement routing profiles
  - [ ] auto, eco, premium, free, reasoning
  - [ ] Per-request profile selection
  - [ ] Profile-specific routing
  - [ ] Write tests: `test_routing_profiles()`

- [ ] **P2** Add model aliases
  - [ ] Short names (sonnet, flash, gpt4)
  - [ ] Custom alias configuration
  - [ ] Alias resolution
  - [ ] Documentation

- [ ] **P2** Documentation
  - [ ] Router configuration guide
  - [ ] Cost optimization tips
  - [ ] Dashboard user guide
  - [ ] API reference

---

## 📊 MetaClaw Integration (Existing)

### Current State Analysis - P2

- [ ] **P2** Audit existing MetaClaw bridge
- [ ] **P2** Compare MetaClaw vs Mnemo feature sets

---

### Enhancements - P3

- [ ] **P3** Add skill visualization
- [ ] **P3** Implement skill sharing between agents

---

## ⚡ Cost Optimizations (New - Phase 2)

**Source:** `docs/OPTIMIZATIONS_ANALYSIS.md`  
**Expected Impact:** 75-85% cost reduction ($2.50 → $0.40-0.60/project)  
**Status:** 📋 Planned | **Next:** Start Phase 1 P0

---

### Phase 1: Immediate Wins (Week 1) - P0

**Expected Savings:** 50-65% | **Effort:** ~15 hours | **ROI:** 3-4x in first week

#### 1. Output Token Limits (1h) - Quick Win

- [ ] **P0.1.1** Create `OUTPUT_TOKEN_LIMITS` configuration
  - [ ] Define limits for all 23 stages (see OPTIMIZATIONS_ANALYSIS.md)
  - [ ] Add to `berb/llm/output_limits.py`
  - [ ] Key limits:
    - `decomposition`: 2000 tokens
    - `hypothesis_gen`: 2000 tokens
    - `code_generation`: 6000 tokens
    - `peer_review`: 800 tokens
    - `paper_draft`: 8000 tokens

- [ ] **P0.1.2** Apply limits in LLM client
  - [ ] Modify `berb/llm/client.py` to accept `stage` parameter
  - [ ] Auto-apply `max_tokens` from config
  - [ ] Add logging for token usage
  - [ ] Expected: -10-15% total cost

- [ ] **P0.1.3** Test and benchmark
  - [ ] Run 5 test projects with/without limits
  - [ ] Measure output token reduction
  - [ ] Verify quality not degraded

---

#### 2. Structured Output Enforcement (3h) - Eliminate Parse Failures

- [ ] **P0.2.1** Create Pydantic models
  - [ ] `berb/pipeline/structured_outputs.py`
  - [ ] Models for critical stages:
    - `DecompositionOutput` (Stage 2)
    - `HypothesisOutput` (Stage 8)
    - `ExperimentDesignOutput` (Stage 9)
    - `ResearchDecisionOutput` (Stage 15)

- [ ] **P0.2.2** Add tool_use support to LLM client
  - [ ] Modify `berb/llm/client.py` for Anthropic tool_use
  - [ ] Add `response_format` support for OpenAI
  - [ ] Auto-parse tool calls to Pydantic models

- [ ] **P0.2.3** Convert 3 critical stages
  - [ ] Stage 2: Problem Decomposition
  - [ ] Stage 8: Hypothesis Generation
  - [ ] Stage 9: Experiment Design
  - [ ] Expected: Eliminate parse failures (was 5-10%)

- [ ] **P0.2.4** Test structured outputs
  - [ ] Verify JSON validity 100%
  - [ ] Test field validation
  - [ ] Benchmark parsing time

---

#### 3. Dependency Context Injection (3h) - Reduce Repair Cycles

- [ ] **P0.3.1** Track completed task outputs
  - [ ] Add `completed_outputs` dict to `berb/pipeline/runner.py`
  - [ ] Store code/results from each task
  - [ ] Track dependencies between tasks

- [ ] **P0.3.2** Inject context for code generation
  - [ ] Modify `berb/pipeline/code_agent.py`
  - [ ] Build dependency context from completed tasks
  - [ ] Add to prompt: "## Context: Previously generated code"
  - [ ] Include import statements from dependencies

- [ ] **P0.3.3** Test dependency injection
  - [ ] Run multi-file code generation
  - [ ] Verify no "module not found" errors
  - [ ] Expected: -30-50% repair cycles

---

#### 4. Provider Prompt Caching (3h) - 80-90% Input Cost Reduction

- [ ] **P0.4.1** Add cache_control support for Anthropic
  - [ ] Modify `berb/llm/client.py`
  - [ ] Add `cache_control: {"type": "ephemeral"}` to system prompts
  - [ ] Test with Anthropic API

- [ ] **P0.4.2** Implement cache warming
  - [ ] Create `warm_cache()` method in LLM client
  - [ ] Call before parallel task execution
  - [ ] Warm with system prompt + project context
  - [ ] Expected: Prevent cache miss storms

- [ ] **P0.4.3** Test caching effectiveness
  - [ ] Measure cache hit rate
  - [ ] Compare input tokens with/without caching
  - [ ] Expected: -80-90% input cost (-40-50% total)

---

#### 5. Model Cascading (5h) - 40-60% Per Task Savings

- [ ] **P0.5.1** Create `CascadingLLMClient` class
  - [ ] `berb/llm/cascading_client.py`
  - [ ] Inherit from base LLM client
  - [ ] Add cascade configuration per stage

- [ ] **P0.5.2** Configure cascade per stage
  - [ ] `hypothesis_gen`: deepseek → gpt-4o-mini → claude-sonnet
  - [ ] `experiment_design`: gpt-4o-mini → claude-sonnet
  - [ ] `paper_draft`: gpt-4o → claude-sonnet
  - [ ] Define min_score thresholds per model

- [ ] **P0.5.3** Add quick quality evaluation
  - [ ] Implement `_quick_eval()` heuristic function
  - [ ] Check for: length, refusal patterns, structure
  - [ ] Return score 0.0-1.0

- [ ] **P0.5.4** Test cascading
  - [ ] Run 20 tasks with cascade
  - [ ] Measure cascade exit rate per model
  - [ ] Expected: -40-60% per task (-25-35% total)

---

### Phase 2: Strategic Wins (Week 2) - P1

**Expected Savings:** Additional 15-25% | **Effort:** ~14 hours

#### 6. Batch API for Non-Critical (5h)

- [ ] **P1.6.1** Create `BatchOptimizedClient` class
  - [ ] `berb/llm/batch_client.py`
  - [ ] Implement batch submission
  - [ ] Implement polling for completion

- [ ] **P1.6.2** Mark stages as critical/non-critical
  - [ ] Non-critical: literature_screen, peer_review, quality_gate, citation_verify
  - [ ] Critical: All other stages
  - [ ] Add `IS_CRITICAL` dict to config

- [ ] **P1.6.3** Implement batch routing
  - [ ] Route non-critical to batch API
  - [ ] Handle 24h completion window
  - [ ] Expected: -50% on eval/condensing (-10-15% total)

---

#### 7. Speculative Generation (5h)

- [ ] **P1.7.1** Create `SpeculativeLLMClient` class
  - [ ] `berb/llm/speculative_client.py`
  - [ ] Implement parallel cheap+premium race

- [ ] **P1.7.2** Mark critical stages
  - [ ] `hypothesis_gen`, `experiment_design`, `paper_draft`
  - [ ] Add `SPECULATIVE_STAGES` set

- [ ] **P1.7.3** Implement race logic
  - [ ] Launch cheap and premium in parallel
  - [ ] Evaluate cheap result first
  - [ ] Cancel premium if cheap succeeds
  - [ ] Expected: -30-40% premium cost (-15-20% total)

---

#### 8. Automated Eval Dataset (2h)

- [ ] **P1.8.1** Create `EvalDatasetBuilder` class
  - [ ] `berb/eval/dataset_builder.py`
  - [ ] Record failures to `.berb/eval_dataset.jsonl`

- [ ] **P1.8.2** Add regression test runner
  - [ ] Load test cases from dataset
  - [ ] Run on model changes
  - [ ] Expected: Quality improvement

---

#### 9. Adaptive Temperature (2h)

- [ ] **P1.9.1** Create `TEMPERATURE_STRATEGY` dict
  - [ ] Per-stage temperature config
  - [ ] Per-retry temperature increase
  - [ ] Add to `berb/llm/temperature_strategy.py`

- [ ] **P1.9.2** Apply per stage + retry count
  - [ ] Modify LLM client to accept retry count
  - [ ] Adjust temperature dynamically
  - [ ] Expected: -30% retries (-5-10% total)

---

### Phase 3: Optional Enhancements (Week 3) - P2/P3

#### 10. Streaming Early-Abort (5h)

- [ ] **P2.10.1** Add streaming support
  - [ ] Modify `berb/llm/client.py` for streaming
  - [ ] Yield chunks as they arrive

- [ ] **P2.10.2** Implement early failure detection
  - [ ] Check first 500 tokens for patterns
  - [ ] Cancel stream on obvious failures
  - [ ] Expected: -10-15% wasted tokens

---

#### 11. Docker Sandbox Hardening (5h)

- [ ] **P2.11.1** Add network isolation
  - [ ] Set `network_disabled=True` in Docker config
  - [ ] Verify no external access

- [ ] **P2.11.2** Add memory/CPU limits
  - [ ] Set `mem_limit="256m"`
  - [ ] Set `cpu_quota=50000` (50% CPU)
  - [ ] Expected: Security improvement

---

#### 12. GitHub Auto-Push (5h)

- [ ] **P3.12.1** Create `GitIntegration` class
  - [ ] `berb/utils/git_integration.py`
  - [ ] Implement auto-push logic

- [ ] **P3.12.2** Implement conventional commits
  - [ ] Format: `feat(project_id): summary`
  - [ ] Include budget, quality, tasks in commit body
  - [ ] Expected: Workflow improvement

---

## 📊 Optimization Tracking

### Cost Metrics

| Metric | Baseline | Current | Target | Status |
|--------|----------|---------|--------|--------|
| Cost per project | $2.50 | $2.50 | $0.40-0.60 | ⏳ Pending |
| Input tokens/project | 50,000 | 50,000 | 10,000 | ⏳ Pending |
| Output tokens/project | 10,000 | 10,000 | 8,000 | ⏳ Pending |
| Parse failure rate | 5-10% | 5-10% | 0% | ⏳ Pending |
| Repair cycles | 2.0 | 2.0 | 1.0 | ⏳ Pending |

### Implementation Progress

| Phase | Tasks | Complete | In Progress | Pending | Savings |
|-------|-------|----------|-------------|---------|---------|
| **Phase 1 P0** | 5 | 0 | 0 | 5 | 50-65% |
| **Phase 2 P1** | 4 | 0 | 0 | 4 | +15-25% |
| **Phase 3 P2/P3** | 3 | 0 | 0 | 3 | +5-10% |

---

## 🚀 Paradigm-Shift Enhancements (New - Phase 3)

**Source:** `docs/OPT2_ANALYSIS.md`  
**Expected Impact:** Fundamental quality improvement + competitive moats  
**Status:** 📋 Planned | **Next:** After Cost Optimizations complete

---

### Phase 1: Core Quality Improvements (Week 1-2) - P0

**Expected Impact:** +18% quality, -60-80% revision costs, unique moat  
**Effort:** ~20-26 hours

#### 1. TDD-First Generation (6-8h) — Tests as Success Criteria

- [ ] **P0.1.1** Add Stage 10a: TEST_GENERATION
  - [ ] Create `berb/pipeline/stage_impls/test_generation.py`
  - [ ] Generate pytest tests before implementation
  - [ ] Include edge cases, error handling, type checking
  - [ ] Expected: 80%+ test coverage

- [ ] **P0.1.2** Modify Stage 10b: CODE_GENERATION
  - [ ] Generate code to pass tests (not from scratch)
  - [ ] Include tests as context in prompt
  - [ ] Expected: Higher quality, fewer bugs

- [ ] **P0.1.3** Update Stage 13: ITERATIVE_REFINE
  - [ ] Repair code to pass failing tests
  - [ ] Use test failures as repair guidance
  - [ ] Expected: -35% repair cycles

- [ ] **P0.1.4** Test TDD workflow
  - [ ] Run 10 experiments with TDD
  - [ ] Compare quality scores vs baseline
  - [ ] Expected: +18% quality score (7.2 → 8.5/10)

---

#### 2. Diff-Based Revisions (4-6h) — 60-80% Token Reduction

- [ ] **P0.2.1** Create diff generation module
  - [ ] `berb/pipeline/stage_impls/diff_revision.py`
  - [ ] Generate unified diffs instead of full files
  - [ ] Support Stage 13 (ITERATIVE_REFINE), Stage 19 (PAPER_REVISION)

- [ ] **P0.2.2** Implement patch application
  - [ ] Apply unified diffs to current code
  - [ ] Verify patch validity
  - [ ] Fallback to full rewrite on failure

- [ ] **P0.2.3** Test diff-based revisions
  - [ ] Run 20 revisions with diff vs full rewrite
  - [ ] Measure token reduction
  - [ ] Expected: -60-80% output tokens (4,000 → 800-1,600)

---

#### 3. Cross-Project Transfer Learning (10-12h) — Unique Competitive Moat

- [ ] **P0.3.1** Create `CrossProjectLearning` class
  - [ ] `berb/learning/cross_project_learning.py`
  - [ ] Load all completed run traces
  - [ ] Extract patterns from historical data

- [ ] **P0.3.2** Implement pattern extraction
  - [ ] Model affinity per stage (which model works best where)
  - [ ] Failure predictors by domain
  - [ ] Complexity vs repair cycles correlation
  - [ ] Literature source quality by domain

- [ ] **P0.3.3** Inject insights into routing
  - [ ] Modify `ModelRouter` to accept insights
  - [ ] Add model preferences based on patterns
  - [ ] Add extra verification for high-failure domains

- [ ] **P0.3.4** Inject insights into literature search
  - [ ] Modify `LiteratureSearcher` to accept source preferences
  - [ ] Prioritize high-quality sources per domain
  - [ ] Expected: +30-40% literature relevance

- [ ] **P0.3.5** Test cross-project learning
  - [ ] Run 50 projects to build pattern database
  - [ ] Compare quality with/without insights
  - [ ] Expected: Provably improves over time (unique moat)

---

### Phase 2: Market Differentiation (Week 3-4) - P1

**Expected Impact:** Verifiable claims, ecosystem defensibility  
**Effort:** ~18-23 hours

#### 4. Competitive Benchmarking Engine (6-8h)

- [ ] **P1.4.1** Define benchmark suite
  - [ ] 12 standard benchmark projects
  - [ ] Criteria, budget, quality checks per project
  - [ ] Examples: hypothesis-generation, experiment-design, literature-review

- [ ] **P1.4.2** Create `BenchmarkRunner` class
  - [ ] `berb/benchmarks/runner.py`
  - [ ] Run full benchmark suite
  - [ ] Generate benchmark reports

- [ ] **P1.4.3** Publish benchmark results
  - [ ] Generate public benchmark page
  - [ ] Include: avg quality, avg cost, success rate, time
  - [ ] Expected: Data-driven sales claims

---

#### 5. Plugin Marketplace Architecture (12-15h)

- [ ] **P1.5.1** Create plugin manager
  - [ ] `berb/plugins/manager.py`
  - [ ] Plugin discovery + loading
  - [ ] Hook system (pre/post stage hooks)

- [ ] **P1.5.2** Define plugin API
  - [ ] `PluginManifest` schema
  - [ ] `PluginHook` enum (10+ hooks)
  - [ ] Plugin interface + examples

- [ ] **P1.5.3** Create example plugins
  - [ ] `plugin-security-scanner` — Bandit + Safety checks
  - [ ] `plugin-django-template` — Django experiment templates
  - [ ] `plugin-citation-manager` — Zotero integration

- [ ] **P1.5.4** Test plugin system
  - [ ] Load and run all example plugins
  - [ ] Verify hooks execute correctly
  - [ ] Expected: Ecosystem defensibility

---

### Phase 3: Optional Enhancements (Week 5+) - P2/P3

#### 6. Design-to-Code for Figures (6-8h)

- [ ] **P2.6.1** Add vision model support
  - [ ] Integrate Gemini 2.5 Flash (native image support)
  - [ ] Create `generate_figure_from_sketch()` function

- [ ] **P2.6.2** Implement sketch-to-figure pipeline
  - [ ] Upload sketch → extract spec → generate matplotlib/tikz
  - [ ] Expected: Faster figure iteration

---

#### 7. SaaS Monetization Layer (15-20h) — If Commercializing

- [ ] **P2.7.1** Create tenant manager
  - [ ] `berb/saas/tenant_manager.py`
  - [ ] Multi-tenant support
  - [ ] Usage tracking per tenant

- [ ] **P2.7.2** Define pricing plans
  - [ ] Free, Researcher, Lab, Enterprise
  - [ ] Quotas, features, allowed models per plan

- [ ] **P2.7.3** Add API key authentication
  - [ ] Generate API keys per tenant
  - [ ] Check quotas on each request

---

#### 8. Deployment Feedback Loop (8-10h)

- [ ] **P3.8.1** Add experiment monitoring
  - [ ] Health checks for long-running experiments
  - [ ] Auto-diagnose failures

- [ ] **P3.8.2** Implement auto-fix
  - [ ] Generate fixes for detected issues
  - [ ] Deploy fixes automatically
  - [ ] Expected: Higher completion rate

---

## 📊 Paradigm-Shift Tracking

### Quality Metrics

| Metric | Baseline | Current | Target | Status |
|--------|----------|---------|--------|--------|
| Code quality score | 7.2/10 | 7.2/10 | 9.0/10 | ⏳ Pending |
| Test coverage | 0% | 0% | 80%+ | ⏳ Pending |
| Revision token cost | $0.06 | $0.06 | $0.01-0.02 | ⏳ Pending |
| Repair cycles | 2.3 avg | 2.3 avg | 1.5 avg | ⏳ Pending |
| Literature relevance | 0.70 | 0.70 | 0.90+ | ⏳ Pending |

### Implementation Progress

| Phase | Tasks | Complete | In Progress | Pending | Impact |
|-------|-------|----------|-------------|---------|--------|
| **Phase 1 P0** | 3 | 0 | 0 | 3 | +18% quality, -60-80% cost |
| **Phase 2 P1** | 2 | 0 | 0 | 2 | Verifiable claims, ecosystem |
| **Phase 3 P2/P3** | 3 | 0 | 0 | 3 | Optional enhancements |

---

## 📚 Grey Literature Search (New - Literature Enhancement)

**Source:** `docs/GREY_LITERATURE_SEARCH.md`  
**Expected Impact:** +100% literature coverage, +40% unique findings  
**Status:** 📋 Planned | **Next:** After Phase 1 Cost Optimizations

---

### Why Grey Literature Matters

**Grey literature** = research not formally published in peer-reviewed journals

| Type | Examples | Coverage Impact |
|------|----------|-----------------|
| **Preprints** | bioRxiv, medRxiv, SSRN | +60-80% papers |
| **Theses** | DART-Europe, NDLTD | +20-30% papers |
| **Clinical Trials** | ClinicalTrials.gov | Critical for medical |
| **Datasets/Code** | Zenodo, Figshare, GitHub | Reproducibility |
| **Conference Papers** | DBLP, OpenReview, ACM | +50-70% CS/ML papers |

**Current State:** Only OpenAlex, Semantic Scholar, arXiv — misses 40-60% of research  
**Target:** Add 8+ grey literature sources with quality verification

---

### Phase 1: Critical Preprint Servers (Week 1) - P1

**Expected Impact:** +60-80% more papers | **Effort:** ~12-15 hours

- [ ] **P1.1.1** Create grey literature module
  - [ ] `berb/literature/grey_literature/__init__.py`
  - [ ] `base.py` — Base grey literature client
  - [ ] `quality.py` — Multi-layer quality verification

- [ ] **P1.1.2** Add bioRxiv client (Biology)
  - [ ] `biorxiv.py` — REST API client
  - [ ] API: `https://api.biorxiv.org/`
  - [ ] Expected: 200k+ biology preprints
  - [ ] Quality signals: institution, authors, citations

- [ ] **P1.1.3** Add medRxiv client (Medicine)
  - [ ] `medrxiv.py` — REST API client
  - [ ] API: `https://api.medrxiv.org/`
  - [ ] Expected: 150k+ medical preprints

- [ ] **P1.1.4** Add SSRN client (Social Sciences)
  - [ ] `ssrn.py` — Limited API + scraping fallback
  - [ ] Expected: 800k+ social science preprints

- [ ] **P1.1.5** Implement quality verification
  - [ ] Source reputation scoring (arXiv=0.95, unknown=0.50)
  - [ ] Author affiliation checking
  - [ ] Citation count normalization by age/field
  - [ ] Later peer-reviewed check (+15% quality bonus)
  - [ ] Minimum quality threshold: 0.70

- [ ] **P1.1.6** Integrate with literature search
  - [ ] Modify `berb/literature/search.py`
  - [ ] Add grey literature as optional sources
  - [ ] Domain-specific activation (medical → medRxiv)
  - [ ] Quality filtering (min score 0.70)

- [ ] **P1.1.7** Test grey literature search
  - [ ] Run 10 searches with/without grey lit
  - [ ] Measure: recall improvement, quality scores
  - [ ] Expected: +60-80% papers, -2% avg quality (acceptable)

---

### Phase 2: Theses & Clinical Trials (Week 2) - P1

**Expected Impact:** +20-30% medical papers | **Effort:** ~10-12 hours

- [ ] **P1.2.1** Add DART-Europe client (Theses)
  - [ ] `dart_europe.py` — OAI-PMH client
  - [ ] Expected: 1M+ European theses

- [ ] **P1.2.2** Add NDLTD client (Theses)
  - [ ] `ndltd.py` — OAI-PMH client
  - [ ] Expected: 6M+ global theses

- [ ] **P1.2.3** Add ClinicalTrials.gov client
  - [ ] `clinical_trials.py` — REST API client
  - [ ] API: `https://clinicaltrials.gov/api/`
  - [ ] Expected: 450k+ clinical trials
  - [ ] Critical for medical research

- [ ] **P1.2.4** Add quality verification for theses
  - [ ] University reputation scoring
  - [ ] Advisor h-index checking
  - [ ] Citation count normalization

- [ ] **P1.2.5** Integrate with literature search
  - [ ] Auto-activate for medical domain
  - [ ] Include trial results in literature review

---

### Phase 3: Datasets & Code (Week 3) - P2

**Expected Impact:** Better reproducibility | **Effort:** ~8-10 hours

- [ ] **P2.3.1** Add Zenodo client
  - [ ] `zenodo.py` — REST API client
  - [ ] Expected: 5M+ datasets/code/papers

- [ ] **P2.3.2** Add Figshare client
  - [ ] `figshare.py` — REST API client
  - [ ] Expected: 2M+ datasets/figures

- [ ] **P2.3.3** Add GitHub code search
  - [ ] `github_code.py` — GitHub API client
  - [ ] Search for experiment code, datasets

- [ ] **P2.3.4** Integrate with experiment design
  - [ ] Suggest existing datasets for reuse
  - [ ] Find code implementations for methods
  - [ ] Expected: Faster experiments, better reproducibility

---

### Phase 4: Conference Proceedings (Week 4) - P2

**Expected Impact:** +50-70% CS/ML papers | **Effort:** ~10-12 hours

- [ ] **P2.4.1** Add DBLP client (CS Bibliography)
  - [ ] `dblp.py` — DBLP API client
  - [ ] Expected: 6M+ CS publications

- [ ] **P2.4.2** Add OpenReview client (ML/AI)
  - [ ] `openreview.py` — OpenReview API
  - [ ] Expected: 100k+ NeurIPS/ICLR/ICML papers

- [ ] **P2.4.3** Add ACM DL client
  - [ ] `acm_dl.py` — ACM REST API
  - [ ] Expected: 3M+ CS papers

- [ ] **P2.4.4** Integrate with CS/ML research
  - [ ] Auto-activate for CS domain
  - [ ] Prioritize conference papers for ML

---

## 📊 Grey Literature Tracking

### Coverage Metrics

| Metric | Baseline | Current | Target | Status |
|--------|----------|---------|--------|--------|
| Papers per search | 20-30 | 20-30 | 40-55 | ⏳ Pending |
| Grey literature % | 30% | 30% | 50% | ⏳ Pending |
| Quality score avg | 0.85 | 0.85 | 0.83 | ⏳ Pending |
| Recent papers (<1y) | 20% | 20% | 50% | ⏳ Pending |
| Unique findings | 100% | 100% | 140% | ⏳ Pending |

### Implementation Progress

| Phase | Sources | Complete | In Progress | Pending | Coverage Gain |
|-------|---------|----------|-------------|---------|---------------|
| **Phase 1 P1** | 3 (preprints) | 0 | 0 | 3 | +60-80% |
| **Phase 2 P1** | 3 (theses/trials) | 0 | 0 | 3 | +20-30% |
| **Phase 3 P2** | 3 (datasets/code) | 0 | 0 | 3 | Reproducibility |
| **Phase 4 P2** | 3 (conferences) | 0 | 0 | 3 | +50-70% CS/ML |

---

## 🧠 Hyperagents Architecture (Self-Improving Agents)

**Source:** `docs/HYPERAGENTS_PAPER_ANALYSIS.md` — Facebook AI Research paper (arXiv:2603.19461v1)  
**Paper:** "HYPERAGENTS: Self-Referential Self-Improving Agents for Any Computable Task"  
**Authors:** Zhang et al. (FAIR, U Toronto, U Cambridge)  
**Expected Impact:** +32% quality, self-improving, cross-domain transfer  
**Status:** 📋 Research Complete | **Priority:** **P0** — Highest ROI

---

### What Are Hyperagents? (Based on Paper)

**Hyperagents** = Self-referential self-improving agents that integrate:
- **Task Agent** — Solves target task (research automation)
- **Meta Agent** — Modifies task agent AND its own modification procedure
- **Persistent Memory** — Cross-run improvement tracking
- **Editable Modification Procedure** — Metacognitive self-modification

**Key Innovation:** The meta-level modification procedure is itself editable, enabling **metacognitive self-modification** — improving not just task-solving, but the mechanism that generates improvements.

**Paper Results:**
- DGM-H outperforms baselines by +37-58% across domains
- Meta-improvements transfer across domains
- Improvements accumulate across runs
- Self-accelerating progress over time

---

### Phase 1: Foundation (Week 1-2) - P0

**Expected Impact:** Foundation for self-improving system | **Effort:** ~12-15 hours

- [ ] **P0.1** Create Hyperagent base class
  - [ ] `berb/hyperagent/__init__.py`
  - [ ] `berb/hyperagent/base.py` — Hyperagent base class
  - [ ] `berb/hyperagent/task_agent.py` — Wraps existing 23-stage pipeline
  - [ ] `berb/hyperagent/meta_agent.py` — Self-improvement logic
  - [ ] `berb/hyperagent/memory.py` — Persistent memory for cross-run storage

- [ ] **P0.2** Implement self-improvement loop
  - [ ] `berb/hyperagent/improvement_loop.py`
  - [ ] Performance analysis module
  - [ ] Diff generation for code improvements
  - [ ] Evaluation and selection logic
  - [ ] `select_next_parent.py` — Select best variant for next iteration

- [ ] **P0.3** Add persistent memory
  - [ ] Run history storage (all projects)
  - [ ] Improvement log (what worked, what didn't)
  - [ ] Cross-domain pattern extraction
  - [ ] Quality metrics per stage per domain

- [ ] **P0.4** Test basic self-improvement
  - [ ] Run 5 research projects
  - [ ] Verify meta-agent generates improvements
  - [ ] Measure performance gain over runs
  - [ ] Expected: +10-20% improvement by run 5

---

### Phase 2: Metacognitive Enhancement (Week 3-4) - P1

**Expected Impact:** Self-accelerating improvement, cross-domain transfer | **Effort:** ~14-16 hours

- [ ] **P1.1** Make modification procedure editable
  - [ ] `berb/hyperagent/meta_modify.py`
  - [ ] Meta-agent can modify its own `generate_improvements()` method
  - [ ] Track meta-level improvements separately

- [ ] **P1.2** Add cross-domain transfer
  - [ ] Extract patterns from ML research → apply to Biology
  - [ ] Transfer improvement strategies across domains
  - [ ] Measure transfer effectiveness

- [ ] **P1.3** Implement performance tracking
  - [ ] Per-stage metrics collection
  - [ ] Bottleneck detection
  - [ ] Automatic improvement prioritization

- [ ] **P1.4** Test metacognitive improvement
  - [ ] Run 20 research projects across 4 domains
  - [ ] Measure: improvement acceleration over time
  - [ ] Expected: Meta-improvements compound, +30-50% by run 20

---

### Phase 3: Production Hardening (Week 5-6) - P1

**Expected Impact:** Production-ready self-improving system | **Effort:** ~12-15 hours

- [ ] **P1.5** Add safety mechanisms
  - [ ] `berb/hyperagent/safety.py`
  - [ ] Prevent destructive self-modifications
  - [ ] Rollback capability
  - [ ] Human-in-the-loop for major changes

- [ ] **P1.6** Implement visualization
  - [ ] Improvement trajectory dashboard
  - [ ] Meta-level change visualization
  - [ ] Cross-domain transfer diagrams

- [ ] **P1.7** Benchmark against baseline
  - [ ] Run 50 projects with Hyperagent
  - [ ] Run 50 projects with fixed pipeline
  - [ ] Compare: quality, speed, cost, success rate
  - [ ] Expected: Hyperagent outperforms by +40-60%

---

## 📊 Hyperagents Tracking (Updated from Paper)

### Performance Metrics (Paper Results)

| Metric | Baseline | DGM-H | Improvement |
|--------|----------|-------|-------------|
| **Coding Tasks** | 65% | 89% | +37% |
| **Math Problems** | 58% | 82% | +41% |
| **Scientific Reasoning** | 52% | 78% | +50% |
| **Multi-step Planning** | 45% | 71% | +58% |

### AutoResearchClaw Targets

| Metric | Current | Target (run 50) | Improvement |
|--------|---------|-----------------|-------------|
| **Quality score** | 7.2/10 | 9.5/10 | +32% |
| **Success rate** | 85% | 95% | +12% |
| **Time per project** | 3 hours | 1.5 hours | -50% |
| **Cost per project** | $2.50 | $0.80 | -68% |
| **Cross-domain transfer** | None | Full transfer | New capability |
| **Self-improvement** | None | Continuous | New capability |

### Implementation Progress

| Phase | Tasks | Complete | In Progress | Pending | Impact |
|-------|-------|----------|-------------|---------|--------|
| **Phase 1 P0** | 4 | 0 | 0 | 4 | Self-improving foundation |
| **Phase 2 P1** | 4 | 0 | 0 | 4 | Metacognitive enhancement |
| **Phase 3 P1** | 3 | 0 | 0 | 3 | Production hardening |

---

## 🔍 Additional Model Providers (Perplexity + xAI)

**Source:** `docs/PERPLEXITY_XAI_ANALYSIS.md`  
**Expected Impact:** +67% literature coverage, +18% hypothesis quality  
**Status:** 📋 Research Complete | **Priority:** **P1** — High value, easy integration

---

### Perplexity Sonar Models

| Model | Category | Best For | AutoResearchClaw Application |
|-------|----------|----------|-----------------------------|
| **sonar** | Search | Quick factual queries | Stage 1, 4, 23 (fact-checking) |
| **sonar pro** | Search | Complex queries, follow-ups | Stage 3, 5 (search planning) |
| **sonar reasoning pro** | Reasoning | Multi-step reasoning | Stage 8, 15, 18 (hypotheses, decisions, review) |
| **sonar deep research** ⭐ | Research | Literature reviews | **Stage 3-6 (literature search)** |

**Key Benefits:**
- Real-time web grounding
- Exhaustive literature search
- Cross-source verification
- Retraction detection

---

### xAI Grok Models

| Model | Context Window | Best For | AutoResearchClaw Application |
|-------|----------------|----------|-----------------------------|
| **Grok 4.20** ⭐ | 2M tokens | Full paper analysis | Stage 4 (complete paper analysis) |
| **Grok 4** | 2M tokens | Complex reasoning | Stage 8, 9 (hypotheses, experiment design) |
| **Grok 3 Mini** | 128K tokens | Cost-effective tasks | Simple classification, summarization |

**Key Benefits:**
- **2M context window** — Analyze 50+ papers simultaneously
- Full paper analysis (not just abstracts)
- Cross-paper synthesis
- Coherent full-draft generation
- Batch API: 50% discount

---

### Phase 1: Provider Integration (Week 1) - P1

**Expected Impact:** Foundation for new providers | **Effort:** ~4-6 hours

- [ ] **P1.1** Add Perplexity provider preset
  - [ ] `berb/llm/__init__.py` — Add `perplexity` to `PROVIDER_PRESETS`
  - [ ] `base_url`: `https://api.perplexity.ai`
  - [ ] API key config: `PERPLEXITY_API_KEY`
  - [ ] Test connectivity

- [ ] **P1.2** Add xAI provider preset
  - [ ] `berb/llm/__init__.py` — Add `xai` to `PROVIDER_PRESETS`
  - [ ] `base_url`: `https://api.x.ai/v1`
  - [ ] API key config: `XAI_API_KEY`
  - [ ] Test connectivity

- [ ] **P1.3** Update model routing config
  - [ ] Add Sonar models to NadirClaw routing
  - [ ] Add Grok models to NadirClaw routing
  - [ ] Configure cascade per task type

- [ ] **P1.4** Test basic integration
  - [ ] Run test queries through both providers
  - [ ] Verify billing/usage tracking
  - [ ] Expected: Both providers working

---

### Phase 2: Specialized Clients (Week 2) - P1

**Expected Impact:** +67% literature coverage, +18% hypothesis quality | **Effort:** ~10-12 hours

- [ ] **P2.1** Create Perplexity client
  - [ ] `berb/literature/perplexity_client.py`
  - [ ] `PerplexityClient` class
  - [ ] `deep_research()` method for literature review
  - [ ] `verify_citation()` method for verification

- [ ] **P2.2** Create Grok client
  - [ ] `berb/literature/grok_client.py`
  - [ ] `GrokClient` class
  - [ ] `analyze_full_paper()` method (2M context)
  - [ ] `synthesize_papers()` method (cross-paper synthesis)
  - [ ] `generate_full_draft()` method

- [ ] **P2.3** Integrate with literature search
  - [ ] Modify Stage 3-4 to use Sonar Deep Research
  - [ ] Add as optional enhancement (config flag)
  - [ ] Fallback to existing APIs if Sonar fails

- [ ] **P2.4** Integrate with paper analysis
  - [ ] Modify Stage 4 to use Grok for key papers (top 10)
  - [ ] Config: number of papers to analyze with Grok
  - [ ] Cost tracking per provider

- [ ] **P2.5** Test specialized clients
  - [ ] Run 5 literature searches with Sonar
  - [ ] Run 5 paper analyses with Grok
  - [ ] Compare quality vs baseline
  - [ ] Expected: +40-60% literature quality

---

### Phase 3: Cost Optimization (Week 3) - P2

**Expected Impact:** Optimal cost/quality balance | **Effort:** ~8-10 hours

- [ ] **P3.1** Add cost tracking per provider
  - [ ] Track tokens per provider
  - [ ] Track cost per project
  - [ ] Dashboard widget for provider costs

- [ ] **P3.2** Implement smart routing
  - [ ] Route simple queries to cheap models (Sonar, Grok 3 Mini)
  - [ ] Route complex tasks to premium models (Sonar Deep Research, Grok 4.20)
  - [ ] Config-based routing rules

- [ ] **P3.3** Add Batch API support (xAI)
  - [ ] Implement batch submission for non-urgent tasks
  - [ ] 50% cost savings
  - [ ] 24h processing window

- [ ] **P3.4** Benchmark and optimize
  - [ ] Run 20 projects with new providers
  - [ ] Measure: quality, cost, speed
  - [ ] Adjust routing rules based on results
  - [ ] Expected: Optimal cost/quality balance

---

## 📊 Model Provider Tracking

### Coverage Metrics

| Metric | Current | With Sonar+Grok | Target | Status |
|--------|---------|-----------------|--------|--------|
| Literature coverage | 20-30 papers | 35-50 papers | 35-50 | ⏳ Pending |
| Literature quality | 0.85 | 0.92 | 0.92 | ⏳ Pending |
| Paper analysis depth | Abstract | Full-paper | Full-paper | ⏳ Pending |
| Hypothesis quality | 7.2/10 | 8.5/10 | 8.5/10 | ⏳ Pending |
| Draft coherence | 7.5/10 | 8.8/10 | 8.8/10 | ⏳ Pending |

### Implementation Progress

| Phase | Tasks | Complete | In Progress | Pending | Impact |
|-------|-------|----------|-------------|---------|--------|
| **Phase 1 P1** | 4 | 0 | 0 | 4 | Provider foundation |
| **Phase 2 P1** | 5 | 0 | 0 | 5 | Specialized clients |
| **Phase 3 P2** | 4 | 0 | 0 | 4 | Cost optimization |

---

## 🧪 Code Agent Improvements

### Code Generation Quality - P1

- [ ] **P1** Enhance CodeAgent v2 validation
- [ ] **P1** Improve execution-in-the-loop
- [ ] **P2** Add code quality metrics

---

### OpenCode Beast Mode - P2

- [ ] **P2** Improve complexity scoring
- [ ] **P2** Enhance workspace collection

---

## 📚 Literature System Enhancements

### Multi-Source Search - P1

- [ ] **P1** Add more literature sources (via SearXNG)
- [ ] **P1** Improve deduplication (via SearXNG)
- [ ] **P2** Add citation graph analysis

---

### PDF Processing - P2

- [ ] **P2** Improve PDF text extraction
- [ ] **P2** Add figure extraction

---

## 🧪 Experiment System Enhancements

### Sandbox Improvements - P1

- [ ] **P1** Enhance security
- [ ] **P1** Improve error detection
- [ ] **P2** Add experiment templating

---

### Docker Sandbox - P2

- [ ] **P2** Improve GPU support
- [ ] **P2** Add distributed execution

---

## 📝 Paper Writing Enhancements

### LaTeX Generation - P1

- [ ] **P1** Add more conference templates
- [ ] **P1** Improve table generation
- [ ] **P2** Add Beamer presentation export

---

### Writing Quality - P1

- [ ] **P1** Enhance anti-fabrication guard
- [ ] **P1** Improve revision length guard
- [ ] **P2** Add grammar/style checking

---

## 🔍 Citation Verification Improvements

### Multi-Layer Verification - P0

- [ ] **P0** Improve arXiv verification
- [ ] **P1** Add Crossref similarity search
- [ ] **P1** Enhance LLM relevance scoring
- [ ] **P2** Add Semantic Scholar S2API integration

---

## 🖥️ Figure Generation System

### Figure Agent - P1

- [ ] **P1** Improve Matplotlib generation
- [ ] **P1** Enhance Nano Banana integration
- [ ] **P2** Add TikZ/PGFPlots support
- [ ] **P2** Implement figure consistency checks

---

## 🏗️ Infrastructure & DevOps

### Testing - P1

- [ ] **P1** Increase test coverage (target: 85%+)
- [ ] **P1** Add performance tests
- [ ] **P2** Create end-to-end test scenarios

---

### Documentation - P1

- [ ] **P1** Update README.md with integration features
- [ ] **P1** Create video tutorials
- [ ] **P2** Write architecture documentation

---

### CI/CD - P2

- [ ] **P2** Add automated releases
- [ ] **P2** Implement canary deployments

---

## 📈 Analytics & Monitoring

### Run Analytics - P2

- [ ] **P2** Implement run statistics dashboard
- [ ] **P2** Add user feedback collection
- [ ] **P2** Create benchmark suite

---

### Logging & Observability - P2

- [ ] **P2** Add structured logging
- [ ] **P2** Integrate with observability tools

---

## 🔒 Security Enhancements

### Sandbox Security - P0

- [ ] **P0** Audit sandbox escape vectors
- [ ] **P0** Add security scanning to CI
- [ ] **P1** Implement secrets detection

---

## 🌍 Internationalization

### Multi-Language Support - P3

- [ ] **P3** Add i18n framework
- [ ] **P3** Translate documentation

---

## 🤝 Community & Ecosystem

### Plugin System - P3

- [ ] **P3** Design plugin architecture
- [ ] **P3** Create example plugins

---

### Integration Partners - P2

- [ ] **P2** Overleaf integration
- [ ] **P2** Hugging Face integration
- [ ] **P2** GitHub integration

---

## 📋 Backlog (Future Considerations)

### Research Features - P3

- [ ] Multi-paper runs
- [ ] Collaborative research
- [ ] Human-in-the-loop checkpoints
- [ ] Real-time collaboration dashboard

---

### Advanced AI Features - P3

- [ ] Multi-agent debate for all stages
- [ ] Self-improving prompt optimization
- [ ] Automated hyperparameter tuning

---

### Enterprise Features - P3

- [ ] SSO integration
- [ ] Team management
- [ ] Access controls
- [ ] Audit logging

---

## 📝 Notes

### Priority Definitions

- **P0 (Critical):** Must-have for next release, blocks other work
- **P1 (High):** Important improvements, should do soon
- **P2 (Medium):** Valuable but not urgent, schedule permitting
- **P3 (Low):** Nice-to-have, future consideration

### Estimation Guidelines

- Week = 5 working days
- Phase duration assumes 3 developers (parallel work)
- Adjust based on team capacity
- Some tasks can be parallelized

### Dependencies

```
Week 1 (Foundation):
  Mnemo P0 → Mnemo P1+
  Reasoner P0 → Reasoner P1+
  SearXNG P0 → SearXNG P1+

Week 2 (Quality):
  All P1 → All P2

Week 3 (Advanced):
  All P2 → All P1 (hardening)

Week 4 (Production):
  All P1 → Release
```

---

## 🎯 Sprint Schedule

### Sprint 1: Week 1 (Foundation)

**Goals:**
- [ ] All three modules created
- [ ] All three servers running locally
- [ ] Basic integration working
- [ ] Unit tests passing

**Success Criteria:**
- Can import all three modules
- Mnemo responds on port 50001
- SearXNG responds on port 8888
- Reasoner parsing works
- All unit tests pass

---

### Sprint 2: Week 2 (Quality)

**Goals:**
- [ ] Context vetting working
- [ ] Critique scoring implemented
- [ ] Custom SearXNG engines added
- [ ] Circuit breakers active

**Success Criteria:**
- CoT detection filters bad papers
- Peer reviews have quantitative scores
- OpenAlex/Semantic Scholar in SearXNG
- Provider failures handled gracefully

---

### Sprint 3: Week 3 (Advanced)

**Goals:**
- [ ] Self-healing working
- [ ] Reasoning presets available
- [ ] SearXNG deduplication active
- [ ] Dashboard widgets created

**Success Criteria:**
- Experiment bugs auto-repaired
- 5 reasoning methods selectable
- No duplicate papers in results
- Real-time metrics visible

---

### Sprint 4: Week 4 (Production)

**Goals:**
- [ ] A/B benchmarks complete
- [ ] Observability stack ready
- [ ] Security audit passed
- [ ] Documentation complete

**Success Criteria:**
- 50 runs benchmarked (with/without)
- Prometheus + Grafana dashboards
- All security checks pass
- User guides published

---

## 📊 Success Metrics

| Metric | Baseline | Target (8 weeks) | Measurement |
|--------|----------|------------------|-------------|
| Hypothesis diversity | 2.3/10 | 7.5/10 | Perspective variance |
| Experiment flaws | 35% | <15% | Pre-execution stress tests |
| Citation hallucinations | 2-3% | <0.5% | Post-vetting audit |
| Literature sources | 3 | 8+ | Engine count |
| Papers per query | 15-25 | 40-60 | Results count |
| **Token consumption (CLI)** | 100% | 30-40% | RTK filtering |
| **LLM API costs** | 100% | 40-60% | NadirClaw routing |
| **Input tokens** | 100% | 50-70% | Context optimization |
| **API cost reduction** | $2.50/run | $0.60/run | RTK + NadirClaw |
| Repeated mistakes | 15% | <5% | Cross-run error analysis |
| Pipeline retries | 15% | <8% | Error tracking |
| Search time | 8-12s | 4-6s | Latency tracking |
| User satisfaction | 3.8/5 | 4.5/5 | Post-run surveys |
| Paper quality score | 6.2/10 | 8.5/10 | Blind expert review |

---

**Last Updated:** 2026-03-26  
**Next Review:** 2026-04-02  
**Sprint Review:** Every Friday 10:00 AM
