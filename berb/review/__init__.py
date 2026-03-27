"""Automated peer review for Berb papers.

Implements 5-reviewer ensemble + Area Chair meta-review
based on AI Scientist (Nature 2026).
"""

from .ensemble import (
    AutomatedReviewerEnsemble,
    Decision,
    MetaReview,
    Review,
    ReviewDimension,
    ReviewerPersona,
    review_paper,
)

__all__ = [
    "AutomatedReviewerEnsemble",
    "Decision",
    "MetaReview",
    "Review",
    "ReviewDimension",
    "ReviewerPersona",
    "review_paper",
]
