from typing import Optional, Dict, Any
from .models import Correction, Explanation, ExplanationType, CorrectionType
from .storage import MarkdownStorage


class CorrectionLogger:
    """API principale pour logger les corrections"""

    def __init__(
        self,
        base_path: str,
        explainer: Optional[Any] = None,  # BaseExplainer type hint causes circular import
        auto_explain: bool = False,
    ):
        self.storage = MarkdownStorage(base_path)
        self.explainer = explainer
        self.auto_explain = auto_explain

    def log(
        self,
        original: Any,
        corrected: Any,
        document_id: str,
        field_path: str = "unknown",
        context: Optional[Dict[str, Any]] = None,
        corrector_id: Optional[str] = None,
        confidence_before: Optional[float] = None,
        human_explanation: Optional[str] = None,
    ) -> Correction:
        """
        Log une correction.

        Args:
            original: Valeur originale extraite
            corrected: Valeur corrigée
            document_id: ID du document source
            field_path: Chemin du champ (ex: "invoice.total_amount")
            context: Contexte additionnel (modèle utilisé, type de doc, etc.)
            corrector_id: ID de la personne qui corrige
            confidence_before: Score de confiance avant correction
            human_explanation: Explication fournie par l'humain

        Returns:
            Correction object
        """
        correction = Correction(
            document_id=document_id,
            field_path=field_path,
            original_value=original,
            corrected_value=corrected,
            confidence_before=confidence_before,
            corrector_id=corrector_id,
            context=context or {},
        )

        # Sauvegarde la correction
        filepath = self.storage.save_correction(correction)

        # Explication automatique si configurée
        if self.auto_explain and self.explainer:
            if human_explanation:
                # Utilise l'explication humaine
                explanation = Explanation(
                    correction_id=correction.correction_id,
                    explanation_type=ExplanationType.HUMAN_PROVIDED,
                    category=self._categorize_from_text(human_explanation),
                    description=human_explanation,
                    explainer_id=corrector_id or "unknown",
                )
            else:
                # Demande au LLM d'expliquer
                explanation = self.explainer.explain(correction)

            self.storage.save_explanation(explanation, correction)

        return correction

    def explain_pending(self, correction_id: str, explanation_text: Optional[str] = None):
        """Ajoute une explication à une correction en attente"""
        # Charge la correction depuis inbox
        corrections = self.storage.load_corrections(status="inbox")
        correction = next((c for c in corrections if c.correction_id == correction_id), None)

        if not correction:
            raise ValueError(f"Correction {correction_id} not found in inbox")

        if explanation_text:
            # Explication fournie
            explanation = Explanation(
                correction_id=correction_id,
                explanation_type=ExplanationType.HUMAN_PROVIDED,
                category=self._categorize_from_text(explanation_text),
                description=explanation_text,
                explainer_id="human",
            )
        elif self.explainer:
            # LLM infère l'explication
            explanation = self.explainer.explain(correction)
        else:
            raise ValueError("No explainer configured and no explanation provided")

        self.storage.save_explanation(explanation, correction)

    def _categorize_from_text(self, text: str) -> CorrectionType:
        """Catégorise basiquement depuis le texte (à améliorer)"""
        text_lower = text.lower()
        if any(word in text_lower for word in ["format", "décimal", "séparateur"]):
            return CorrectionType.FORMAT_ERROR
        elif any(word in text_lower for word in ["règle", "métier", "business"]):
            return CorrectionType.BUSINESS_RULE
        else:
            return CorrectionType.OTHER
