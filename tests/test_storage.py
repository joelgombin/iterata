import pytest
import tempfile
import shutil
from pathlib import Path
from iterata.core.storage import MarkdownStorage
from iterata.core.models import Correction, Explanation, ExplanationType, CorrectionType


@pytest.fixture
def temp_storage():
    """Create a temporary storage directory for testing"""
    temp_dir = tempfile.mkdtemp()
    storage = MarkdownStorage(temp_dir)
    yield storage
    # Cleanup
    shutil.rmtree(temp_dir)


class TestMarkdownStorage:
    def test_init_directories(self, temp_storage):
        """Test that all required directories are created"""
        base_path = temp_storage.base_path

        assert (base_path / "inbox").exists()
        assert (base_path / "explained" / "format_errors").exists()
        assert (base_path / "explained" / "business_rules").exists()
        assert (base_path / "explained" / "model_limitations").exists()
        assert (base_path / "explained" / "context_missing").exists()
        assert (base_path / "explained" / "ocr_errors").exists()
        assert (base_path / "explained" / "other").exists()
        assert (base_path / "patterns").exists()
        assert (base_path / "rules").exists()
        assert (base_path / "meta").exists()

    def test_save_correction(self, temp_storage):
        """Test saving a correction to inbox"""
        correction = Correction(
            document_id="test_doc_001",
            field_path="invoice.total",
            original_value="1,234.56",
            corrected_value="1234.56",
        )

        filepath = temp_storage.save_correction(correction)

        assert filepath.exists()
        assert filepath.parent.name == "inbox"
        assert filepath.suffix == ".md"

    def test_save_correction_with_context(self, temp_storage):
        """Test saving a correction with context"""
        correction = Correction(
            document_id="test_doc_002",
            field_path="invoice.vendor",
            original_value="ACME",
            corrected_value="ACME Corp",
            context={"model": "claude-3", "extraction_method": "ocr"},
        )

        filepath = temp_storage.save_correction(correction)

        # Load and verify
        import frontmatter

        post = frontmatter.load(filepath)
        assert post.metadata["document_id"] == "test_doc_002"
        assert post.metadata["model"] == "claude-3"
        assert post.metadata["extraction_method"] == "ocr"

    def test_load_corrections_from_inbox(self, temp_storage):
        """Test loading corrections from inbox"""
        # Save multiple corrections
        corr1 = Correction(
            document_id="doc_001", field_path="field1", original_value="A", corrected_value="B"
        )
        corr2 = Correction(
            document_id="doc_002", field_path="field2", original_value="C", corrected_value="D"
        )

        temp_storage.save_correction(corr1)
        temp_storage.save_correction(corr2)

        # Load all
        corrections = temp_storage.load_corrections(status="inbox")

        assert len(corrections) == 2
        doc_ids = [c.document_id for c in corrections]
        assert "doc_001" in doc_ids
        assert "doc_002" in doc_ids

    def test_save_explanation(self, temp_storage):
        """Test saving an explanation and moving correction"""
        # First, save a correction
        correction = Correction(
            document_id="doc_003",
            field_path="invoice.date",
            original_value="01/02/2024",
            corrected_value="2024-02-01",
        )

        temp_storage.save_correction(correction)

        # Create an explanation
        explanation = Explanation(
            correction_id=correction.correction_id,
            explanation_type=ExplanationType.HUMAN_PROVIDED,
            category=CorrectionType.FORMAT_ERROR,
            description="Date format should be ISO 8601",
            explainer_id="user_123",
            tags=["date", "format"],
        )

        # Save explanation
        new_path = temp_storage.save_explanation(explanation, correction)

        # Check that file moved to explained/format_errors
        assert new_path.exists()
        assert "explained" in str(new_path)
        assert "format_errors" in str(new_path)

        # Check that inbox is empty
        inbox_path = temp_storage.base_path / "inbox" / f"{correction.correction_id}.md"
        assert not inbox_path.exists()

    def test_save_explanation_different_categories(self, temp_storage):
        """Test that explanations are saved to correct category directories"""
        categories_to_test = [
            (CorrectionType.FORMAT_ERROR, "format_errors"),
            (CorrectionType.BUSINESS_RULE, "business_rules"),
            (CorrectionType.MODEL_LIMITATION, "model_limitations"),
            (CorrectionType.CONTEXT_MISSING, "context_missing"),
            (CorrectionType.OCR_ERROR, "ocr_errors"),
            (CorrectionType.OTHER, "other"),
        ]

        for category, expected_dir in categories_to_test:
            correction = Correction(
                document_id=f"doc_{category.value}",
                field_path="test_field",
                original_value="A",
                corrected_value="B",
            )

            temp_storage.save_correction(correction)

            explanation = Explanation(
                correction_id=correction.correction_id,
                explanation_type=ExplanationType.HUMAN_PROVIDED,
                category=category,
                description=f"Test for {category}",
                explainer_id="tester",
            )

            new_path = temp_storage.save_explanation(explanation, correction)
            assert expected_dir in str(new_path)

    def test_load_all_corrections(self, temp_storage):
        """Test loading all corrections (inbox + explained)"""
        # Save to inbox
        corr1 = Correction(
            document_id="doc_inbox", field_path="field1", original_value="A", corrected_value="B"
        )
        temp_storage.save_correction(corr1)

        # Save and explain
        corr2 = Correction(
            document_id="doc_explained",
            field_path="field2",
            original_value="C",
            corrected_value="D",
        )
        temp_storage.save_correction(corr2)

        explanation = Explanation(
            correction_id=corr2.correction_id,
            explanation_type=ExplanationType.HUMAN_PROVIDED,
            category=CorrectionType.OTHER,
            description="Test explanation",
            explainer_id="tester",
        )
        temp_storage.save_explanation(explanation, corr2)

        # Load all
        all_corrections = temp_storage.load_corrections(status="all")
        assert len(all_corrections) == 2

        # Load only inbox
        inbox_corrections = temp_storage.load_corrections(status="inbox")
        assert len(inbox_corrections) == 1
        assert inbox_corrections[0].document_id == "doc_inbox"

        # Load only explained
        explained_corrections = temp_storage.load_corrections(status="explained")
        assert len(explained_corrections) == 1
        assert explained_corrections[0].document_id == "doc_explained"

    def test_correction_markdown_content(self, temp_storage):
        """Test that markdown content is correctly generated"""
        correction = Correction(
            document_id="test_doc",
            field_path="test.field",
            original_value="original",
            corrected_value="corrected",
        )

        filepath = temp_storage.save_correction(correction)

        # Read content
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        assert "# Correction : test.field" in content
        assert "Document : test_doc" in content
        assert "`original`" in content
        assert "`corrected`" in content

    def test_explanation_markdown_content(self, temp_storage):
        """Test that explanation content is added correctly"""
        correction = Correction(
            document_id="test_doc",
            field_path="test.field",
            original_value="A",
            corrected_value="B",
        )

        temp_storage.save_correction(correction)

        explanation = Explanation(
            correction_id=correction.correction_id,
            explanation_type=ExplanationType.LLM_INFERRED,
            category=CorrectionType.BUSINESS_RULE,
            subcategory="validation",
            description="This is a business rule violation",
            confidence=0.95,
            explainer_id="claude-3",
            tags=["validation", "business"],
        )

        new_path = temp_storage.save_explanation(explanation, correction)

        # Read content
        with open(new_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "## Explication" in content
        assert "business_rule" in content
        assert "validation" in content
        assert "This is a business rule violation" in content
        assert "0.95" in content
