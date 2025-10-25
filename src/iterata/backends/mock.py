from .base import BaseExplainer
from ..core.models import Correction, Explanation, ExplanationType, CorrectionType


class MockExplainer(BaseExplainer):
    """Mock explainer pour tests"""

    def explain(self, correction: Correction) -> Explanation:
        """Génère une explication mock"""
        return Explanation(
            correction_id=correction.correction_id,
            explanation_type=ExplanationType.LLM_INFERRED,
            category=CorrectionType.FORMAT_ERROR,
            description="Mock explanation for testing",
            explainer_id="mock",
            tags=["test"],
        )
