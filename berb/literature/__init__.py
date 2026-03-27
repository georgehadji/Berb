"""Berb literature search and citation management.

Provides API clients for Semantic Scholar and arXiv, plus unified search
with deduplication and BibTeX generation.
"""

from .models import Author, Paper
from .search import search_papers
from .verify import (
    CitationResult,
    VerificationReport,
    VerifyStatus,
    verify_citations,
)

__all__ = [
    "Author",
    "CitationResult",
    "Paper",
    "VerificationReport",
    "VerifyStatus",
    "search_papers",
    "verify_citations",
]
