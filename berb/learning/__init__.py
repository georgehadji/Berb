"""Cross-Project Learning module for Berb.

This module implements transfer learning from historical research runs,
enabling the system to provably improve over time.

Features:
- Model affinity per stage/domain
- Failure pattern prediction
- Literature source quality metrics
- Automatic insight injection
"""

from .cross_project_learning import (
    CrossProjectLearning,
    FailurePredictor,
    LiteratureSourceQuality,
    ModelAffinity,
    RunTrace,
    StageTrace,
)

__all__ = [
    "CrossProjectLearning",
    "ModelAffinity",
    "FailurePredictor",
    "LiteratureSourceQuality",
    "RunTrace",
    "StageTrace",
]
