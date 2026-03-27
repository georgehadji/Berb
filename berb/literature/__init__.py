"""Berb literature search and citation management."""

from .models import Author, Paper
from .search import search_papers
from .verify import (
    CitationResult,
    VerificationReport,
    VerifyStatus,
    verify_citations,
)
from .multimodal_search import (
    MultimodalLiteratureAgent,
    MultimodalPaper,
    FigureAnalysis,
    ExtractedChartData,
    ExtractedTableData,
    analyze_paper_multimodal,
)

__all__ = [
    "Author",
    "CitationResult",
    "Paper",
    "VerificationReport",
    "VerifyStatus",
    "search_papers",
    "verify_citations",
    "MultimodalLiteratureAgent",
    "MultimodalPaper",
    "FigureAnalysis",
    "ExtractedChartData",
    "ExtractedTableData",
    "analyze_paper_multimodal",
]
