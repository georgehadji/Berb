# AutoResearchClaw - Project Context

## Project Overview

**AutoResearchClaw** is an autonomous research pipeline that transforms a single research idea into a conference-ready academic paper. The system runs a **23-stage pipeline** across **8 phases** with zero human intervention, producing:

- Full academic paper (Markdown + LaTeX)
- Real literature from OpenAlex, Semantic Scholar & arXiv
- Hardware-aware sandbox experiments with self-healing
- Multi-agent peer review
- Conference-ready LaTeX (NeurIPS/ICML/ICLR templates)
- Verified citations with 4-layer integrity checking

**Key Innovation:** The pipeline self-heals when experiments fail, pivots when hypotheses don't hold, and removes hallucinated citations automatically.

---

## 💼 Management Capabilities

AutoResearchClaw provides comprehensive management capabilities:

### 📋 Project Management
- **23-stage pipeline** with checkpoints and gates
- **Resource allocation** with multi-server scheduling
- **Budget tracking** with token monitoring and alerts
- **Risk management** with fallback chains and retries
- **Timeline:** ~3 hours per research paper

### 🎯 Product Management
- **Paper lifecycle** from idea to publication
- **Template system** for NeurIPS/ICML/ICLR
- **Version control** with artifact versioning
- **Publishing integration** (Overleaf, arXiv)

### 🧠 Knowledge Management
- **Mnemo Cortex** memory (L1/L2/L3 cache)
- **MetaClaw skills** for cross-run learning
- **6-category knowledge base**
- **Session archiving** with auto-capture

### ✅ Quality Control
- **3 quality gates** (stages 5, 9, 20)
- **4-layer citation verification**
- **Stress testing** (3 scenarios)
- **Multi-agent review** (4 dimensions)

**Expected Outcomes:**
- **-56%** cost reduction
- **-60%** faster delivery
- **+100%** better acceptance rate

📖 **Full docs:** `docs/MANAGEMENT_CAPABILITIES.md`

## Quick Reference

```bash
# Install & Setup
pip install -e .
berb setup          # Interactive setup (installs OpenCode, checks Docker/LaTeX)
berb init           # Creates config.arc.yaml interactively

# Run Pipeline
berb run --topic "Your research idea" --auto-approve

# Development
pytest tests/               # Run 1823+ tests
berb doctor         # Validate environment
```

## Project Structure

```
AutoResearchClaw-main/
├── berb/           # Core Python package
│   ├── pipeline/           # 23-stage pipeline orchestration
│   │   ├── runner.py       # Main pipeline runner
│   │   ├── stages.py       # Stage definitions & state machine
│   │   ├── executor.py     # Stage execution engine
│   │   ├── code_agent.py   # Multi-phase code generation
│   │   ├── opencode_bridge.py  # OpenCode Beast Mode integration
│   │   ├── paper_verifier.py   # 4-layer citation verification
│   │   └── stage_impls/    # Individual stage implementations
│   ├── agents/             # Specialized AI agents
│   │   ├── decision_agent.py   # Hypothesis/analysis decisions
│   │   ├── benchmark_agent.py  # Dataset & baseline selection
│   │   └── figure_agent.py     # Scientific visualization
│   ├── experiment/         # Experiment execution backends
│   │   ├── sandbox.py      # Local sandbox with AST validation
│   │   ├── docker_sandbox.py   # Docker with GPU support
│   │   ├── ssh_remote.py   # Remote SSH execution
│   │   └── colab_drive.py  # Google Colab via Drive
│   ├── literature/         # Literature search & collection
│   │   ├── openalex.py     # OpenAlex API client
│   │   ├── semantic_scholar.py  # Semantic Scholar client
│   │   └── arxiv_client.py  # arXiv API client
│   ├── knowledge/          # Knowledge base & memory
│   ├── llm/                # LLM provider adapters
│   │   ├── base.py         # Base provider interface
│   │   ├── openai.py       # OpenAI provider
│   │   ├── anthropic.py    # Anthropic provider
│   │   ├── acp.py          # ACP (Agent Client Protocol)
│   │   └── minimax.py      # MiniMax provider
│   ├── metaclaw_bridge/    # MetaClaw cross-run learning
│   ├── templates/          # LaTeX templates (NeurIPS/ICML/ICLR)
│   ├── utils/              # Utilities & helpers
│   └── cli.py              # CLI entry point
├── tests/                  # 1823+ test cases
│   ├── test_rc_*.py        # Core pipeline tests
│   ├── test_code_agent.py  # Code generation tests
│   ├── test_opencode_bridge.py  # OpenCode integration tests
│   └── e2e_*.py            # End-to-end tests
├── docs/                   # Documentation
│   ├── integration-guide.md    # Setup & usage guide
│   ├── TESTER_GUIDE.md     # Testing guide
│   ├── showcase/           # Generated paper showcase
│   └── README_*.md         # Translations (CN/JA/KO/FR/DE/ES/PT/RU/AR)
├── scripts/                # Utility scripts
├── config.berb.example.yaml  # Config template
├── prompts.default.yaml    # Default LLM prompts
├── pyproject.toml          # Python package configuration
└── QWEN.md                 # This file
```

## Configuration

### Minimum Required Config (`config.arc.yaml`)

```yaml
project:
  name: "my-research"

research:
  topic: "Your research topic here"

llm:
  provider: "openai-compatible"
  base_url: "https://api.openai.com/v1"
  api_key_env: "OPENAI_API_KEY"
  primary_model: "gpt-4o"
  fallback_models: ["gpt-4o-mini"]

experiment:
  mode: "sandbox"
  sandbox:
    python_path: ".venv/bin/python"  # Windows: .venv\Scripts\python.exe
```

### Key Configuration Options

| Section | Option | Description |
|---------|--------|-------------|
| `llm` | `provider` | `openai`, `openrouter`, `deepseek`, `minimax`, `acp`, `openai-compatible` |
| `llm.acp` | `agent` | ACP agent CLI: `claude`, `codex`, `gemini`, `kimi`, `opencode` |
| `experiment` | `mode` | `sandbox`, `docker`, `simulated`, `ssh_remote`, `colab_drive` |
| `experiment.opencode` | `enabled` | Enable OpenCode Beast Mode for complex experiments |
| `metaclaw_bridge` | `enabled` | Enable cross-run learning from MetaClaw |
| `runtime` | `max_parallel_tasks` | Concurrent experiment limit |
| `security` | `hitl_required_stages` | Stages requiring human approval: `[5, 9, 20]` |

## Pipeline: 23 Stages, 8 Phases

### Phase A: Research Scoping
1. **TOPIC_INIT** - Initialize research topic
2. **PROBLEM_DECOMPOSE** - Decompose into problem tree

### Phase B: Literature Discovery
3. **SEARCH_STRATEGY** - Plan search queries
4. **LITERATURE_COLLECT** - Collect from OpenAlex/Semantic Scholar/arXiv
5. **LITERATURE_SCREEN** 🔒 - Gate: relevance & quality screening
6. **KNOWLEDGE_EXTRACT** - Extract knowledge cards

### Phase C: Knowledge Synthesis
7. **SYNTHESIS** - Cluster findings, identify gaps
8. **HYPOTHESIS_GEN** - Generate hypotheses via multi-agent debate

### Phase D: Experiment Design
9. **EXPERIMENT_DESIGN** 🔒 - Gate: experiment plan
10. **CODE_GENERATION** - Generate experiment code (CodeAgent v2)
11. **RESOURCE_PLANNING** - Estimate resources

### Phase E: Experiment Execution
12. **EXPERIMENT_RUN** - Execute in sandbox
13. **ITERATIVE_REFINE** - Self-healing loop (up to 10 rounds)

### Phase F: Analysis & Decision
14. **RESULT_ANALYSIS** - Multi-agent analysis
15. **RESEARCH_DECISION** - PROCEED / REFINE / PIVOT decision

### Phase G: Paper Writing
16. **PAPER_OUTLINE** - Section outline
17. **PAPER_DRAFT** - Full draft (5,000-6,500 words)
18. **PEER_REVIEW** - Multi-agent review with evidence check
19. **PAPER_REVISION** - Revise with length guard

### Phase H: Finalization
20. **QUALITY_GATE** 🔒 - Gate: quality check
21. **KNOWLEDGE_ARCHIVE** - Archive to knowledge base
22. **EXPORT_PUBLISH** - Export LaTeX (NeurIPS/ICML/ICLR)
23. **CITATION_VERIFY** - 4-layer citation verification

> 🔒 **Gate stages** (5, 9, 20) pause for human approval. Use `--auto-approve` to skip.

## Key Features

### Multi-Agent System
- **Decision Agent**: Hypothesis generation, result analysis, PIVOT/REFINE decisions
- **Benchmark Agent**: 4-agent pipeline (Surveyor→Selector→Acquirer→Validator) for dataset selection
- **Figure Agent**: Scientific visualization (Matplotlib/TikZ + Nano Banana image generation)
- **Code Agent**: Multi-phase code generation with architecture planning & sequential file generation

### Experiment Backends

| Mode | Description |
|------|-------------|
| `sandbox` | Local sandbox with AST validation, NaN/Inf detection, self-healing |
| `docker` | Docker container with GPU support, network isolation, auto-dependency install |
| `ssh_remote` | Remote SSH execution (lab servers, cloud GPUs) |
| `colab_drive` | Google Colab via Google Drive file synchronization |
| `simulated` | Formula-generated fake data (debugging only) |

### OpenCode Beast Mode
External AI coding agent for complex experiments:
- Auto-triggered based on complexity score (threshold: 0.2)
- Generates multi-file projects with custom architectures
- Supports training loops, ablation studies, custom models
- Install: `npm i -g opencode-ai@latest` or `berb setup`

### MetaClaw Integration
Cross-run learning system:
- Captures lessons from failures/warnings
- Converts to reusable skills stored in `~/.metaclaw/skills/`
- Injects skills into all 23 stages on subsequent runs
- **+18.3% robustness** in controlled experiments

### Citation Verification (4-Layer)
1. **arXiv ID check** - Verify arXiv papers exist
2. **CrossRef/DataCite DOI** - Verify DOI resolution
3. **Semantic Scholar title match** - Cross-reference metadata
4. **LLM relevance scoring** - Semantic relevance to paper content

Hallucinated references are auto-removed before export.

## Building & Running

### Installation

```bash
# Clone
git clone https://github.com/aiming-lab/AutoResearchClaw.git
cd AutoResearchClaw

# Virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Install
pip install -e .

# Optional: Install OpenCode Beast Mode
berb setup
```

### Running the Pipeline

```bash
# Basic run
berb run --topic "Your research idea" --auto-approve

# With custom config
berb run --config config.arc.yaml --topic "..." --auto-approve

# Resume from checkpoint
berb run --resume --config config.arc.yaml

# Validate environment first
berb doctor
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test category
pytest tests/test_rc_stages.py
pytest tests/test_code_agent.py
pytest tests/test_opencode_bridge.py

# End-to-end tests (requires API keys)
pytest tests/e2e_real_llm.py
```

### Output Artifacts

After a successful run, artifacts are stored in:
```
artifacts/rc-YYYYMMDD-HHMMSS-<hash>/deliverables/
├── paper_draft.md          # Full academic paper
├── paper.tex               # Conference-ready LaTeX
├── references.bib          # Verified BibTeX references
├── verification_report.json  # Citation integrity report
├── reviews.md              # Multi-agent peer reviews
├── experiment_runs/        # Generated code + results
├── charts/                 # Auto-generated figures
└── evolution/              # Self-learning lessons
```

## Development Conventions

### Code Style
- **Type Hints**: Full type annotations with `from __future__ import annotations`
- **Error Handling**: Explicit exception handling with `BLE001` wildcard pattern
- **Docstrings**: Google-style docstrings for public APIs
- **Logging**: Structured logging via `logging` module

### Testing Practices
- **Unit Tests**: Isolated tests in `tests/test_*.py`
- **Integration Tests**: Cross-module tests in `tests/test_rc_*.py`
- **E2E Tests**: Full pipeline tests in `tests/e2e_*.py`
- **Fixtures**: Shared fixtures in `tests/conftest.py`

### Configuration Convention
- `config.berb.example.yaml` - Tracked template (no secrets)
- `config.arc.yaml` - Local config (gitignored, created by `berb init`)
- `config.yaml` - Fallback local config (gitignored)

### Git Workflow
- Branch from `main`
- One concern per PR
- Ensure `pytest tests/` passes
- Include tests for new functionality

## LLM Providers

### Supported Providers

| Provider | Config Example |
|----------|---------------|
| OpenAI | `provider: "openai"` |
| OpenRouter | `provider: "openrouter"` |
| DeepSeek | `provider: "deepseek"` |
| MiniMax | `provider: "minimax"` |
| Anthropic | `provider: "anthropic"` |
| ACP (Agent Client Protocol) | `provider: "acp"` |
| OpenAI-Compatible | `provider: "openai-compatible"` |

### ACP (Agent Client Protocol)
Use any ACP-compatible coding agent as LLM backend:

```yaml
llm:
  provider: "acp"
  acp:
    agent: "claude"   # or: codex, gemini, kimi, opencode
    cwd: "."
```

No API keys needed - the agent handles its own authentication.

## Security Features

### Sandbox Security
- **AST Validation**: Code validated before execution
- **Import Restrictions**: Whitelist-only imports
- **Memory Limits**: Configurable memory caps
- **Timeout Enforcement**: Hard time budgets per experiment
- **NaN/Inf Fast-Fail**: Immediate detection of invalid results

### Sentinel Watchdog
Background quality monitor:
- NaN/Inf detection
- Paper-evidence consistency checks
- Citation relevance scoring
- Anti-fabrication guard

### Gate Stages
Three human-in-the-loop gates (configurable):
- Stage 5: Literature screening approval
- Stage 9: Experiment design approval
- Stage 20: Quality gate before export

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `berb: command not found` | Ensure virtual environment is activated |
| LLM API errors | Check `api_key_env` variable is set |
| Experiment timeouts | Increase `time_budget_sec` or reduce experiment scale |
| Docker permission denied | Add user to `docker` group or run as root |
| Citation verification fails | Check network connectivity to arXiv/CrossRef APIs |

### Debug Mode
```bash
# Enable verbose logging
export RESEARCHCLAW_DEBUG=1
berb run --topic "..." --auto-approve
```

### Health Check
```bash
berb doctor
```

## Integration Points

### OpenClaw Bridge
Optional adapters for deeper OpenClaw integration:

```yaml
openclaw_bridge:
  use_cron: true              # Scheduled research runs
  use_message: true           # Progress notifications
  use_memory: true            # Cross-session persistence
  use_sessions_spawn: true    # Parallel sub-sessions
  use_web_fetch: true         # Live web search
  use_browser: false          # Browser automation
```

### MCP Server
Model Context Protocol server for Claude Desktop integration (see `berb/mcp/`).

### Overleaf Integration
Direct Overleaf publishing support (see `berb/overleaf/`).

## Performance Benchmarks

| Metric | Value |
|--------|-------|
| Total Tests | 1823+ |
| Pipeline Stages | 23 |
| Supported LLM Providers | 6+ |
| Experiment Backends | 5 |
| Conference Templates | 3 (NeurIPS/ICML/ICLR) |
| Citation Verification Layers | 4 |
| MetaClaw Robustness Improvement | +18.3% |

## Version Information

**Current Version:** v0.3.2 (Cross-Platform Support + Major Stability)

**Recent Changes:**
- Cross-platform support (Windows/macOS/Linux)
- CLI-agent code generation backend
- Anti-fabrication system (VerifiedRegistry)
- Experiment diagnosis & repair loop
- 100+ bug fixes from production runs

## Resources

- **GitHub:** https://github.com/aiming-lab/AutoResearchClaw
- **Integration Guide:** `docs/integration-guide.md`
- **Tester Guide:** `docs/TESTER_GUIDE.md`
- **Paper Showcase:** `docs/showcase/SHOWCASE.md`
- **Bug Tracker:** `docs/BUG_TRACKER.md`
- **Changelog:** See `README.md` News section

## License

MIT License - See `LICENSE` file for details.
