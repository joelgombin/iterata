"""iterata - Learn from human corrections to improve ML models"""

__version__ = "0.1.0"

from .core import (
    Correction,
    CorrectionType,
    Explanation,
    ExplanationType,
    Pattern,
    IterataConfig,
    MarkdownStorage,
    CorrectionLogger,
)
from .analysis import PatternDetector, Statistics
from .skill import SkillGenerator
from .loop import CorrectionLoop
from .decorators import with_correction_tracking, track_corrections

__all__ = [
    "Correction",
    "CorrectionType",
    "Explanation",
    "ExplanationType",
    "Pattern",
    "IterataConfig",
    "MarkdownStorage",
    "CorrectionLogger",
    "PatternDetector",
    "Statistics",
    "SkillGenerator",
    "CorrectionLoop",
    "with_correction_tracking",
    "track_corrections",
    "__version__",
]
