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
    "__version__",
]
