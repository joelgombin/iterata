from collections import Counter, defaultdict
from typing import List, Dict
from datetime import datetime
from ..core.models import Correction, Pattern, CorrectionType
from ..core.storage import MarkdownStorage


class PatternDetector:
    """Détecte les patterns récurrents dans les corrections"""

    def __init__(self, storage: MarkdownStorage):
        self.storage = storage

    def detect_patterns(self, min_occurrences: int = 3) -> List[Pattern]:
        """Identifie les patterns avec au moins N occurrences"""
        corrections = self.storage.load_corrections(status="explained")

        # Group par catégorie + sous-catégorie
        patterns_dict = defaultdict(list)

        for corr in corrections:
            category = corr.context.get("category", "unknown")
            subcategory = corr.context.get("subcategory", "")
            key = f"{category}_{subcategory}"
            patterns_dict[key].append(corr)

        patterns = []
        for key, corr_list in patterns_dict.items():
            if len(corr_list) >= min_occurrences:
                category_str = corr_list[0].context.get("category", "other")
                try:
                    category = CorrectionType(category_str)
                except ValueError:
                    category = CorrectionType.OTHER

                pattern = Pattern(
                    pattern_id=f"pattern_{key}",
                    category=category,
                    description=self._generate_pattern_description(corr_list),
                    frequency=len(corr_list),
                    first_seen=min(c.timestamp for c in corr_list),
                    last_seen=max(c.timestamp for c in corr_list),
                    correction_ids=[c.correction_id for c in corr_list],
                    impact=self._assess_impact(len(corr_list)),
                    automation_potential=self._assess_automation_potential(corr_list),
                )
                patterns.append(pattern)

        return patterns

    def detect_patterns_by_field(self, min_occurrences: int = 3) -> List[Pattern]:
        """
        Détecte les patterns en groupant par champ plutôt que par catégorie.
        Utile pour identifier les champs problématiques.
        """
        corrections = self.storage.load_corrections(status="explained")

        # Group par field_path
        field_patterns = defaultdict(list)

        for corr in corrections:
            field_patterns[corr.field_path].append(corr)

        patterns = []
        for field_path, corr_list in field_patterns.items():
            if len(corr_list) >= min_occurrences:
                # Déterminer la catégorie la plus fréquente pour ce champ
                categories = [
                    corr.context.get("category", "other") for corr in corr_list
                ]
                most_common_category = Counter(categories).most_common(1)[0][0]

                try:
                    category = CorrectionType(most_common_category)
                except ValueError:
                    category = CorrectionType.OTHER

                pattern = Pattern(
                    pattern_id=f"pattern_field_{field_path.replace('.', '_')}",
                    category=category,
                    description=f"Erreur récurrente sur le champ '{field_path}'",
                    frequency=len(corr_list),
                    first_seen=min(c.timestamp for c in corr_list),
                    last_seen=max(c.timestamp for c in corr_list),
                    correction_ids=[c.correction_id for c in corr_list],
                    impact=self._assess_impact(len(corr_list)),
                    automation_potential=self._assess_automation_potential(corr_list),
                )
                patterns.append(pattern)

        return patterns

    def detect_transformation_patterns(self, min_occurrences: int = 3) -> List[Dict]:
        """
        Détecte les transformations récurrentes (ex: "1,234" -> "1234").
        Retourne une liste de transformations avec leurs fréquences.
        """
        corrections = self.storage.load_corrections(status="explained")

        # Group par type de transformation
        transformations = defaultdict(list)

        for corr in corrections:
            # Créer une clé de transformation basée sur les types et patterns
            orig_type = type(corr.original_value).__name__
            corr_type = type(corr.corrected_value).__name__

            # Pour les strings, essayer de détecter le pattern
            if isinstance(corr.original_value, str) and isinstance(
                corr.corrected_value, str
            ):
                pattern_key = self._infer_transformation_pattern(
                    corr.original_value, corr.corrected_value
                )
            else:
                pattern_key = f"{orig_type}_to_{corr_type}"

            transformations[pattern_key].append(corr)

        # Filtrer par fréquence minimum
        result = []
        for pattern_key, corr_list in transformations.items():
            if len(corr_list) >= min_occurrences:
                result.append(
                    {
                        "pattern": pattern_key,
                        "frequency": len(corr_list),
                        "examples": [
                            {
                                "original": c.original_value,
                                "corrected": c.corrected_value,
                                "field": c.field_path,
                            }
                            for c in corr_list[:5]  # Limiter aux 5 premiers exemples
                        ],
                        "correction_ids": [c.correction_id for c in corr_list],
                    }
                )

        # Trier par fréquence
        result.sort(key=lambda x: x["frequency"], reverse=True)
        return result

    def _generate_pattern_description(self, corrections: List[Correction]) -> str:
        """Génère une description du pattern"""
        # Compte les champs les plus fréquents
        field_paths = Counter(c.field_path for c in corrections)
        most_common_field = field_paths.most_common(1)[0][0]

        # Récupère la description si disponible
        descriptions = [
            c.context.get("description", "") for c in corrections if c.context.get("description")
        ]

        if descriptions:
            # Prend la description la plus commune
            desc_counter = Counter(descriptions)
            most_common_desc = desc_counter.most_common(1)[0][0]
            return f"{most_common_desc} (champ: {most_common_field})"
        else:
            return f"Erreur récurrente sur le champ '{most_common_field}'"

    def _assess_impact(self, frequency: int) -> str:
        """Évalue l'impact d'un pattern"""
        if frequency >= 20:
            return "high"
        elif frequency >= 10:
            return "medium"
        else:
            return "low"

    def _assess_automation_potential(self, corrections: List[Correction]) -> float:
        """Évalue le potentiel d'automatisation (0-1)"""
        # Heuristique basée sur plusieurs facteurs

        # Facteur 1: Consistance des types
        orig_types = set(type(c.original_value).__name__ for c in corrections)
        corr_types = set(type(c.corrected_value).__name__ for c in corrections)

        type_consistency = 1.0 if len(orig_types) == 1 and len(corr_types) == 1 else 0.5

        # Facteur 2: Même champ
        fields = set(c.field_path for c in corrections)
        field_consistency = 1.0 if len(fields) == 1 else 0.5

        # Facteur 3: Transformations similaires
        if all(
            isinstance(c.original_value, str) and isinstance(c.corrected_value, str)
            for c in corrections
        ):
            # Pour les strings, vérifier si les transformations sont similaires
            patterns = set(
                self._infer_transformation_pattern(c.original_value, c.corrected_value)
                for c in corrections
            )
            transformation_consistency = 1.0 if len(patterns) == 1 else 0.3
        else:
            transformation_consistency = 0.5

        # Score final (moyenne pondérée)
        score = (
            type_consistency * 0.3
            + field_consistency * 0.3
            + transformation_consistency * 0.4
        )

        return round(score, 2)

    def _infer_transformation_pattern(self, original: str, corrected: str) -> str:
        """Infère le type de transformation entre deux strings"""
        # Détection de patterns simples
        # Important: tester les patterns spécifiques AVANT les patterns génériques

        # Pattern de séparateur décimal (virgule -> point)
        if "," in original and "." in corrected and original.replace(",", ".") == corrected:
            return "decimal_comma_to_dot"

        # Pattern de séparateur décimal (point -> virgule)
        if "." in original and "," in corrected and original.replace(".", ",") == corrected:
            return "decimal_dot_to_comma"

        # Suppression d'espaces
        if original.replace(" ", "") == corrected:
            return "remove_spaces"

        # Ajout d'espaces
        if corrected.replace(" ", "") == original:
            return "add_spaces"

        # Changement de casse (vérifier AVANT les remplacements génériques)
        if original.lower() == corrected.lower():
            if corrected.isupper():
                return "to_uppercase"
            elif corrected.islower():
                return "to_lowercase"
            elif corrected.istitle():
                return "to_titlecase"

        # Pattern de date
        if any(sep in original for sep in ["/", "-"]) and any(
            sep in corrected for sep in ["/", "-"]
        ):
            return "date_format_change"

        # Suppression de ponctuation
        if corrected.isalnum() and not original.isalnum():
            return "remove_punctuation"

        # Suppression de caractères (pattern générique)
        if len(corrected) < len(original) and all(c in original for c in corrected):
            removed = set(original) - set(corrected)
            return f"remove_chars_{','.join(sorted(removed))}"

        # Remplacement de caractères (pattern générique)
        if len(original) == len(corrected):
            diff_positions = sum(1 for o, c in zip(original, corrected) if o != c)
            if diff_positions == 1:
                return "single_char_replace"
            elif diff_positions <= 3:
                return "few_chars_replace"

        # Par défaut
        return "other_transformation"

    def get_pattern_summary(self) -> Dict:
        """Génère un résumé des patterns détectés"""
        patterns = self.detect_patterns(min_occurrences=1)
        field_patterns = self.detect_patterns_by_field(min_occurrences=1)
        transformations = self.detect_transformation_patterns(min_occurrences=1)

        # Statistiques par catégorie
        category_stats = Counter(p.category for p in patterns)

        # Top patterns par impact
        high_impact = [p for p in patterns if p.impact == "high"]
        medium_impact = [p for p in patterns if p.impact == "medium"]
        low_impact = [p for p in patterns if p.impact == "low"]

        # Patterns avec haut potentiel d'automatisation
        automatable = [p for p in patterns if p.automation_potential >= 0.7]

        return {
            "total_patterns": len(patterns),
            "patterns_by_category": dict(category_stats),
            "high_impact_count": len(high_impact),
            "medium_impact_count": len(medium_impact),
            "low_impact_count": len(low_impact),
            "highly_automatable_count": len(automatable),
            "field_patterns_count": len(field_patterns),
            "transformation_patterns_count": len(transformations),
            "top_patterns": sorted(patterns, key=lambda p: p.frequency, reverse=True)[:5],
            "most_automatable": sorted(
                patterns, key=lambda p: p.automation_potential, reverse=True
            )[:5],
        }
