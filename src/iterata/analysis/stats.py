from typing import Dict, Any, List
from collections import Counter
from datetime import datetime, timedelta
from ..core.storage import MarkdownStorage
from .pattern_detector import PatternDetector


class Statistics:
    """Calcule les statistiques sur les corrections"""

    def __init__(self, storage: MarkdownStorage):
        self.storage = storage
        self.pattern_detector = PatternDetector(storage)

    def compute(self) -> Dict[str, Any]:
        """Calcule toutes les statistiques"""
        corrections = self.storage.load_corrections(status="all")
        explained = self.storage.load_corrections(status="explained")
        patterns = self.pattern_detector.detect_patterns()

        # Statistiques par catégorie
        categories = Counter(c.context.get("category", "unknown") for c in explained)

        # Statistiques par champ
        fields = Counter(c.field_path for c in corrections)

        # Statistiques temporelles
        time_stats = self._compute_time_stats(corrections)

        return {
            "total_corrections": len(corrections),
            "corrections_explained": len(explained),
            "corrections_pending": len(corrections) - len(explained),
            "patterns_count": len(patterns),
            "correction_rate": len(explained) / len(corrections) if corrections else 0,
            "categories": dict(categories),
            "top_fields": dict(fields.most_common(10)),
            "time_stats": time_stats,
            "patterns": [p.model_dump() for p in patterns],
        }

    def compute_detailed(self) -> Dict[str, Any]:
        """Calcule des statistiques détaillées incluant les patterns et transformations"""
        corrections = self.storage.load_corrections(status="all")
        explained = self.storage.load_corrections(status="explained")
        inbox = self.storage.load_corrections(status="inbox")

        # Stats de base
        basic_stats = self.compute()

        # Pattern detection avancé
        patterns = self.pattern_detector.detect_patterns(min_occurrences=3)
        field_patterns = self.pattern_detector.detect_patterns_by_field(min_occurrences=3)
        transformations = self.pattern_detector.detect_transformation_patterns(
            min_occurrences=3
        )
        pattern_summary = self.pattern_detector.get_pattern_summary()

        # Stats par correcteur
        corrector_stats = self._compute_corrector_stats(corrections)

        # Stats de confiance
        confidence_stats = self._compute_confidence_stats(corrections)

        # Stats par document
        document_stats = self._compute_document_stats(corrections)

        return {
            **basic_stats,
            "field_patterns": [p.model_dump() for p in field_patterns],
            "transformation_patterns": transformations,
            "pattern_summary": pattern_summary,
            "corrector_stats": corrector_stats,
            "confidence_stats": confidence_stats,
            "document_stats": document_stats,
            "inbox_corrections": len(inbox),
        }

    def get_summary(self) -> str:
        """Génère un résumé textuel des statistiques"""
        stats = self.compute()

        summary = f"""
=== Iterata Statistics Summary ===

Total Corrections: {stats['total_corrections']}
  - Explained: {stats['corrections_explained']}
  - Pending: {stats['corrections_pending']}
  - Explanation Rate: {stats['correction_rate']:.1%}

Patterns Detected: {stats['patterns_count']}

Top Categories:
"""
        for category, count in sorted(
            stats["categories"].items(), key=lambda x: x[1], reverse=True
        ):
            summary += f"  - {category}: {count}\n"

        if stats["top_fields"]:
            summary += "\nTop Fields with Corrections:\n"
            for field, count in list(stats["top_fields"].items())[:5]:
                summary += f"  - {field}: {count}\n"

        if stats["time_stats"]["corrections_last_7_days"] > 0:
            summary += f"\nRecent Activity:\n"
            summary += (
                f"  - Last 7 days: {stats['time_stats']['corrections_last_7_days']}\n"
            )
            summary += (
                f"  - Last 30 days: {stats['time_stats']['corrections_last_30_days']}\n"
            )

        return summary

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """
        Génère des recommandations basées sur les patterns détectés.
        Utile pour identifier les actions prioritaires.
        """
        patterns = self.pattern_detector.detect_patterns(min_occurrences=3)
        transformations = self.pattern_detector.detect_transformation_patterns(
            min_occurrences=5
        )

        recommendations = []

        # Recommandations basées sur les patterns à fort impact
        high_impact = [p for p in patterns if p.impact == "high"]
        for pattern in high_impact:
            if pattern.automation_potential >= 0.7:
                recommendations.append(
                    {
                        "priority": "high",
                        "type": "automation",
                        "title": f"Automatiser: {pattern.description}",
                        "reason": f"Pattern à fort impact ({pattern.frequency} occurrences) avec haut potentiel d'automatisation ({pattern.automation_potential:.0%})",
                        "pattern_id": pattern.pattern_id,
                    }
                )
            else:
                recommendations.append(
                    {
                        "priority": "high",
                        "type": "investigation",
                        "title": f"Investiguer: {pattern.description}",
                        "reason": f"Pattern à fort impact ({pattern.frequency} occurrences) nécessite une analyse approfondie",
                        "pattern_id": pattern.pattern_id,
                    }
                )

        # Recommandations basées sur les transformations fréquentes
        for transfo in transformations[:3]:  # Top 3 transformations
            if transfo["frequency"] >= 10:
                recommendations.append(
                    {
                        "priority": "medium",
                        "type": "rule",
                        "title": f"Créer une règle: {transfo['pattern']}",
                        "reason": f"Transformation récurrente ({transfo['frequency']} fois)",
                        "examples": transfo["examples"][:3],
                    }
                )

        # Recommandation pour les corrections en attente
        inbox = self.storage.load_corrections(status="inbox")
        if len(inbox) > 10:
            recommendations.append(
                {
                    "priority": "medium",
                    "type": "action",
                    "title": "Expliquer les corrections en attente",
                    "reason": f"{len(inbox)} corrections attendent une explication",
                }
            )

        # Trier par priorité
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order[x["priority"]])

        return recommendations

    def _compute_time_stats(self, corrections: List) -> Dict[str, Any]:
        """Calcule les statistiques temporelles"""
        if not corrections:
            return {
                "first_correction": None,
                "last_correction": None,
                "corrections_last_7_days": 0,
                "corrections_last_30_days": 0,
            }

        now = datetime.utcnow()
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)

        corrections_7d = sum(1 for c in corrections if c.timestamp >= seven_days_ago)
        corrections_30d = sum(1 for c in corrections if c.timestamp >= thirty_days_ago)

        timestamps = [c.timestamp for c in corrections]

        return {
            "first_correction": min(timestamps).isoformat(),
            "last_correction": max(timestamps).isoformat(),
            "corrections_last_7_days": corrections_7d,
            "corrections_last_30_days": corrections_30d,
            "days_since_first": (now - min(timestamps)).days,
            "average_per_day": len(corrections) / max((now - min(timestamps)).days, 1),
        }

    def _compute_corrector_stats(self, corrections: List) -> Dict[str, Any]:
        """Calcule les statistiques par correcteur"""
        correctors = Counter(c.corrector_id for c in corrections if c.corrector_id)

        if not correctors:
            return {"total_correctors": 0, "corrections_by_corrector": {}}

        return {
            "total_correctors": len(correctors),
            "corrections_by_corrector": dict(correctors.most_common()),
            "most_active_corrector": correctors.most_common(1)[0]
            if correctors
            else None,
        }

    def _compute_confidence_stats(self, corrections: List) -> Dict[str, Any]:
        """Calcule les statistiques de confiance"""
        with_confidence = [c for c in corrections if c.confidence_before is not None]

        if not with_confidence:
            return {
                "corrections_with_confidence": 0,
                "average_confidence": None,
                "low_confidence_corrections": 0,
            }

        confidences = [c.confidence_before for c in with_confidence]
        avg_confidence = sum(confidences) / len(confidences)
        low_confidence = sum(1 for conf in confidences if conf < 0.5)

        return {
            "corrections_with_confidence": len(with_confidence),
            "average_confidence": round(avg_confidence, 3),
            "min_confidence": min(confidences),
            "max_confidence": max(confidences),
            "low_confidence_corrections": low_confidence,
            "low_confidence_rate": low_confidence / len(with_confidence),
        }

    def _compute_document_stats(self, corrections: List) -> Dict[str, Any]:
        """Calcule les statistiques par document"""
        documents = Counter(c.document_id for c in corrections)

        return {
            "total_documents": len(documents),
            "corrections_per_document": dict(documents.most_common(10)),
            "average_corrections_per_doc": (
                sum(documents.values()) / len(documents) if documents else 0
            ),
            "documents_with_most_corrections": documents.most_common(5),
        }

    def export_stats_json(self) -> str:
        """Exporte les statistiques en JSON"""
        import json

        stats = self.compute_detailed()
        return json.dumps(stats, indent=2, default=str)

    def export_stats_csv(self) -> str:
        """Exporte un résumé des corrections en CSV"""
        import csv
        import io

        corrections = self.storage.load_corrections(status="all")

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "correction_id",
                "timestamp",
                "document_id",
                "field_path",
                "original_value",
                "corrected_value",
                "category",
                "corrector_id",
            ],
        )

        writer.writeheader()
        for c in corrections:
            writer.writerow(
                {
                    "correction_id": c.correction_id,
                    "timestamp": c.timestamp.isoformat(),
                    "document_id": c.document_id,
                    "field_path": c.field_path,
                    "original_value": c.original_value,
                    "corrected_value": c.corrected_value,
                    "category": c.context.get("category", ""),
                    "corrector_id": c.corrector_id or "",
                }
            )

        return output.getvalue()
