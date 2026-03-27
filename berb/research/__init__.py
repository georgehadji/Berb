"""Research exploration module for Berb.

Parallelized agentic tree search for exploring multiple research directions.
Open-ended discovery for template-free exploration.
"""

from .tree_search import (
    ParallelizedTreeSearch,
    SearchConfig,
    SearchPath,
    BranchNode,
    BranchStatus,
    DecisionPoint,
    explore_research_space,
)
from .idea_scorer import (
    IdeaQualityScorer,
    ScoringConfig,
    ResearchIdea,
    ScoredIdea,
    NoveltyLevel,
    score_and_rank_ideas,
)
from .open_ended_discovery import (
    OpenEndedDiscoveryAgent,
    DiscoveryNode,
    DiscoveryResult,
    NodeStatus,
    ExperimentManagerAgent,
    NoveltyVerifier,
    run_open_ended_discovery,
)

__all__ = [
    "ParallelizedTreeSearch",
    "SearchConfig",
    "SearchPath",
    "BranchNode",
    "BranchStatus",
    "DecisionPoint",
    "explore_research_space",
    "IdeaQualityScorer",
    "ScoringConfig",
    "ResearchIdea",
    "ScoredIdea",
    "NoveltyLevel",
    "score_and_rank_ideas",
    "OpenEndedDiscoveryAgent",
    "DiscoveryNode",
    "DiscoveryResult",
    "NodeStatus",
    "ExperimentManagerAgent",
    "NoveltyVerifier",
    "run_open_ended_discovery",
]
