"""Pipeline core — 23-stage research pipeline."""

from .hallucination_detector import (
    HallucinationDetector,
    HallucinationReport,
    CitationVerification,
    ClaimVerification,
    verify_paper_for_hallucinations,
)

__all__ = [
    "HallucinationDetector",
    "HallucinationReport",
    "CitationVerification",
    "ClaimVerification",
    "verify_paper_for_hallucinations",
]
