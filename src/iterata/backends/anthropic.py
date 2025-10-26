"""
Anthropic backend for Claude integration
"""

from typing import Optional
import json

from .base import BaseExplainer
from ..core.models import Correction, Explanation, ExplanationType, CorrectionType


class AnthropicExplainer(BaseExplainer):
    """Explainer utilisant l'API Claude d'Anthropic"""

    def __init__(
        self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-5-20250929"
    ):
        """
        Initialize Anthropic explainer.

        Args:
            api_key: Anthropic API key (if None, will use ANTHROPIC_API_KEY env var)
            model: Claude model to use
        """
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError(
                "anthropic package not installed. Install with: pip install iterata[anthropic]"
            )

        self.client = Anthropic(api_key=api_key)
        self.model = model

    def explain(self, correction: Correction) -> Explanation:
        """
        Génère une explication via Claude.

        Args:
            correction: The correction to explain

        Returns:
            Explanation with category, description, and confidence
        """
        prompt = self._build_prompt(correction)

        try:
            response = self.client.messages.create(
                model=self.model, max_tokens=1000, messages=[{"role": "user", "content": prompt}]
            )

            # Parse la réponse JSON
            result = json.loads(response.content[0].text)

            explanation = Explanation(
                correction_id=correction.correction_id,
                explanation_type=ExplanationType.LLM_INFERRED,
                category=CorrectionType(result["category"]),
                subcategory=result.get("subcategory"),
                description=result["description"],
                confidence=result.get("confidence"),
                explainer_id=self.model,
                tags=result.get("tags", []),
            )

            return explanation

        except json.JSONDecodeError as e:
            # Fallback si le JSON n'est pas valide
            return self._create_fallback_explanation(correction, str(e))

        except Exception as e:
            # Fallback en cas d'erreur API
            return self._create_fallback_explanation(correction, str(e))

    def _build_prompt(self, correction: Correction) -> str:
        """Construit le prompt pour Claude"""
        return f"""Analyse cette correction faite par un humain sur une extraction automatique.

Document : {correction.document_id}
Champ : {correction.field_path}
Valeur originale : {correction.original_value}
Valeur corrigée : {correction.corrected_value}

Contexte additionnel : {json.dumps(correction.context, ensure_ascii=False)}

Fournis une explication structurée de cette correction.

Catégories possibles :
- format_error : Erreur de format (décimal, date, etc.)
- business_rule : Violation d'une règle métier
- model_limitation : Limitation du modèle d'extraction
- context_missing : Contexte manquant
- ocr_error : Erreur d'OCR
- other : Autre raison

Réponds UNIQUEMENT avec un JSON valide suivant ce format exact :
{{
    "category": "format_error|business_rule|model_limitation|context_missing|ocr_error|other",
    "subcategory": "sous-catégorie spécifique si applicable, sinon null",
    "description": "Description claire et concise du problème (1-2 phrases)",
    "tags": ["tag1", "tag2"],
    "confidence": 0.95
}}

Ne réponds qu'avec le JSON, rien d'autre."""

    def _create_fallback_explanation(self, correction: Correction, error: str) -> Explanation:
        """Crée une explication de secours en cas d'erreur"""
        return Explanation(
            correction_id=correction.correction_id,
            explanation_type=ExplanationType.LLM_INFERRED,
            category=CorrectionType.OTHER,
            description=f"Automatic explanation failed: {error}. Manual review needed.",
            confidence=0.0,
            explainer_id=f"{self.model}_fallback",
            tags=["error", "needs_review"],
        )

    def explain_batch(self, corrections: list[Correction]) -> list[Explanation]:
        """
        Explique plusieurs corrections en batch (pour optimiser les appels API).

        Args:
            corrections: List of corrections to explain

        Returns:
            List of explanations
        """
        explanations = []
        for correction in corrections:
            explanation = self.explain(correction)
            explanations.append(explanation)

        return explanations
