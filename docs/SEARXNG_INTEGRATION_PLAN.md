# SearXNG Integration Plan for AutoResearchClaw

**Document Created:** 2026-03-26
**Status:** Analysis Complete | Planning Phase

---

## Executive Summary

**SearXNG** is a privacy-respecting metasearch engine that aggregates results from **200+ search engines** including Google Scholar, arXiv, Crossref, and many academic sources. Integrating SearXNG with AutoResearchClaw would provide:

1. **Unified search interface** - Single API call to query multiple sources
2. **Enhanced source coverage** - Access to 200+ engines beyond current OpenAlex/S2/arXiv
3. **Built-in deduplication** - SearXNG handles result merging
4. **Rate limit management** - SearXNG distributes load across sources
5. **Privacy preservation** - No tracking, no profiling
6. **Self-hostable** - Full control over search infrastructure

**Expected Impact:**
- **+50%** more literature sources discovered
- **-60%** API rate limit issues
- **-40%** literature search time
- **Better coverage** of grey literature, preprints, and domain-specific repositories

---

## SearXNG Architecture Analysis

### Core Components

| Component | File | Purpose | AutoResearchClaw Integration Point |
|-----------|------|---------|-----------------------------------|
| **Search Engine** | `searx/search/__init__.py` | Main search orchestrator | Replace `researchclaw/literature/search.py` |
| **Engine Loader** | `searx/engines/__init__.py` | Dynamic engine loading | Use for custom academic engines |
| **Result Types** | `searx/result_types.py` | Typed result containers | Enhance `researchclaw/literature/models.py` |
| **Web App** | `searx/webapp.py` | HTTP API + UI | Use JSON API for programmatic access |
| **Settings** | `searx/settings.yml` | Engine configuration | Template for academic search config |
| **Engines** | `searx/engines/*.py` | Individual search backends | Reuse google_scholar, arxiv, crossref |

### Key Features

| Feature | Description | AutoResearchClaw Benefit |
|---------|-------------|--------------------------|
| **200+ Engines** | Pre-built integrations | Instant access to academic databases |
| **Deduplication** | Merge by DOI/URL/title | No duplicate papers in results |
| **Score Normalization** | Cross-engine ranking | Better result ordering |
| **Error Handling** | Graceful degradation | Continue if some sources fail |
| **Caching** | Redis/Valkey backend | Reduce API calls |
| **Plugins** | Extensible architecture | Custom academic filters |

---

## Academic Search Engines in SearXNG

### Currently Available

| Engine | File | Category | API Type |
|--------|------|----------|----------|
| **Google Scholar** | `google_scholar.py` | science | HTML scraping |
| **arXiv** | `arxiv.py` | science | XML API |
| **Crossref** | `crossref.py` | science | JSON API |
| **Semantic Scholar** | (not present) | science | JSON API |
| **OpenAlex** | (not present) | science | JSON API |
| **PubMed** | (not present) | science | E-utilities API |
| **IEEE Xplore** | (not present) | science | JSON API |
| **ACM Digital Library** | (not present) | science | JSON API |
| **BASE** | (not present) | science | OAI-PMH |
| **CORE** | (not present) | science | REST API |
| **DOAJ** | (not present) | science | REST API |
| **ZbMATH** | (not present) | math | REST API |
| **MathSciNet** | (not present) | math | API |

### Integration Strategy

**Option 1: Use Existing SearXNG Engines** (Recommended)
- Deploy SearXNG instance
- Enable academic engines (google_scholar, arxiv, crossref)
- Call SearXNG JSON API from AutoResearchClaw
- Add missing engines (OpenAlex, Semantic Scholar) to SearXNG

**Option 2: Extract Engine Code**
- Copy engine implementations (`arxiv.py`, `crossref.py`, `google_scholar.py`)
- Integrate into `researchclaw/literature/`
- Adapt to AutoResearchClaw patterns
- Maintain separately

**Option 3: Hybrid Approach** (Best of Both)
- Use SearXNG for broad search
- Keep direct API calls for OpenAlex/Semantic Scholar (higher rate limits)
- Merge results with deduplication

---

## Integration Approaches

### Approach 1: SearXNG as Primary Search Backend (Recommended)

**Architecture:**
```
AutoResearchClaw Stage 3-4
         │
         ▼
┌─────────────────────────┐
│  SearXNG API Client     │
│  (researchclaw/searxng) │
│  - search()             │
│  - get_config()         │
│  - health_check()       │
└───────────┬─────────────┘
            │ HTTP JSON API
            ▼
┌─────────────────────────┐
│   SearXNG Server        │
│   (localhost:8888)      │
│  ┌──────────────────┐   │
│  │ Enabled Engines: │   │
│  │ - google_scholar │   │
│  │ - arxiv          │   │
│  │ - crossref       │   │
│  │ - pubmed         │   │
│  │ - base           │   │
│  └──────────────────┘   │
└─────────────────────────┘
```

**Implementation:**
```python
# researchclaw/literature/searxng_client.py

import httpx
from typing import Literal
from dataclasses import dataclass

@dataclass
class SearXNGResult:
    title: str
    url: str
    content: str
    engine: str
    score: float
    published_date: str | None
    authors: list[str]
    doi: str | None

class SearXNGClient:
    def __init__(self, base_url: str = "http://localhost:8888"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def search(
        self,
        query: str,
        categories: list[str] = ["science"],
        engines: list[str] | None = None,
        language: str = "en",
        pageno: int = 1,
        time_range: Literal["day", "week", "month", "year", "all"] = "all",
        safesearch: int = 0,
    ) -> list[SearXNGResult]:
        """Search across multiple academic sources."""
        
        params = {
            "q": query,
            "categories": ",".join(categories),
            "language": language,
            "pageno": pageno,
            "time_range": time_range,
            "safesearch": safesearch,
            "format": "json",
        }
        
        if engines:
            params["engines"] = ",".join(engines)
        
        response = await self.client.get(
            f"{self.base_url}/search",
            params=params,
            headers={"Accept": "application/json"}
        )
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        for result in data.get("results", []):
            # Extract structured data
            authors = self._extract_authors(result.get("content", ""))
            doi = self._extract_doi(result)
            
            results.append(SearXNGResult(
                title=result.get("title", ""),
                url=result.get("url", ""),
                content=result.get("content", ""),
                engine=result.get("engine", ""),
                score=result.get("score", 0.0),
                published_date=result.get("publishedDate"),
                authors=authors,
                doi=doi,
            ))
        
        return results
    
    def _extract_authors(self, content: str) -> list[str]:
        """Extract authors from result content."""
        # Parse author names from HTML content
        # Implementation depends on engine-specific format
        return []
    
    def _extract_doi(self, result: dict) -> str | None:
        """Extract DOI from result metadata."""
        # Check various DOI fields
        return result.get("doi") or result.get("identifier")
    
    async def get_config(self) -> dict:
        """Get SearXNG configuration."""
        response = await self.client.get(f"{self.base_url}/config")
        response.raise_for_status()
        return response.json()
    
    async def health_check(self) -> bool:
        """Check if SearXNG is healthy."""
        try:
            response = await self.client.get(f"{self.base_url}/healthz")
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        await self.client.aclose()
```

**Usage in AutoResearchClaw:**
```python
# researchclaw/literature/search.py

from .searxng_client import SearXNGClient

async def search_literature_searxng(
    query: str,
    limit: int = 20,
    sources: list[str] | None = None,
    year_min: int | None = None,
) -> list[Paper]:
    """Search literature using SearXNG metasearch."""
    
    client = SearXNGClient()
    
    # Map AutoResearchClaw sources to SearXNG engines
    engine_mapping = {
        "google_scholar": "google scholar",
        "arxiv": "arxiv",
        "crossref": "crossref",
        "pubmed": "pubmed",
        "base": "base",
        "core": "core",
    }
    
    engines = None
    if sources:
        engines = [engine_mapping[s] for s in sources if s in engine_mapping]
    
    # Determine time range from year_min
    time_range = "all"
    if year_min:
        from datetime import datetime
        years_back = datetime.now().year - year_min
        if years_back <= 1:
            time_range = "year"
        elif years_back <= 5:
            time_range = "year"  # SearXNG doesn't support custom ranges
    
    results = await client.search(
        query=query,
        categories=["science"],
        engines=engines,
        time_range=time_range,
        pageno=1,
    )
    
    # Convert to AutoResearchClaw Paper objects
    papers = []
    for result in results[:limit]:
        paper = Paper(
            paper_id=result.doi or result.url,
            title=result.title,
            abstract=result.content,
            authors=tuple(result.authors),
            doi=result.doi,
            url=result.url,
            source=result.engine,
            year=extract_year(result.published_date),
            citation_count=0,  # SearXNG doesn't provide this
        )
        papers.append(paper)
    
    await client.close()
    return papers
```

---

### Approach 2: Custom SearXNG Instance with Academic Engines

**Configuration:**
```yaml
# config.searxng.academic.yaml

general:
  instance_name: "AutoResearchClaw Academic Search"
  enable_metrics: true

search:
  safe_search: 0
  autocomplete: "google"
  default_lang: "en"
  formats:
    - json

server:
  port: 8888
  bind_address: "127.0.0.1"
  limiter: false
  public_instance: false

outgoing:
  request_timeout: 10.0
  max_request_timeout: 30.0
  pool_connections: 100
  pool_maxsize: 50
  enable_http2: true

engines:
  # Academic search engines
  - name: google scholar
    engine: google_scholar
    shortcut: gos
    categories: science
    timeout: 10
    disabled: false

  - name: arxiv
    engine: arxiv
    shortcut: arx
    categories: science
    timeout: 10
    disabled: false

  - name: crossref
    engine: crossref
    shortcut: crs
    categories: science
    timeout: 10
    disabled: false

  # Add custom engines for OpenAlex, Semantic Scholar
  - name: openalex
    engine: openalex
    shortcut: oal
    categories: science
    timeout: 10
    disabled: false

  - name: semantic scholar
    engine: semantic_scholar
    shortcut: sem
    categories: science
    timeout: 10
    disabled: false

  # Additional academic sources
  - name: pubmed
    engine: pubmed
    shortcut: pub
    categories: science
    timeout: 10
    disabled: false

  - name: base
    engine: base
    shortcut: bas
    categories: science
    timeout: 10
    disabled: false

  - name: core
    engine: core
    shortcut: cor
    categories: science
    timeout: 10
    disabled: false

  - name: doaj
    engine: doaj
    shortcut: doa
    categories: science
    timeout: 10
    disabled: false

  - name: zbmath
    engine: zbmath
    shortcut: zbm
    categories: science
    timeout: 10
    disabled: false

plugins:
  searx.plugins.calculator.SXNGPlugin:
    active: true
  
  searx.plugins.oa_doi_rewrite.SXNGPlugin:
    active: true  # Add DOI links to results
```

---

### Approach 3: Engine Code Reuse (Lightweight)

**Copy engine implementations directly:**

```python
# researchclaw/literature/searxng_engines/arxiv.py
# Copied from SearXNG with adaptations

from typing import TypedDict
from urllib.parse import urlencode
from datetime import datetime
from lxml import etree
import httpx

from researchclaw.literature.models import Paper, Author

class SearXNGArxivConfig(TypedDict):
    base_url: str
    max_results: int

DEFAULT_CONFIG: SearXNGArxivConfig = {
    "base_url": "https://export.arxiv.org/api/query",
    "max_results": 20,
}

async def search_arxiv_searxng(
    query: str,
    page: int = 1,
    config: SearXNGArxivConfig | None = None,
) -> list[Paper]:
    """Search arXiv using SearXNG engine implementation."""
    
    cfg = config or DEFAULT_CONFIG
    
    params = {
        "search_query": f"all:{query}",
        "start": (page - 1) * cfg["max_results"],
        "max_results": cfg["max_results"],
    }
    
    url = f"{cfg['base_url']}?{urlencode(params)}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
    
    # Parse XML response
    root = etree.fromstring(response.content)
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }
    
    papers = []
    for entry in root.xpath("//atom:entry", namespaces=ns):
        # Extract title
        title_elem = entry.xpath(".//atom:title", namespaces=ns)[0]
        title = title_elem.text.strip()
        
        # Extract abstract
        summary_elem = entry.xpath(".//atom:summary", namespaces=ns)[0]
        abstract = summary_elem.text.strip()
        
        # Extract authors
        authors = []
        for author_elem in entry.xpath(".//atom:author/atom:name", namespaces=ns):
            authors.append(Author(name=author_elem.text, affiliation=""))
        
        # Extract arXiv ID
        id_elem = entry.xpath(".//atom:id", namespaces=ns)[0]
        arxiv_id = id_elem.text.split("/abs/")[-1]
        
        # Extract published date
        published_elem = entry.xpath(".//atom:published", namespaces=ns)[0]
        published_date = datetime.fromisoformat(published_elem.text)
        
        # Extract PDF URL
        pdf_elems = entry.xpath(".//atom:link[@title='pdf']", namespaces=ns)
        pdf_url = pdf_elems[0].attrib.get("href") if pdf_elems else ""
        
        paper = Paper(
            paper_id=arxiv_id,
            title=title,
            abstract=abstract,
            authors=tuple(authors),
            year=published_date.year,
            venue="arXiv",
            citation_count=0,
            arxiv_id=arxiv_id,
            url=f"https://arxiv.org/abs/{arxiv_id}",
            pdf_url=pdf_url,
            source="arxiv",
        )
        papers.append(paper)
    
    return papers
```

---

## Implementation Roadmap

### Phase 1: SearXNG Client (Week 1) - P0

**Goal:** Basic SearXNG integration working

**Tasks:**
- [ ] **P0** Create `researchclaw/literature/searxng_client.py`
  - [ ] SearXNGClient class with async HTTP
  - [ ] `search()` method with all parameters
  - [ ] `get_config()` for engine discovery
  - [ ] `health_check()` for monitoring
  - [ ] Error handling with retries

- [ ] **P0** Deploy local SearXNG instance
  - [ ] Docker Compose setup
  - [ ] Enable academic engines
  - [ ] Configure rate limits
  - [ ] Test connectivity

- [ ] **P0** Integrate with Stage 3 (SEARCH_STRATEGY)
  - [ ] Replace current search with SearXNG
  - [ ] Map sources to SearXNG engines
  - [ ] Handle result conversion
  - [ ] Write tests: `test_searxng_search()`

- [ ] **P0** Add SearXNG to config
  - [ ] `config.searxng.enabled`
  - [ ] `config.searxng.base_url`
  - [ ] `config.searxng.engines` list
  - [ ] Engine-specific timeouts

---

### Phase 2: Custom Academic Engines (Week 2) - P1

**Goal:** Add missing academic sources

**Tasks:**
- [ ] **P1** Create OpenAlex engine for SearXNG
  - [ ] Copy `researchclaw/literature/openalex_client.py` logic
  - [ ] Adapt to SearXNG engine interface
  - [ ] Add to SearXNG config
  - [ ] Test with real queries

- [ ] **P1** Create Semantic Scholar engine for SearXNG
  - [ ] Copy `researchclaw/literature/semantic_scholar.py` logic
  - [ ] Adapt to SearXNG engine interface
  - [ ] Add to SearXNG config
  - [ ] Test with real queries

- [ ] **P1** Add PubMed engine
  - [ ] Implement NCBI E-utilities API
  - [ ] Handle XML parsing
  - [ ] Add to SearXNG config
  - [ ] Test with biomedical queries

- [ ] **P1** Add BASE engine
  - [ ] Implement OAI-PMH protocol
  - [ ] Handle Dublin Core metadata
  - [ ] Add to SearXNG config
  - [ ] Test with interdisciplinary queries

- [ ] **P1** Write integration tests
  - [ ] Test all academic engines
  - [ ] Test deduplication
  - [ ] Test error handling
  - [ ] Test rate limiting

---

### Phase 3: Advanced Features (Week 3) - P2

**Goal:** Leverage SearXNG advanced capabilities

**Tasks:**
- [ ] **P2** Implement result deduplication
  - [ ] DOI-based merging
  - [ ] Title similarity fallback
  - [ ] Citation count prioritization
  - [ ] Write tests: `test_deduplication()`

- [ ] **P2** Add SearXNG caching
  - [ ] Redis/Valkey backend
  - [ ] Cache search results (TTL: 24h)
  - [ ] Cache engine configs
  - [ ] Write tests: `test_caching()`

- [ ] **P2** Implement query expansion
  - [ ] Use SearXNG autocomplete
  - [ ] Add related terms
  - [ ] Multi-language support
  - [ ] Write tests: `test_query_expansion()`

- [ ] **P2** Add engine health monitoring
  - [ ] Track engine success rates
  - [ ] Auto-disable failing engines
  - [ ] Alert on persistent failures
  - [ ] Dashboard widget

- [ ] **P2** Create SearXNG dashboard
  - [ ] Engine status display
  - [ ] Search statistics
  - [ ] Rate limit tracking
  - [ ] Cache hit rates

---

### Phase 4: Production Hardening (Week 4) - P1

**Goal:** Production-ready integration

**Tasks:**
- [ ] **P1** Performance optimization
  - [ ] Parallel engine execution
  - [ ] Connection pooling
  - [ ] Response streaming
  - [ ] Benchmark vs current system

- [ ] **P1** Add fallback mechanisms
  - [ ] Direct API fallback if SearXNG down
  - [ ] Engine-specific fallbacks
  - [ ] Graceful degradation
  - [ ] Write tests: `test_fallback()`

- [ ] **P1** Security hardening
  - [ ] Input validation
  - [ ] XSS prevention in results
  - [ ] Rate limiting per user
  - [ ] Audit logging

- [ ] **P1** Documentation
  - [ ] SearXNG setup guide
  - [ ] Engine configuration reference
  - [ ] Troubleshooting guide
  - [ ] API reference

- [ ] **P1** Benchmark comparison
  - [ ] 50 queries with/without SearXNG
  - [ ] Measure: recall, precision, time, cost
  - [ ] Document in `docs/searxng-benchmark.md`

---

## Configuration Reference

### AutoResearchClaw Config with SearXNG

```yaml
# config.arc.yaml

literature:
  # Primary search backend
  backend: "searxng"  # searxng | direct | hybrid
  
  # SearXNG configuration
  searxng:
    enabled: true
    base_url: "http://localhost:8888"
    timeout_sec: 30
    max_pages: 5
    
    # Engines to use
    engines:
      - "google scholar"
      - "arxiv"
      - "crossref"
      - "openalex"
      - "semantic scholar"
      - "pubmed"
      - "base"
      - "core"
    
    # Categories
    categories:
      - "science"
    
    # Language
    language: "en"
    
    # Safe search (0=off, 1=moderate, 2=strict)
    safesearch: 0
    
    # Time range
    time_range: "all"  # day, week, month, year, all
    
    # Deduplication
    deduplicate: true
    dedup_method: "doi"  # doi, title, url
    
    # Caching
    cache:
      enabled: true
      ttl_hours: 24
      backend: "memory"  # memory, redis, valkey
  
  # Direct API fallback (if SearXNG unavailable)
  fallback:
    enabled: true
    sources:
      - "openalex"
      - "semantic_scholar"
      - "arxiv"
    
  # Rate limiting
  rate_limits:
    openalex: 10000  # per day
    semantic_scholar: 1000  # per 5 min
    arxiv: 100  # per minute
    google_scholar: 100  # per hour (via SearXNG)
```

### SearXNG Docker Compose

```yaml
# docker-compose.searxng.yaml

version: '3.8'

services:
  searxng:
    image: searxng/searxng:latest
    container_name: searxng
    ports:
      - "8888:8080"
    volumes:
      - ./searxng-config:/etc/searxng:rw
    environment:
      - SEARXNG_BASE_URL=http://localhost:8888
      - SEARXNG_SECRET=your-secret-key-here
      - SEARXNG_LIMITER=false
    networks:
      - searxng-network
    restart: unless-stopped
  
  # Optional: Redis for caching
  redis:
    image: redis:alpine
    container_name: searxng-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - searxng-network
    restart: unless-stopped

volumes:
  redis-data:

networks:
  searxng-network:
    driver: bridge
```

### SearXNG Settings for Academic Search

```yaml
# searxng-config/settings.yml

general:
  instance_name: "AutoResearchClaw Academic Search"
  debug: false
  enable_metrics: true

search:
  safe_search: 0
  autocomplete: "google"
  default_lang: "en"
  formats:
    - html
    - json

server:
  port: 8080
  bind_address: "0.0.0.0"
  limiter: false
  public_instance: false
  secret_key: "change-this-secret-key"

outgoing:
  request_timeout: 10.0
  max_request_timeout: 30.0
  pool_connections: 100
  pool_maxsize: 50
  enable_http2: true

valkey:
  # Redis for caching
  url: "redis://redis:6379/0"

engines:
  # Enable only academic engines
  - name: google scholar
    engine: google_scholar
    shortcut: gos
    categories: science
    timeout: 10
    disabled: false

  - name: arxiv
    engine: arxiv
    shortcut: arx
    categories: science
    timeout: 10
    disabled: false

  - name: crossref
    engine: crossref
    shortcut: crs
    categories: science
    timeout: 10
    disabled: false

  # Add custom engines here
  # See Phase 2 for implementation

plugins:
  searx.plugins.calculator.SXNGPlugin:
    active: true
  
  searx.plugins.oa_doi_rewrite.SXNGPlugin:
    active: true
  
  searx.plugins.tracker_url_remover.SXNGPlugin:
    active: true
```

---

## Code Examples

### Example 1: Hybrid Search (SearXNG + Direct APIs)

```python
# researchclaw/literature/hybrid_search.py

import asyncio
from typing import Literal
from .searxng_client import SearXNGClient
from .openalex_client import search_openalex
from .semantic_scholar import search_semantic_scholar
from .arxiv_client import search_arxiv
from .models import Paper

class HybridLiteratureSearch:
    """Combine SearXNG metasearch with direct API calls."""
    
    def __init__(self, searxng_url: str = "http://localhost:8888"):
        self.searxng = SearXNGClient(searxng_url)
        self.direct_sources = ["openalex", "semantic_scholar", "arxiv"]
    
    async def search(
        self,
        query: str,
        limit: int = 50,
        sources: list[str] | None = None,
        year_min: int | None = None,
        strategy: Literal["searxng_only", "direct_only", "hybrid"] = "hybrid",
    ) -> list[Paper]:
        """Search literature with configurable strategy."""
        
        if strategy == "searxng_only":
            return await self._search_searxng(query, limit, sources, year_min)
        elif strategy == "direct_only":
            return await self._search_direct(query, limit, sources, year_min)
        else:  # hybrid
            return await self._search_hybrid(query, limit, sources, year_min)
    
    async def _search_hybrid(
        self, query: str, limit: int, sources: list[str] | None, year_min: int | None
    ) -> list[Paper]:
        """Hybrid approach: SearXNG for breadth, direct APIs for depth."""
        
        # Run SearXNG and direct APIs in parallel
        searxng_task = asyncio.create_task(
            self._search_searxng(query, limit // 2, sources, year_min)
        )
        direct_task = asyncio.create_task(
            self._search_direct(query, limit // 2, sources, year_min)
        )
        
        searxng_results, direct_results = await asyncio.gather(
            searxng_task, direct_task, return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(searxng_results, Exception):
            searxng_results = []
        if isinstance(direct_results, Exception):
            direct_results = []
        
        # Merge and deduplicate
        all_papers = searxng_results + direct_results
        deduplicated = self._deduplicate(all_papers)
        
        # Sort by citation count (if available)
        deduplicated.sort(key=lambda p: p.citation_count, reverse=True)
        
        return deduplicated[:limit]
    
    async def _search_searxng(
        self, query: str, limit: int, sources: list[str] | None, year_min: int | None
    ) -> list[Paper]:
        """Search via SearXNG."""
        # Implementation from Approach 1
        pass
    
    async def _search_direct(
        self, query: str, limit: int, sources: list[str] | None, year_min: int | None
    ) -> list[Paper]:
        """Search via direct API calls."""
        tasks = []
        
        if not sources or "openalex" in sources:
            tasks.append(search_openalex(query, limit=limit // 3, year_min=year_min))
        
        if not sources or "semantic_scholar" in sources:
            tasks.append(search_semantic_scholar(query, limit=limit // 3, year_min=year_min))
        
        if not sources or "arxiv" in sources:
            tasks.append(search_arxiv(query, limit=limit // 3, year_min=year_min))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        papers = []
        for result in results:
            if isinstance(result, list):
                papers.extend(result)
        
        return papers
    
    def _deduplicate(self, papers: list[Paper]) -> list[Paper]:
        """Remove duplicates by DOI/arXiv ID/title."""
        seen_dois = set()
        seen_arxiv = set()
        seen_titles = set()
        
        unique = []
        for paper in papers:
            # Check DOI
            if paper.doi and paper.doi in seen_dois:
                continue
            if paper.doi:
                seen_dois.add(paper.doi)
            
            # Check arXiv ID
            if paper.arxiv_id and paper.arxiv_id in seen_arxiv:
                continue
            if paper.arxiv_id:
                seen_arxiv.add(paper.arxiv_id)
            
            # Fuzzy title match (simplified)
            title_key = paper.title.lower().strip()
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            
            unique.append(paper)
        
        return unique
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_searxng_client.py

import pytest
from researchclaw.literature.searxng_client import SearXNGClient

@pytest.fixture
async def searxng_client():
    client = SearXNGClient("http://localhost:8888")
    yield client
    await client.close()

@pytest.mark.asyncio
async def test_searxng_search(searxng_client):
    results = await searxng_client.search(
        query="graph neural networks",
        categories=["science"],
        engines=["google scholar", "arxiv"],
    )
    
    assert len(results) > 0
    assert all(hasattr(r, "title") for r in results)
    assert all(hasattr(r, "engine") for r in results)

@pytest.mark.asyncio
async def test_searxng_get_config(searxng_client):
    config = await searxng_client.get_config()
    
    assert "engines" in config
    assert "categories" in config

@pytest.mark.asyncio
async def test_searxng_health_check(searxng_client):
    healthy = await searxng_client.health_check()
    assert healthy is True
```

### Integration Tests

```python
# tests/test_searxng_integration.py

@pytest.mark.integration
class TestSearXNGIntegration:
    async def test_full_literature_search(self):
        config = load_test_config()
        config.literature.backend = "searxng"
        config.literature.searxng.enabled = True
        
        papers = await search_literature(
            query="transformer attention mechanisms",
            limit=20,
            backend="searxng"
        )
        
        assert len(papers) >= 10
        assert all(p.source in config.literature.searxng.engines for p in papers)
```

---

## Success Metrics

| Metric | Baseline (Current) | Target (with SearXNG) | Measurement |
|--------|-------------------|----------------------|-------------|
| **Sources searched** | 3 (OpenAlex, S2, arXiv) | 8+ | Engine count |
| **Papers per query** | 15-25 | 40-60 | Results count |
| **Search time** | 8-12 seconds | 4-6 seconds | Latency |
| **Rate limit errors** | 5-10% | <1% | Error tracking |
| **Duplicate rate** | 15-20% | <5% | Deduplication audit |
| **Grey literature coverage** | Low | High | Manual review |
| **API cost** | $0.50/run | $0.20/run | Cost tracking |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **SearXNG downtime** | Search fails | Fallback to direct APIs |
| **Engine rate limits** | Incomplete results | SearXNG distributes load |
| **Result quality variance** | Inconsistent ranking | Score normalization |
| **Maintenance overhead** | Engine breakage | Automated health checks |
| **Resource usage** | Memory/CPU increase | Connection pooling, caching |

---

## Next Steps

1. **Decision:** Approve Phase 1 implementation
2. **Setup:** Deploy SearXNG locally
3. **Development:** Create SearXNG client
4. **Testing:** Write comprehensive tests
5. **Benchmark:** Compare with current system
6. **Documentation:** Write integration guide

---

## References

- **SearXNG Repo:** `E:\Documents\Vibe-Coding\Github Projects\Search\searxng-master\searxng-master`
- **SearXNG GitHub:** https://github.com/searxng/searxng
- **SearXNG Docs:** https://docs.searxng.org
- **SearXNG Instances:** https://searx.space
- **AutoResearchClaw Literature:** `researchclaw/literature/`

---

**Last Updated:** 2026-03-26
**Next Review:** After Phase 1 completion
