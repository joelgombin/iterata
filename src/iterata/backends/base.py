from abc import ABC, abstractmethod
from ..core.models import Correction, Explanation


class BaseExplainer(ABC):
    """Interface abstraite pour les explainers"""

    @abstractmethod
    def explain(self, correction: Correction) -> Explanation:
        """Génère une explication pour une correction"""
        pass
