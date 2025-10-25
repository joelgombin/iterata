from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from ..core.models import Pattern, Correction
from ..core.storage import MarkdownStorage
from ..analysis.pattern_detector import PatternDetector


class SkillGenerator:
    """Génère des Claude Skills depuis les patterns détectés"""

    def __init__(self, storage: MarkdownStorage):
        self.storage = storage
        self.pattern_detector = PatternDetector(storage)

    def generate_skill(
        self,
        skill_path: str,
        skill_name: str = "extraction-expertise",
        min_corrections: int = 10,
        min_pattern_occurrences: int = 3,
    ) -> Path:
        """
        Génère une skill complète.

        Args:
            skill_path: Chemin où créer la skill
            skill_name: Nom de la skill
            min_corrections: Nombre minimum de corrections avant génération
            min_pattern_occurrences: Nombre minimum d'occurrences pour un pattern

        Returns:
            Path vers le SKILL.md généré
        """
        corrections = self.storage.load_corrections(status="explained")

        if len(corrections) < min_corrections:
            raise ValueError(
                f"Pas assez de corrections ({len(corrections)} < {min_corrections})"
            )

        # Détecte les patterns
        patterns = self.pattern_detector.detect_patterns(
            min_occurrences=min_pattern_occurrences
        )
        field_patterns = self.pattern_detector.detect_patterns_by_field(
            min_occurrences=min_pattern_occurrences
        )
        transformations = self.pattern_detector.detect_transformation_patterns(
            min_occurrences=min_pattern_occurrences
        )

        # Crée la structure
        skill_dir = Path(skill_path)
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "rules").mkdir(exist_ok=True)
        (skill_dir / "examples").mkdir(exist_ok=True)
        (skill_dir / "scripts").mkdir(exist_ok=True)

        # Génère SKILL.md
        skill_content = self._generate_skill_md(
            skill_name, corrections, patterns, field_patterns, transformations
        )

        skill_file = skill_dir / "SKILL.md"
        with open(skill_file, "w", encoding="utf-8") as f:
            f.write(skill_content)

        # Génère les règles métier
        self._generate_rules(skill_dir, patterns, corrections)

        # Génère des exemples
        self._generate_examples(skill_dir, corrections, patterns)

        # Génère un script de validation
        self._generate_validation_script(skill_dir, transformations)

        # Génère un README
        self._generate_readme(skill_dir, skill_name, corrections, patterns)

        return skill_file

    def _generate_skill_md(
        self,
        name: str,
        corrections: List[Correction],
        patterns: List[Pattern],
        field_patterns: List[Pattern],
        transformations: List[Dict[str, Any]],
    ) -> str:
        """Génère le contenu du SKILL.md"""
        from .templates import SkillTemplate

        # Trie les patterns par impact et fréquence
        top_patterns = sorted(
            patterns, key=lambda p: (self._impact_score(p.impact), p.frequency), reverse=True
        )[:10]

        # Identifie les patterns hautement automatisables
        automatable = [p for p in patterns if p.automation_potential >= 0.7]

        # Identifie les champs problématiques
        problematic_fields = sorted(field_patterns, key=lambda p: p.frequency, reverse=True)[
            :5
        ]

        # Top transformations
        top_transformations = transformations[:5]

        template = SkillTemplate()
        return template.generate_skill_md(
            name=name,
            total_corrections=len(corrections),
            pattern_count=len(patterns),
            top_patterns=top_patterns,
            automatable_patterns=automatable,
            problematic_fields=problematic_fields,
            transformations=top_transformations,
        )

    def _generate_rules(
        self, skill_dir: Path, patterns: List[Pattern], corrections: List[Correction]
    ):
        """Génère les règles métier"""
        from .templates import RuleTemplate

        rules_dir = skill_dir / "rules"

        # Groupe les corrections par catégorie pour créer des règles
        from collections import defaultdict

        corrections_by_category = defaultdict(list)
        for corr in corrections:
            category = corr.context.get("category", "other")
            corrections_by_category[category].append(corr)

        template = RuleTemplate()

        # Génère une règle par catégorie majeure
        for category, corr_list in corrections_by_category.items():
            if len(corr_list) >= 3:  # Au moins 3 corrections pour justifier une règle
                # Trouve les patterns associés
                related_patterns = [
                    p for p in patterns if p.category.value == category and p.frequency >= 3
                ]

                if related_patterns:
                    rule_content = template.generate_rule(
                        category=category, corrections=corr_list, patterns=related_patterns
                    )

                    rule_file = rules_dir / f"{category.replace('_', '-')}.md"
                    with open(rule_file, "w", encoding="utf-8") as f:
                        f.write(rule_content)

    def _generate_examples(
        self, skill_dir: Path, corrections: List[Correction], patterns: List[Pattern]
    ):
        """Génère des exemples JSON pour few-shot learning"""
        from .templates import ExampleTemplate

        examples_dir = skill_dir / "examples"

        # Prend les corrections les plus récentes et représentatives
        recent = sorted(corrections, key=lambda c: c.timestamp, reverse=True)[:20]

        # Groupe les exemples par pattern si possible
        examples_by_pattern = {}
        for pattern in patterns[:5]:  # Top 5 patterns
            pattern_corrections = [
                c for c in corrections if c.correction_id in pattern.correction_ids
            ]
            if pattern_corrections:
                examples_by_pattern[pattern.pattern_id] = pattern_corrections[:3]

        template = ExampleTemplate()

        # Génère corrections.json (exemples généraux)
        general_examples = template.generate_correction_examples(recent)
        with open(examples_dir / "corrections.json", "w", encoding="utf-8") as f:
            json.dump(general_examples, f, indent=2, ensure_ascii=False)

        # Génère patterns.json (exemples par pattern)
        pattern_examples = template.generate_pattern_examples(examples_by_pattern, patterns)
        with open(examples_dir / "patterns.json", "w", encoding="utf-8") as f:
            json.dump(pattern_examples, f, indent=2, ensure_ascii=False)

    def _generate_validation_script(self, skill_dir: Path, transformations: List[Dict]):
        """Génère un script Python de validation"""
        from .templates import ValidationScriptTemplate

        scripts_dir = skill_dir / "scripts"

        template = ValidationScriptTemplate()
        script_content = template.generate_validation_script(transformations)

        script_file = scripts_dir / "validate_extraction.py"
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(script_content)

        # Rend le script exécutable
        script_file.chmod(0o755)

    def _generate_readme(
        self,
        skill_dir: Path,
        skill_name: str,
        corrections: List[Correction],
        patterns: List[Pattern],
    ):
        """Génère un README pour la skill"""
        from .templates import ReadmeTemplate

        template = ReadmeTemplate()
        readme_content = template.generate_readme(
            skill_name=skill_name,
            total_corrections=len(corrections),
            pattern_count=len(patterns),
            high_impact_count=len([p for p in patterns if p.impact == "high"]),
            automatable_count=len([p for p in patterns if p.automation_potential >= 0.7]),
        )

        readme_file = skill_dir / "README.md"
        with open(readme_file, "w", encoding="utf-8") as f:
            f.write(readme_content)

    def _impact_score(self, impact: str) -> int:
        """Convertit l'impact en score numérique"""
        return {"high": 3, "medium": 2, "low": 1}.get(impact, 0)

    def can_generate_skill(self, min_corrections: int = 10) -> Dict[str, Any]:
        """
        Vérifie si assez de données pour générer une skill.

        Returns:
            Dict avec 'ready', 'corrections_count', 'patterns_count', 'reason'
        """
        corrections = self.storage.load_corrections(status="explained")
        patterns = self.pattern_detector.detect_patterns(min_occurrences=3)

        ready = len(corrections) >= min_corrections and len(patterns) > 0

        return {
            "ready": ready,
            "corrections_count": len(corrections),
            "patterns_count": len(patterns),
            "min_required": min_corrections,
            "reason": (
                "Ready to generate skill"
                if ready
                else f"Need {min_corrections - len(corrections)} more corrections"
                if len(corrections) < min_corrections
                else "No patterns detected"
            ),
        }
