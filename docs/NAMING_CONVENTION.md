# Project Naming Convention

**Author:** Georgios-Chrysovalantis Chatzivantsidis

---

## Naming Policy

All integrated external projects must be renamed to avoid trademark issues and maintain project independence.

---

## Original → New Name Mapping

| Original Name | New Name | Rationale |
|---------------|----------|-----------|
| **Mnemo Cortex** | **MemoryVault** | Descriptive, no trademark |
| **Reasoner (ARA Pipeline)** | **CognitiveFlow** | Describes reasoning flow |
| **SearXNG** | **MetaSearch** | Generic metasearch name |
| **RTK (Rust Token Killer)** | **TokenSaver** | Descriptive of function |
| **NadirClaw** | **ModelRouter** | Describes model routing function |
| **Hyperagents** | **SelfEvolve** | Describes self-improvement |
| **Perplexity Sonar** | **DeepQuery** | Describes deep search |
| **xAI Grok** | **DeepMind AI** | Generic AI name |

---

## Code Attribution Standard

All code files must include author attribution:

```python
"""Module description.

Author: Georgios-Chrysovalantis Chatzivantsidis
"""
```

---

## Updated Import Paths

| Old Import | New Import |
|------------|------------|
| `berb.mnemo_bridge` | `berb.memory_vault` |
| `berb.reasoner_bridge` | `berb.cognitive_flow` |
| `berb.literature.searxng_client` | `berb.literature.metasearch_client` |
| `berb.utils.rtk_client` | `berb.utils.token_saver` |
| `berb.llm.nadirclaw_router` | `berb.llm.model_router` |
| `berb.hyperagent` | `berb.self_evolve` |
| `berb.llm.perplexity_client` | `berb.llm.deep_query_client` |
| `berb.llm.grok_client` | `berb.llm.deepmind_client` |

---

## Documentation Updates

All documentation must reference new names:

| Document | Updates Required |
|----------|-----------------|
| `docs/MNEMO_CORTEX_INTEGRATION_PLAN.md` | → `docs/MEMORY_VAULT_INTEGRATION_PLAN.md` |
| `docs/REASONER_INTEGRATION_PLAN.md` | → `docs/COGNITIVE_FLOW_INTEGRATION_PLAN.md` |
| `docs/SEARXNG_INTEGRATION_PLAN.md` | → `docs/METASEARCH_INTEGRATION_PLAN.md` |
| `docs/RTK_INTEGRATION_PLAN.md` | → `docs/TOKEN_SAVER_INTEGRATION_PLAN.md` |
| `docs/NADIRCLAW_INTEGRATION_PLAN.md` | → `docs/MODEL_ROUTER_INTEGRATION_PLAN.md` |
| `docs/HYPERAGENTS_PAPER_ANALYSIS.md` | → `docs/SELF_EVOLVE_PAPER_ANALYSIS.md` |
| `docs/PERPLEXITY_XAI_ANALYSIS.md` | → `docs/DEEP_QUERY_DEEPMIND_ANALYSIS.md` |

---

## Implementation Checklist

- [ ] Rename all module directories
- [ ] Update all import statements
- [ ] Update all docstrings
- [ ] Update all documentation files
- [ ] Update all config examples
- [ ] Update all test files
- [ ] Add author attribution to all files
- [ ] Update TODO.md references
- [ ] Update QWEN.md references

---

**Date:** 2026-03-26  
**Author:** Georgios-Chrysovalantis Chatzivantsidis
