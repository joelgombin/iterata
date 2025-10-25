from pathlib import Path
import frontmatter
from typing import List, Optional
from .models import Correction, Explanation, Pattern


class MarkdownStorage:
    """Gère le stockage en markdown avec frontmatter YAML"""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self._init_directories()

    def _init_directories(self):
        """Crée la structure de répertoires"""
        dirs = [
            "inbox",
            "explained/format_errors",
            "explained/business_rules",
            "explained/model_limitations",
            "explained/context_missing",
            "explained/ocr_errors",
            "explained/other",
            "patterns",
            "rules",
            "meta",
        ]
        for dir_name in dirs:
            (self.base_path / dir_name).mkdir(parents=True, exist_ok=True)

    def save_correction(self, correction: Correction) -> Path:
        """Sauvegarde une correction dans inbox/"""
        content = self._generate_correction_markdown(correction)

        post = frontmatter.Post(content)
        post.metadata = correction.model_dump(exclude={"context"})
        # Convert datetime to ISO string for YAML serialization
        post.metadata["timestamp"] = correction.timestamp.isoformat()
        post.metadata.update(correction.context)

        filepath = self.base_path / "inbox" / f"{correction.correction_id}.md"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        return filepath

    def save_explanation(self, explanation: Explanation, correction: Correction):
        """Sauvegarde une explication et déplace la correction vers explained/"""
        # Charge la correction existante
        correction_path = self.base_path / "inbox" / f"{correction.correction_id}.md"
        post = frontmatter.load(correction_path)

        # Ajoute l'explication au contenu
        explanation_content = self._generate_explanation_markdown(explanation)
        post.content += "\n\n" + explanation_content

        # Met à jour les métadonnées
        post.metadata["status"] = "explained"
        post.metadata["explanation_type"] = explanation.explanation_type.value
        post.metadata["category"] = explanation.category.value
        post.metadata["tags"] = explanation.tags

        # Déplace vers le bon sous-répertoire
        category_dir = explanation.category.replace("_", "_")
        if explanation.category == "format_error":
            category_dir = "format_errors"
        elif explanation.category == "business_rule":
            category_dir = "business_rules"
        elif explanation.category == "model_limitation":
            category_dir = "model_limitations"
        elif explanation.category == "context_missing":
            category_dir = "context_missing"
        elif explanation.category == "ocr_error":
            category_dir = "ocr_errors"
        else:
            category_dir = "other"

        new_path = self.base_path / "explained" / category_dir / f"{correction.correction_id}.md"

        with open(new_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        # Supprime de inbox
        correction_path.unlink()

        return new_path

    def load_corrections(self, status: str = "all") -> List[Correction]:
        """Charge toutes les corrections"""
        corrections = []

        if status == "all" or status == "inbox":
            inbox_path = self.base_path / "inbox"
            if inbox_path.exists():
                for file in inbox_path.glob("*.md"):
                    post = frontmatter.load(file)
                    # Rebuild correction from metadata
                    corrections.append(self._correction_from_metadata(post.metadata))

        if status == "all" or status == "explained":
            explained_path = self.base_path / "explained"
            if explained_path.exists():
                for file in explained_path.rglob("*.md"):
                    post = frontmatter.load(file)
                    corrections.append(self._correction_from_metadata(post.metadata))

        return corrections

    def _correction_from_metadata(self, metadata: dict) -> Correction:
        """Reconstruit un objet Correction depuis les métadonnées"""
        # Extract context fields (everything that's not a Correction field)
        correction_fields = {
            "correction_id",
            "timestamp",
            "document_id",
            "field_path",
            "original_value",
            "corrected_value",
            "confidence_before",
            "corrector_id",
        }

        context = {k: v for k, v in metadata.items() if k not in correction_fields}

        # Build correction dict
        corr_dict = {
            "correction_id": metadata.get("correction_id"),
            "timestamp": metadata.get("timestamp"),
            "document_id": metadata.get("document_id"),
            "field_path": metadata.get("field_path"),
            "original_value": metadata.get("original_value"),
            "corrected_value": metadata.get("corrected_value"),
            "confidence_before": metadata.get("confidence_before"),
            "corrector_id": metadata.get("corrector_id"),
            "context": context,
        }

        return Correction(**corr_dict)

    def _generate_correction_markdown(self, correction: Correction) -> str:
        """Génère le contenu markdown d'une correction"""
        return f"""# Correction : {correction.field_path}

## Contexte
Document : {correction.document_id}
Timestamp : {correction.timestamp.isoformat()}

## Valeurs
- **Original** : `{correction.original_value}`
- **Corrigé** : `{correction.corrected_value}`

## Explication
[À compléter]

## Notes
"""

    def _generate_explanation_markdown(self, explanation: Explanation) -> str:
        """Génère le contenu markdown d'une explication"""
        subcategory_line = (
            f"**Sous-catégorie** : `{explanation.subcategory}`\n"
            if explanation.subcategory
            else ""
        )
        confidence_line = (
            f"**Confiance** : {explanation.confidence}\n" if explanation.confidence else ""
        )

        return f"""## Explication

**Catégorie** : `{explanation.category}`
{subcategory_line}
{explanation.description}

**Type** : {explanation.explanation_type}
{confidence_line}"""
