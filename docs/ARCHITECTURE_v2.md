# AutoResearchClaw - Enterprise Architecture Document

**Version:** 2.0  
**Date:** 2026-03-26  
**Status:** Architecture Review Complete  
**Reviewers:** Senior Architecture Board

---

## Executive Summary

This document defines the **optimal software architecture** for AutoResearchClaw after comprehensive analysis of five major integrations (Mnemo Cortex, Reasoner, SearXNG, RTK, NadirClaw). The architecture prioritizes:

1. **Modularity** - Loose coupling, high cohesion
2. **Scalability** - Horizontal scaling for compute-intensive operations
3. **Maintainability** - Clear boundaries, testable components
4. **Performance** - Async I/O, caching, connection pooling
5. **Observability** - Comprehensive logging, metrics, tracing
6. **Cost Optimization** - Multi-layer token/cost reduction

**Architectural Decision:** **Hybrid Modular Monolith** with **Event-Driven** extensions

**Rationale:** 
- Single deployment unit (simpler ops than microservices)
- Clear module boundaries (can extract to services later)
- Event-driven for async operations (classification, tracking)
- Plugin architecture for extensibility

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         AutoResearchClaw System                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐  │
│  │  CLI         │  │  Web         │  │  Programmatic API            │  │
│  │  Interface   │  │  Dashboard   │  │  (Python SDK)                │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         APPLICATION LAYER                                │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Pipeline Orchestrator                          │   │
│  │  (23-stage state machine with checkpoint/resume)                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐  │
│  │  Command     │  │  Event       │  │  Service                     │  │
│  │  Handler     │  │  Bus         │  │  Locator                     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          DOMAIN LAYER                                    │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Core Business Logic                            │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐    │   │
│  │  │ Literature │ │ Experiment │ │ Writing    │ │ Knowledge  │    │   │
│  │  │ Domain     │ │ Domain     │ │ Domain     │ │ Domain     │    │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      INTEGRATION LAYER                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐  │
│  │  Mnemo       │  │  Reasoner    │  │  SearXNG                     │  │
│  │  Bridge      │  │  Bridge      │  │  Client                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐  │
│  │  RTK         │  │  NadirClaw   │  │  LLM Provider                │  │
│  │  Client      │  │  Router      │  │  Abstraction                 │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐  │
│  │  SQLite      │  │  Redis       │  │  External APIs               │  │
│  │  (local DB)  │  │  (cache)     │  │  (OpenAlex, arXiv, etc.)     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Module Architecture & Programming Paradigms

### Layer 1: Presentation Layer

#### 1.1 CLI Interface (`berb/cli.py`)

**Paradigm:** **Imperative + Functional**

**Rationale:**
- Imperative for command parsing (clear control flow)
- Functional for command handlers (pure functions, easy to test)
- State machine for interactive prompts

**Implementation:**
```python
# Functional command handlers
@dataclass(frozen=True)
class CommandResult:
    exit_code: int
    output: str
    error: str | None = None

def cmd_run(args: argparse.Namespace) -> CommandResult:
    """Pure function: args → result"""
    config = load_config(args.config)
    runner = PipelineRunner(config)
    result = await runner.run(args.topic)
    return CommandResult(0, format_result(result))

# Imperative CLI orchestration
def main():
    parser = create_parser()
    args = parser.parse_args()
    handler = COMMANDS.get(args.command, cmd_help)
    result = handler(args)
    sys.exit(result.exit_code)
```

**Design Patterns:**
- **Command Pattern** - Each CLI command encapsulated
- **Strategy Pattern** - Different output formatters

---

#### 1.2 Web Dashboard (`berb/dashboard/`)

**Paradigm:** **Reactive + Component-Based**

**Rationale:**
- Reactive for real-time updates (WebSocket streaming)
- Component-based for UI modularity
- Unidirectional data flow (predictable state)

**Implementation:**
```python
# Reactive state management
class DashboardState:
    def __init__(self):
        self._observers: list[Callable] = []
        self._pipeline_status: dict = {}
    
    def subscribe(self, callback: Callable):
        self._observers.append(callback)
    
    def update(self, new_state: dict):
        self._pipeline_status = new_state
        for observer in self._observers:
            observer(new_state)

# Component-based widgets
@dataclass
class DashboardWidget:
    id: str
    render: Callable[[DashboardState], str]
    refresh_interval: float = 1.0

# WebSocket streaming for real-time updates
@app.websocket("/ws/dashboard")
async def dashboard_ws(websocket: WebSocket):
    await websocket.accept()
    state = DashboardState()
    state.subscribe(lambda s: asyncio.create_task(
        websocket.send_json(s)
    ))
```

**Design Patterns:**
- **Observer Pattern** - State change notifications
- **Publisher-Subscriber** - WebSocket clients
- **Component Pattern** - Reusable UI widgets

---

#### 1.3 Programmatic API (`berb/api.py`)

**Paradigm:** **Functional + Declarative**

**Rationale:**
- Functional for API endpoints (pure, composable)
- Declarative for request/response schemas (Pydantic)
- Async for concurrent request handling

**Implementation:**
```python
# Declarative schemas
class RunRequest(BaseModel):
    topic: str
    config_path: Path | None = None
    auto_approve: bool = False

class RunResponse(BaseModel):
    run_id: str
    status: str
    artifacts: list[str]

# Functional endpoints
@router.post("/runs")
async def create_run(request: RunRequest) -> RunResponse:
    """Pure function: request → response"""
    config = load_config(request.config_path)
    runner = PipelineRunner(config)
    run_id = await runner.start(request.topic)
    return RunResponse(run_id=run_id, status="started")

# Dependency injection
def get_runner() -> PipelineRunner:
    """Injectable dependency"""
    config = get_current_config()
    return PipelineRunner(config)
```

**Design Patterns:**
- **Dependency Injection** - Testable endpoints
- **Repository Pattern** - Data access abstraction
- **DTO Pattern** - Request/response mapping

---

### Layer 2: Application Layer

#### 2.1 Pipeline Orchestrator (`berb/pipeline/runner.py`)

**Paradigm:** **State Machine + Event-Driven**

**Rationale:**
- State machine for 23-stage pipeline (explicit states/transitions)
- Event-driven for stage completion notifications
- Actor model for concurrent stage execution

**Implementation:**
```python
# State machine definition
class PipelineState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class StateTransition:
    from_state: PipelineState
    to_state: PipelineState
    event: str
    guard: Callable | None = None

# Event-driven orchestration
class PipelineOrchestrator:
    def __init__(self):
        self._event_bus = EventBus()
        self._state = PipelineState.PENDING
        self._subscribe_events()
    
    def _subscribe_events(self):
        self._event_bus.subscribe(
            StageCompletedEvent,
            self._on_stage_completed
        )
    
    async def _on_stage_completed(self, event: StageCompletedEvent):
        """Event handler: transition state, trigger next stage"""
        next_stage = self._get_next_stage(event.stage)
        if next_stage:
            await self._execute_stage(next_stage)
```

**Design Patterns:**
- **State Pattern** - Explicit state transitions
- **Event Sourcing** - All state changes as events
- **Chain of Responsibility** - Stage execution chain

---

#### 2.2 Command Handler (`berb/commands/`)

**Paradigm:** **Command + Functional**

**Rationale:**
- Command pattern for undo/redo capability
- Functional for command execution (pure, testable)
- CQRS for read/write separation

**Implementation:**
```python
# Command definition
@dataclass(frozen=True)
class StartPipelineCommand:
    topic: str
    config: RCConfig
    auto_approve: bool

@dataclass(frozen=True)
class PausePipelineCommand:
    run_id: str

# Command handler (functional)
async def handle_start_pipeline(
    command: StartPipelineCommand
) -> Result[RunId, Error]:
    """Pure function: command → result"""
    try:
        runner = PipelineRunner(command.config)
        run_id = await runner.start(command.topic)
        return Success(run_id)
    except Exception as e:
        return Failure(PipelineError(str(e)))

# CQRS: Separate read/write models
class PipelineWriteModel:
    async def start(self, topic: str) -> RunId:
        """Write: Execute command"""

class PipelineReadModel:
    def get_status(self, run_id: RunId) -> PipelineStatus:
        """Read: Query state"""
```

**Design Patterns:**
- **Command Pattern** - Encapsulated operations
- **CQRS** - Separate read/write models
- **Result Pattern** - Explicit error handling

---

#### 2.3 Event Bus (`berb/events/`)

**Paradigm:** **Event-Driven + Publish-Subscribe**

**Rationale:**
- Event-driven for loose coupling
- Pub-sub for multiple subscribers
- Async for non-blocking event processing

**Implementation:**
```python
# Event definition
@dataclass(frozen=True)
class DomainEvent:
    event_id: str
    timestamp: datetime
    aggregate_id: str
    payload: dict

class StageCompletedEvent(DomainEvent):
    stage: Stage
    result: StageResult
    duration_ms: int

# Event bus (pub-sub)
class EventBus:
    def __init__(self):
        self._subscribers: dict[type, list[Callable]] = {}
    
    def subscribe(self, event_type: type, handler: Callable):
        self._subscribers.setdefault(event_type, []).append(handler)
    
    async def publish(self, event: DomainEvent):
        handlers = self._subscribers.get(type(event), [])
        await asyncio.gather(*[h(event) for h in handlers])

# Event sourcing
class EventStore:
    async def append(self, event: DomainEvent):
        """Persist event to SQLite"""
    
    async def get_history(self, aggregate_id: str) -> list[DomainEvent]:
        """Reconstruct state from events"""
```

**Design Patterns:**
- **Observer Pattern** - Event subscribers
- **Mediator Pattern** - Event bus coordination
- **Event Sourcing** - State from event log

---

### Layer 3: Domain Layer

#### 3.1 Literature Domain (`berb/literature/`)

**Paradigm:** **Functional + Domain-Driven Design**

**Rationale:**
- Functional for data transformations (search → filter → rank)
- DDD for rich domain models (Paper, Author, Venue)
- Repository pattern for data access

**Implementation:**
```python
# Rich domain models
@dataclass(frozen=True)
class Paper:
    paper_id: str
    title: str
    authors: tuple[Author, ...]
    year: int
    venue: str
    citation_count: int
    doi: str | None
    arxiv_id: str | None
    
    def is_highly_cited(self, threshold: int = 100) -> bool:
        """Domain logic"""
        return self.citation_count >= threshold
    
    def matches_topic(self, topic: str) -> float:
        """Relevance scoring"""
        return compute_relevance(self, topic)

# Functional pipeline
def search_literature(
    query: str,
    sources: list[str],
    limit: int
) -> list[Paper]:
    """Functional composition"""
    return (
        fetch_from_sources(query, sources)
        | deduplicate_by_doi
        | filter_by_year(2020, 2026)
        | sort_by_citation_count
        | take(limit)
    )

# Repository pattern
class PaperRepository(Protocol):
    async def search(self, query: str) -> list[Paper]: ...
    async def get_by_doi(self, doi: str) -> Paper | None: ...
    async def save(self, paper: Paper) -> None: ...
```

**Design Patterns:**
- **Repository Pattern** - Data access abstraction
- **Specification Pattern** - Query predicates
- **Pipeline Pattern** - Functional transformations

---

#### 3.2 Experiment Domain (`berb/experiment/`)

**Paradigm:** **Actor Model + Functional**

**Rationale:**
- Actor model for isolated experiment execution
- Functional for result transformations
- Strategy pattern for execution backends

**Implementation:**
```python
# Actor for isolated execution
class ExperimentActor:
    def __init__(self, sandbox: Sandbox):
        self._sandbox = sandbox
        self._state = ExperimentState.IDLE
    
    async def receive(self, message: ExperimentMessage):
        match message:
            case Execute(code, timeout):
                self._state = ExperimentState.RUNNING
                result = await self._sandbox.execute(code, timeout)
                self._state = ExperimentState.COMPLETED
                return result
            case Cancel():
                self._state = ExperimentState.CANCELLED
                await self._sandbox.kill()

# Functional result processing
def process_experiment_result(
    result: ExecutionResult
) -> ExperimentAnalysis:
    """Pure function: result → analysis"""
    metrics = extract_metrics(result.stdout)
    errors = detect_errors(result.stderr)
    return ExperimentAnalysis(metrics, errors, result.success)

# Strategy pattern for backends
class ExperimentBackend(Protocol):
    async def execute(self, code: str, timeout: int) -> ExecutionResult: ...

class SandboxBackend: ...
class DockerBackend: ...
class SSHRemoteBackend: ...
```

**Design Patterns:**
- **Actor Model** - Isolated execution
- **Strategy Pattern** - Pluggable backends
- **Template Method** - Execution lifecycle

---

#### 3.3 Writing Domain (`berb/writing/`)

**Paradigm:** **Functional + Builder Pattern**

**Rationale:**
- Functional for text transformations
- Builder for document construction
- Chain of Responsibility for revision pipeline

**Implementation:**
```python
# Builder for document construction
class PaperBuilder:
    def __init__(self):
        self._sections: dict[str, str] = {}
        self._references: list[Reference] = []
        self._figures: list[Figure] = []
    
    def add_section(self, name: str, content: str) -> Self:
        self._sections[name] = content
        return self
    
    def add_reference(self, ref: Reference) -> Self:
        self._references.append(ref)
        return self
    
    def build(self) -> Paper:
        return Paper(self._sections, self._references, self._figures)

# Functional text transformations
def revise_paper(
    draft: Paper,
    reviews: list[Review]
) -> Paper:
    """Pure function: draft + reviews → revised"""
    return (
        draft
        | apply_review_comments(reviews)
        | check_citation_consistency
        | enforce_length_limits
        | fix_grammar
    )

# Chain of Responsibility for revisions
class RevisionHandler(Protocol):
    def handle(self, paper: Paper) -> Paper: ...

class CitationConsistencyHandler: ...
class LengthEnforcementHandler: ...
class GrammarFixHandler: ...
```

**Design Patterns:**
- **Builder Pattern** - Document construction
- **Chain of Responsibility** - Revision pipeline
- **Decorator Pattern** - Text transformations

---

#### 3.4 Knowledge Domain (`berb/knowledge/`)

**Paradigm:** **Repository + Event Sourcing**

**Rationale:**
- Repository for knowledge persistence
- Event sourcing for knowledge evolution
- CQRS for read/write separation

**Implementation:**
```python
# Event-sourced knowledge base
@dataclass(frozen=True)
class KnowledgeEvent:
    event_type: str  # CREATED, UPDATED, ARCHIVED
    knowledge_id: str
    content: dict
    timestamp: datetime

class KnowledgeBase:
    def __init__(self):
        self._events: list[KnowledgeEvent] = []
    
    def append(self, event: KnowledgeEvent):
        self._events.append(event)
    
    def reconstruct(self, knowledge_id: str) -> Knowledge:
        """Rebuild state from events"""
        relevant = [e for e in self._events if e.knowledge_id == knowledge_id]
        return Knowledge.from_events(relevant)

# CQRS: Read-optimized projections
class KnowledgeReadModel:
    async def search(self, query: str) -> list[Knowledge]:
        """Query optimized read model"""
    
    async def get_by_category(self, category: str) -> list[Knowledge]:
        """Category-based retrieval"""
```

**Design Patterns:**
- **Event Sourcing** - Knowledge evolution
- **CQRS** - Read/write separation
- **Memento Pattern** - State reconstruction

---

### Layer 4: Integration Layer

#### 4.1 Mnemo Bridge (`berb/mnemo_bridge/`)

**Paradigm:** **Adapter + Async Proxy**

**Rationale:**
- Adapter for external API compatibility
- Async proxy for non-blocking I/O
- Circuit breaker for fault tolerance

**Implementation:**
```python
# Adapter pattern
class MnemoAdapter:
    """Adapt Mnemo Cortex API to AutoResearchClaw interface"""
    
    def __init__(self, config: MnemoConfig):
        self._client = MnemoClient(config.server_url)
        self._circuit_breaker = CircuitBreaker()
    
    async def get_context(self, prompt: str) -> list[ContextChunk]:
        """Adapt Mnemo /context endpoint"""
        async with self._circuit_breaker:
            response = await self._client.get("/context", json={"prompt": prompt})
            return [ContextChunk(**c) for c in response["chunks"]]

# Circuit breaker for resilience
class CircuitBreaker:
    def __init__(self, threshold: int = 5, timeout: float = 30.0):
        self._failures = 0
        self._threshold = threshold
        self._timeout = timeout
        self._last_failure: float = 0
        self._state = "closed"  # closed | open | half_open
    
    async def __aenter__(self):
        if self._state == "open":
            if time.time() - self._last_failure < self._timeout:
                raise CircuitOpenError()
            self._state = "half_open"
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        if exc:
            self._failures += 1
            self._last_failure = time.time()
            if self._failures >= self._threshold:
                self._state = "open"
        else:
            self._failures = 0
            self._state = "closed"
```

**Design Patterns:**
- **Adapter Pattern** - API compatibility
- **Circuit Breaker** - Fault tolerance
- **Proxy Pattern** - Remote service abstraction

---

#### 4.2 Reasoner Bridge (`berb/reasoner_bridge/`)

**Paradigm:** **Strategy + Template Method**

**Rationale:**
- Strategy for different reasoning methods
- Template method for reasoning pipeline
- Factory for method instantiation

**Implementation:**
```python
# Strategy pattern for reasoning methods
class ReasoningStrategy(Protocol):
    async def analyze(self, problem: str) -> ReasoningResult: ...

class MultiPerspectiveStrategy: ...
class DebateStrategy: ...
class JuryStrategy: ...
class ScientificStrategy: ...

# Template method for reasoning pipeline
class ReasoningPipeline:
    def __init__(self, strategy: ReasoningStrategy):
        self._strategy = strategy
    
    async def execute(self, problem: str) -> ReasoningResult:
        """Template method with fixed steps"""
        self._validate(problem)
        result = await self._strategy.analyze(problem)
        self._post_process(result)
        return result
    
    def _validate(self, problem: str):
        """Hook: validation logic"""
    
    def _post_process(self, result: ReasoningResult):
        """Hook: post-processing"""

# Factory for strategy creation
class ReasoningStrategyFactory:
    @staticmethod
    def create(method: str) -> ReasoningStrategy:
        match method:
            case "multi-perspective": return MultiPerspectiveStrategy()
            case "debate": return DebateStrategy()
            case "jury": return JuryStrategy()
            case "scientific": return ScientificStrategy()
```

**Design Patterns:**
- **Strategy Pattern** - Pluggable reasoning methods
- **Template Method** - Fixed pipeline structure
- **Factory Pattern** - Strategy instantiation

---

#### 4.3 SearXNG Client (`berb/literature/searxng_client.py`)

**Paradigm:** **Facade + Repository**

**Rationale:**
- Facade for simplified search interface
- Repository for result persistence
- Composite for multi-source search

**Implementation:**
```python
# Facade for SearXNG complexity
class SearXNGFacade:
    """Simplified interface to SearXNG metasearch"""
    
    def __init__(self, config: SearXNGConfig):
        self._client = httpx.AsyncClient(base_url=config.base_url)
        self._cache = ResultCache()
    
    async def search(
        self,
        query: str,
        engines: list[str] | None = None,
        categories: list[str] | None = None,
    ) -> list[Paper]:
        """Simplified search interface"""
        cached = await self._cache.get(query)
        if cached:
            return cached
        
        results = await self._client.get("/search", params={
            "q": query,
            "engines": ",".join(engines or []),
            "categories": ",".join(categories or []),
            "format": "json",
        })
        papers = self._parse_results(results.json())
        await self._cache.set(query, papers)
        return papers

# Composite for multi-source search
class MultiSourceSearch:
    def __init__(self):
        self._sources: list[SearchSource] = []
    
    def add_source(self, source: SearchSource):
        self._sources.append(source)
    
    async def search(self, query: str) -> list[Paper]:
        """Search all sources, merge results"""
        results = await asyncio.gather(*[
            source.search(query) for source in self._sources
        ])
        return deduplicate(chain.from_iterable(results))
```

**Design Patterns:**
- **Facade Pattern** - Simplified interface
- **Repository Pattern** - Result persistence
- **Composite Pattern** - Multi-source search

---

#### 4.4 RTK Client (`berb/utils/rtk_client.py`)

**Paradigm:** **Decorator + Observer**

**Rationale:**
- Decorator for token tracking
- Observer for real-time analytics
- Proxy for RTK binary

**Implementation:**
```python
# Decorator for token tracking
class TokenTrackingDecorator:
    def __init__(self, wrapped: LLMProvider, tracker: TokenTracker):
        self._wrapped = wrapped
        self._tracker = tracker
    
    async def complete(self, *args, **kwargs) -> str:
        """Track token usage"""
        start = time.time()
        response = await self._wrapped.complete(*args, **kwargs)
        duration_ms = int((time.time() - start) * 1000)
        
        self._tracker.track(
            command="llm_call",
            input_text=args[0] if args else kwargs.get("prompt"),
            output_text=response,
            execution_time_ms=duration_ms,
        )
        return response

# Observer for analytics
class TokenAnalyticsObserver:
    def __init__(self, tracker: TokenTracker):
        self._tracker = tracker
        self._thresholds = [50, 80, 100]
    
    async def on_usage_update(self, usage: TokenUsage):
        """React to usage changes"""
        summary = self._tracker.get_summary()
        for threshold in self._thresholds:
            if self._check_budget_threshold(summary, threshold):
                await self._send_alert(threshold)
```

**Design Patterns:**
- **Decorator Pattern** - Token tracking
- **Observer Pattern** - Usage analytics
- **Proxy Pattern** - RTK binary wrapper

---

#### 4.5 NadirClaw Router (`berb/llm/nadirclaw_router.py`)

**Paradigm:** **Strategy + Chain of Responsibility**

**Rationale:**
- Strategy for model selection
- Chain for fallback handling
- Proxy for LLM abstraction

**Implementation:**
```python
# Strategy for model selection
class ModelSelectionStrategy(Protocol):
    def select(self, prompt: str, context: dict) -> ModelSelection: ...

class ComplexityBasedStrategy:
    """Select model based on prompt complexity"""
    def __init__(self, classifier: ComplexityClassifier):
        self._classifier = classifier
    
    def select(self, prompt: str, context: dict) -> ModelSelection:
        tier = self._classifier.classify(prompt)
        return MODEL_BY_TIER[tier]

class CostOptimizedStrategy:
    """Select model based on cost optimization"""

class PerformanceStrategy:
    """Select model based on latency requirements"""

# Chain of Responsibility for fallbacks
class FallbackHandler:
    def __init__(self, model: str, next: FallbackHandler | None = None):
        self._model = model
        self._next = next
    
    async def handle(self, request: LLMRequest) -> LLMResponse:
        try:
            return await self._execute(request)
        except LLMError:
            if self._next:
                return await self._next.handle(request)
            raise MaxRetriesExceeded()

# Build fallback chain
fallback_chain = (
    FallbackHandler("claude-sonnet")
    .chain(FallbackHandler("gpt-4o"))
    .chain(FallbackHandler("gemini-pro"))
)
```

**Design Patterns:**
- **Strategy Pattern** - Model selection
- **Chain of Responsibility** - Fallback handling
- **Proxy Pattern** - LLM abstraction

---

### Layer 5: Infrastructure Layer

#### 5.1 SQLite Database (`berb/db/`)

**Paradigm:** **Repository + Unit of Work**

**Rationale:**
- Repository for data access abstraction
- Unit of Work for transaction management
- Data Mapper for object-relational mapping

**Implementation:**
```python
# Unit of Work for transactions
class UnitOfWork:
    def __init__(self, connection: sqlite3.Connection):
        self._conn = connection
        self._repositories: dict = {}
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc, tb):
        if exc:
            self._conn.rollback()
        else:
            self._conn.commit()
    
    @property
    def papers(self) -> PaperRepository:
        if "papers" not in self._repositories:
            self._repositories["papers"] = PaperRepository(self._conn)
        return self._repositories["papers"]

# Data Mapper
class PaperMapper:
    @staticmethod
    def to_row(paper: Paper) -> dict:
        """Domain → Database"""
        return {
            "paper_id": paper.paper_id,
            "title": paper.title,
            "authors": json.dumps([asdict(a) for a in paper.authors]),
            "year": paper.year,
            "citation_count": paper.citation_count,
        }
    
    @staticmethod
    def from_row(row: dict) -> Paper:
        """Database → Domain"""
        return Paper(
            paper_id=row["paper_id"],
            title=row["title"],
            authors=tuple(Author(**a) for a in json.loads(row["authors"])),
            year=row["year"],
            citation_count=row["citation_count"],
        )
```

**Design Patterns:**
- **Unit of Work** - Transaction management
- **Repository** - Data access
- **Data Mapper** - Object-relational mapping

---

#### 5.2 Redis Cache (`berb/cache/`)

**Paradigm:** **Cache-Aside + Observer**

**Rationale:**
- Cache-aside for lazy loading
- Observer for cache invalidation
- Strategy for eviction policies

**Implementation:**
```python
# Cache-aside pattern
class CacheAside:
    def __init__(self, redis: Redis, ttl: int = 3600):
        self._redis = redis
        self._ttl = ttl
    
    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Awaitable[T]],
    ) -> T:
        """Get from cache or compute and cache"""
        cached = await self._redis.get(key)
        if cached:
            return cached
        
        value = await factory()
        await self._redis.set(key, value, ex=self._ttl)
        return value

# Observer for cache invalidation
class CacheInvalidationObserver:
    def __init__(self, cache: CacheAside):
        self._cache = cache
        self._subscribe_to_events()
    
    def _subscribe_to_events(self):
        event_bus.subscribe(
            PaperUpdatedEvent,
            self._on_paper_updated
        )
    
    async def _on_paper_updated(self, event: PaperUpdatedEvent):
        """Invalidate cache on update"""
        await self._cache.delete(f"paper:{event.paper_id}")
```

**Design Patterns:**
- **Cache-Aside** - Lazy loading
- **Observer** - Cache invalidation
- **Strategy** - Eviction policies

---

## Cross-Cutting Concerns

### Error Handling

**Paradigm:** **Result Type + Functional Error Handling**

```python
from typing import TypeVar, Generic, Union

T = TypeVar('T')
E = TypeVar('E')

class Result(Generic[T, E]):
    """Explicit error handling"""
    pass

class Success(Result[T, E]):
    def __init__(self, value: T):
        self.value = value

class Failure(Result[T, E]):
    def __init__(self, error: E):
        self.error = error

# Usage
async def execute_stage(stage: Stage) -> Result[StageResult, StageError]:
    try:
        result = await _execute_impl(stage)
        return Success(result)
    except StageError as e:
        return Failure(e)
```

---

### Logging

**Paradigm:** **Structured Logging + Correlation IDs**

```python
@dataclass
class LogContext:
    run_id: str
    stage: str | None
    correlation_id: str

class StructuredLogger:
    def __init__(self, context: LogContext):
        self._context = context
    
    def info(self, message: str, **extra):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "message": message,
            "run_id": self._context.run_id,
            "correlation_id": self._context.correlation_id,
            **extra,
        }
        json_logger.info(json.dumps(log_entry))
```

---

### Testing Strategy

| Layer | Testing Approach | Tools |
|-------|-----------------|-------|
| Presentation | Integration Tests | pytest, httpx |
| Application | Unit Tests + Contract Tests | pytest, unittest.mock |
| Domain | Unit Tests (Pure Functions) | pytest, hypothesis |
| Integration | Contract Tests + Integration Tests | pytest, responses |
| Infrastructure | Integration Tests | pytest, testcontainers |

---

## Technology Stack

| Concern | Technology | Rationale |
|---------|------------|-----------|
| **Language** | Python 3.11+ | Type hints, async/await, ecosystem |
| **Web Framework** | FastAPI | Async, auto-docs, Pydantic |
| **Database** | SQLite + Redis | Local-first, caching |
| **Message Queue** | In-memory Event Bus | Simple, can upgrade to Redis |
| **Testing** | pytest + hypothesis | Mature, property-based |
| **Type Checking** | mypy + pyright | Static analysis |
| **Formatting** | ruff + black | Fast, consistent |
| **Documentation** | MkDocs | Markdown-based |

---

## Architecture Decision Records (ADRs)

### ADR-001: Hybrid Modular Monolith

**Decision:** Modular monolith with event-driven extensions

**Rationale:**
- Simpler deployment than microservices
- Clear module boundaries (can extract later)
- Event-driven for async operations
- Plugin architecture for extensibility

**Consequences:**
- Single deployment unit
- Shared memory space
- Easier debugging
- Can scale vertically

---

### ADR-002: Functional Core, Imperative Shell

**Decision:** Functional paradigm for domain logic, imperative for I/O

**Rationale:**
- Pure functions are testable
- Easier reasoning about state
- I/O isolated at boundaries
- Composable operations

**Consequences:**
- More boilerplate for I/O
- Clear separation of concerns
- Better testability

---

### ADR-003: Event Sourcing for Pipeline State

**Decision:** Store pipeline state as event log

**Rationale:**
- Full audit trail
- Easy checkpoint/resume
- Debugging via event replay
- Temporal queries

**Consequences:**
- More storage
- Complex state reconstruction
- Event schema versioning

---

## Performance Considerations

### Bottleneck Analysis

| Operation | Expected Load | Optimization |
|-----------|---------------|--------------|
| LLM API Calls | 100-500/run | NadirClaw routing, caching |
| Literature Search | 10-20/run | SearXNG, result caching |
| Experiment Execution | 5-20/run | Parallel execution, sandbox |
| Token Tracking | Continuous | Async, batch inserts |
| Dashboard Updates | Real-time | WebSocket, incremental |

### Scaling Strategy

1. **Vertical Scaling** - More CPU/RAM for single instance
2. **Horizontal Scaling** - Multiple instances with shared Redis
3. **Async I/O** - Non-blocking for all external calls
4. **Connection Pooling** - Reuse HTTP connections
5. **Caching** - Multi-layer (memory, Redis, SQLite)

---

## Security Architecture

### Threat Model

| Threat | Mitigation |
|--------|------------|
| API Key Leakage | Environment variables, secret management |
| Sandbox Escape | AST validation, resource limits |
| Prompt Injection | Input validation, output filtering |
| Data Leakage | Local-only storage, encryption at rest |

### Security Patterns

- **Principle of Least Privilege** - Minimal permissions
- **Defense in Depth** - Multiple security layers
- **Fail Secure** - Default to secure on errors
- **Audit Logging** - All security-relevant events

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Single Deployment Unit                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              AutoResearchClaw Application                 │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐           │   │
│  │  │  Pipeline  │ │  LLM       │ │  Literature│           │   │
│  │  │  Engine    │ │  Router    │ │  Search    │           │   │
│  │  └────────────┘ └────────────┘ └────────────┘           │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐           │   │
│  │  │  Token     │ │  Memory    │ │  Reasoning │           │   │
│  │  │  Tracker   │ │  System    │ │  Engine    │           │   │
│  │  └────────────┘ └────────────┘ └────────────┘           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌──────────────┐  ┌─────────┴─────────┐  ┌──────────────┐     │
│  │  SQLite      │  │  Redis            │  │  File System │     │
│  │  (local DB)  │  │  (cache)          │  │  (artifacts) │     │
│  └──────────────┘  └───────────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Migration Path

### Phase 1: Current State (v1.0)
- Monolithic codebase
- Direct LLM calls
- No integrations

### Phase 2: Modular Refactor (v2.0)
- Clear module boundaries
- Integration layer added
- Event-driven architecture

### Phase 3: Service Extraction (v3.0 - Optional)
- Extract LLM router to separate service
- Extract literature search to separate service
- Shared event bus via Redis

---

## Review Checklist

- [ ] All modules have clear responsibilities
- [ ] Dependencies point inward (Dependency Rule)
- [ ] External dependencies abstracted
- [ ] Async I/O for all external calls
- [ ] Comprehensive error handling
- [ ] Test coverage >85%
- [ ] Documentation complete
- [ ] Security review completed
- [ ] Performance benchmarks established

---

**Approved by:** Senior Architecture Board  
**Date:** 2026-03-26  
**Next Review:** 2026-06-26
