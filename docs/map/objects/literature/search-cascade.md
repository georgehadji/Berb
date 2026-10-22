---
type: object
cluster: literature
universe: live
status: verified
verified: 2026-10-22 @ fb7bd25
entity: berb/literature/search.py
---

# Search cascade (OpenAlex, Semantic Scholar, arXiv, Perplexity top-up)

`search_papers` and `search_papers_multi_query` (`search.py:145`, `283`) query three free academic APIs, merge, deduplicate and rank. The only live way Berb finds papers.

## Why this shape

Sources run in order OpenAlex, Semantic Scholar, arXiv: most generous rate limit first, arXiv (1 request per 3 s) last (`search.py:34-36`). A paid Perplexity search is a backstop, not a fourth source: it fires once per run only when the free cascade under-delivers (`search.py:333-353`).

## Shape

- Per source: client call, then `cache_put`, then a fixed sleep (0.5 s after OpenAlex, 1.0 s after S2) (`search.py:195-226`). `multi_query` adds `inter_query_delay` 1.5 s between queries.
- Dedup priority DOI, then arXiv id, then normalised title; the higher `citation_count` wins (`search.py:405-484`).
- Rank: `citation_count` times 1.1 for a top-tier venue name, then year, descending (`search.py:68-77`, `275-278`). `year_max` drops later work; `year == 0` is never dropped (`search.py:265-272`).
- Perplexity top-up when fewer than `perplexity_min_candidates` (default 10) survive, or when at least `perplexity_min_failed_sources` (default 2) sources failed (`search.py:333-337`). Stage 4 enables it on round 0 only (`_literature.py:461`).
- Search cache: `.berb_cache/literature/` relative to the current directory; TTL arXiv 1 d, S2 and OpenAlex 3 d (`cache.py:25-33`); capped at 2 GiB (`cache.py:169`). Written only for non-empty results; read only in the failure branch of `search_papers`.
- Clients: `openalex_client.py`, `semantic_scholar.py` (breaker trips after 3 consecutive 429s), `arxiv_client.py` (own breaker); all share `_rate_limiter.RateLimiter`.

## Fixed 2026-10-22 (uncommitted): failures were invisible

The clients used to swallow failures and return `[]`, so the `except` branch in `search_papers` (cache fallback plus `failure_counter`) never ran, an outage overwrote a good cache entry with `[]`, and the "sources down" Perplexity trigger could never fire. Now:
- Each client takes `raise_on_failure=False` (default unchanged, so `trends/feeds.py` and direct callers behave as before). With it set they raise `RuntimeError` on request failure, an open circuit breaker, or a missing arxiv library (`openalex_client.py`, `semantic_scholar.py`, `arxiv_client.py`).
- `search_papers` passes `raise_on_failure=True` to all three, so a failed source reaches the cache fallback and increments `failure_counter` (`search.py:195-240`).
- `_cache_if_found` skips empty results, so neither an outage nor a genuinely empty answer can replace a good cache entry (`search.py:89-98`).
- Tests: `tests/test_literature_failure_signals.py` (8 search tests).
- Not changed: a cache entry only helps within its TTL (arXiv 1 d, others 3 d), and a legitimately empty query still returns `[]`.

## Connected to

- **owns:** the dedup and ranking rules, the search cache.
- **joins:** [[paper-model]] (`Paper`), [[literature-stages]] (stage 4 and `novelty` call it), `perplexity_search.py` (lazy import `search.py:379`), `trends/feeds.py` (imports the three clients directly, not this module).
- **looks-like-but-is-not:** `searxng_client.py` and `grey_search.py` (parked, never called); the verification path in [[citation-verify]], which does its own lookups.

## If you change this

- **Hits:** stage 4 (`_literature.py:442`), [[novelty]] (`novelty.py:323`), `_citations.py:192`; tests `tests/test_berb_literature.py`, `test_berb_cache.py`, `test_literature_expansion.py`.
- **Hits:** the `raise_on_failure` contract: `search_papers` depends on it for the cache fallback and the Perplexity trigger; any new client must support it.
- **Does not hit:** citation verification, retraction lookups (separate HTTP code).

## Surfaces

| Surface | Role |
|---|---|
| `berb run` stage 4 | main consumer |
| `berb literature` (stages 1-8) | same path |

## See

- Source: `berb/literature/search.py`, `cache.py`, `openalex_client.py`, `semantic_scholar.py`, `arxiv_client.py`
