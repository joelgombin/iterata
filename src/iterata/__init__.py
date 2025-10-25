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

__all__ = [
    "Correction",
    "CorrectionType",
    "Explanation",
    "ExplanationType",
    "Pattern",
    "IterataConfig",
    "MarkdownStorage",
    "CorrectionLogger",
    "__version__",
]
