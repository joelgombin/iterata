"""
CorrectionLoop - API principale unifiant tous les composants
"""

from pathlib import Path
from typing import Optional, Dict, Any
import yaml

from .core.logger import CorrectionLogger
from .core.storage import MarkdownStorage
from .skill.generator import SkillGenerator
from .analysis.stats import Statistics
from .backends.base import BaseExplainer


class CorrectionLoop:
    """API principale - point d'entrée unique pour la librairie iterata"""

    def __init__(
        self,
        base_path: str,
        skill_path: Optional[str] = None,
        explainer: Optional[BaseExplainer] = None,
        auto_explain: bool = False,
        min_corrections_for_skill: int = 10,
    ):
        """
        Initialize CorrectionLoop.

        Args:
            base_path: Base directory for storing corrections
            skill_path: Path where to generate skills (optional)
            explainer: Explainer instance for auto-explanation (optional)
            auto_explain: Enable automatic explanation (requires explainer)
            min_corrections_for_skill: Minimum corrections before skill generation
        """
        self.base_path = Path(base_path)
        self.skill_path = Path(skill_path) if skill_path else None
        self.min_corrections_for_skill = min_corrections_for_skill

        # Initialise les composants
        self.storage = MarkdownStorage(str(self.base_path))
        self.logger = CorrectionLogger(
            str(self.base_path), explainer=explainer, auto_explain=auto_explain
        )
        self.skill_generator = SkillGenerator(self.storage)
        self.stats = Statistics(self.storage)

    @classmethod
    def from_config(cls, config_path: str) -> "CorrectionLoop":
        """
        Initialise depuis un fichier YAML.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            CorrectionLoop instance

        Example config.yaml:
            base_path: ./corrections
            skill_path: ./my-skill
            auto_explain: true
            min_corrections_for_skill: 25
            backend:
              provider: anthropic
              api_key: ${ANTHROPIC_API_KEY}
              model: claude-sonnet-4-5-20250929
        """
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Charge le backend si configuré
        explainer = None
        if config.get("backend"):
            backend_type = config["backend"]["provider"]

            if backend_type == "anthropic":
                from .backends.anthropic import AnthropicExplainer

                api_key = config["backend"].get("api_key")
                # Support ${ENV_VAR} syntax
                if api_key and api_key.startswith("${") and api_key.endswith("}"):
                    import os

                    env_var = api_key[2:-1]
                    api_key = os.getenv(env_var)

                explainer = AnthropicExplainer(
                    api_key=api_key, model=config["backend"].get("model", "claude-sonnet-4-5-20250929")
                )

            elif backend_type == "mock":
                from .backends.mock import MockExplainer

                explainer = MockExplainer()

        return cls(
            base_path=config["base_path"],
            skill_path=config.get("skill_path"),
            explainer=explainer,
            auto_explain=config.get("auto_explain", False),
            min_corrections_for_skill=config.get("min_corrections_for_skill", 10),
        )

    def log(self, original: Any, corrected: Any, document_id: str, **kwargs):
        """
        Log a correction (proxy to logger.log()).

        Args:
            original: Original extracted value
            corrected: Corrected value
            document_id: Document identifier
            **kwargs: Additional arguments (field_path, context, etc.)

        Returns:
            Correction object
        """
        return self.logger.log(
            original=original, corrected=corrected, document_id=document_id, **kwargs
        )

    def update_skill(
        self, force: bool = False, skill_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Met à jour la skill si assez de nouvelles corrections.

        Args:
            force: Force la mise à jour même si pas assez de corrections
            skill_name: Custom skill name (default: "extraction-expertise")

        Returns:
            Dict avec les stats de la mise à jour
        """
        if not self.skill_path:
            raise ValueError("No skill_path configured. Set it in __init__ or config file.")

        corrections = self.storage.load_corrections(status="explained")

        if len(corrections) < self.min_corrections_for_skill and not force:
            return {
                "updated": False,
                "reason": f"Not enough corrections ({len(corrections)} < {self.min_corrections_for_skill})",
                "corrections_count": len(corrections),
            }

        # Génère la skill
        skill_name = skill_name or "extraction-expertise"
        skill_file = self.skill_generator.generate_skill(
            skill_path=str(self.skill_path),
            skill_name=skill_name,
            min_corrections=self.min_corrections_for_skill if not force else 0,
        )

        # Calcule les stats
        stats = self.stats.compute()

        return {
            "updated": True,
            "skill_file": str(skill_file),
            "skill_name": skill_name,
            "total_corrections": len(corrections),
            "patterns_detected": stats["patterns_count"],
            "correction_rate": stats["correction_rate"],
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques actuelles.

        Returns:
            Statistics dictionary
        """
        return self.stats.compute()

    def get_detailed_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques détaillées.

        Returns:
            Detailed statistics dictionary
        """
        return self.stats.compute_detailed()

    def get_summary(self) -> str:
        """
        Retourne un résumé textuel des statistiques.

        Returns:
            Text summary
        """
        return self.stats.get_summary()

    def get_recommendations(self) -> list[Dict[str, Any]]:
        """
        Génère des recommandations basées sur les patterns.

        Returns:
            List of recommendations
        """
        return self.stats.get_recommendations()

    def check_skill_readiness(self) -> Dict[str, Any]:
        """
        Vérifie si assez de données pour générer une skill.

        Returns:
            Readiness status dict
        """
        return self.skill_generator.can_generate_skill(min_corrections=self.min_corrections_for_skill)

    def export_stats_json(self) -> str:
        """Export statistics as JSON string"""
        return self.stats.export_stats_json()

    def export_stats_csv(self) -> str:
        """Export corrections as CSV string"""
        return self.stats.export_stats_csv()
