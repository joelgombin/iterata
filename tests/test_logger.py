import pytest
import tempfile
import shutil
from pathlib import Path
from iterata.core.logger import CorrectionLogger
from iterata.core.models import CorrectionType, ExplanationType
from iterata.backends.mock import MockExplainer


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def logger(temp_dir):
    """Create a logger without auto-explain"""
    return CorrectionLogger(base_path=temp_dir)


@pytest.fixture
def logger_with_explainer(temp_dir):
    """Create a logger with mock explainer and auto-explain"""
    explainer = MockExplainer()
    return CorrectionLogger(base_path=temp_dir, explainer=explainer, auto_explain=True)


class TestCorrectionLogger:
    def test_log_basic_correction(self, logger):
        """Test logging a basic correction"""
        correction = logger.log(
            original="1,234.56",
            corrected="1234.56",
            document_id="invoice_001.pdf",
            field_path="total_amount",
        )

        assert correction.original_value == "1,234.56"
        assert correction.corrected_value == "1234.56"
        assert correction.document_id == "invoice_001.pdf"
        assert correction.field_path == "total_amount"
        assert correction.correction_id is not None

    def test_log_with_context(self, logger):
        """Test logging with additional context"""
        correction = logger.log(
            original="ACME",
            corrected="ACME Corporation",
            document_id="invoice_002.pdf",
            field_path="vendor_name",
            context={"model": "claude-3", "extraction_method": "ocr"},
        )

        assert correction.context["model"] == "claude-3"
        assert correction.context["extraction_method"] == "ocr"

    def test_log_with_confidence(self, logger):
        """Test logging with confidence score"""
        correction = logger.log(
            original="2024-01-32",
            corrected="2024-02-01",
            document_id="invoice_003.pdf",
            field_path="invoice_date",
            confidence_before=0.45,
            corrector_id="user_123",
        )

        assert correction.confidence_before == 0.45
        assert correction.corrector_id == "user_123"

    def test_log_saves_to_inbox(self, logger, temp_dir):
        """Test that corrections are saved to inbox"""
        correction = logger.log(
            original="A", corrected="B", document_id="doc_001", field_path="field1"
        )

        inbox_path = Path(temp_dir) / "inbox"
        correction_file = inbox_path / f"{correction.correction_id}.md"

        assert correction_file.exists()

    def test_log_with_human_explanation(self, logger):
        """Test logging with human-provided explanation"""
        correction = logger.log(
            original="1,234",
            corrected="1234",
            document_id="doc_004",
            field_path="amount",
            human_explanation="Le séparateur décimal français n'est pas supporté",
        )

        # Without auto_explain, should still save to inbox
        assert correction.correction_id is not None

    def test_auto_explain_with_human_explanation(self, logger_with_explainer, temp_dir):
        """Test auto-explain with human-provided explanation"""
        correction = logger_with_explainer.log(
            original="1,234",
            corrected="1234",
            document_id="doc_005",
            field_path="amount",
            corrector_id="user_456",
            human_explanation="Le séparateur décimal français n'est pas supporté",
        )

        # Should be moved to explained/ directory
        inbox_path = Path(temp_dir) / "inbox" / f"{correction.correction_id}.md"
        assert not inbox_path.exists()

        # Should be in explained/
        explained_path = Path(temp_dir) / "explained"
        explained_files = list(explained_path.rglob("*.md"))
        assert len(explained_files) == 1

    def test_auto_explain_with_llm(self, logger_with_explainer, temp_dir):
        """Test auto-explain with LLM inference"""
        correction = logger_with_explainer.log(
            original="test_value",
            corrected="corrected_value",
            document_id="doc_006",
            field_path="test_field",
        )

        # Should be moved to explained/ directory
        inbox_path = Path(temp_dir) / "inbox" / f"{correction.correction_id}.md"
        assert not inbox_path.exists()

        # Should be in explained/format_errors (MockExplainer returns FORMAT_ERROR)
        explained_path = Path(temp_dir) / "explained" / "format_errors"
        explained_files = list(explained_path.glob("*.md"))
        assert len(explained_files) == 1

    def test_explain_pending_with_text(self, logger, temp_dir):
        """Test adding explanation to pending correction"""
        # First, log a correction
        correction = logger.log(
            original="A", corrected="B", document_id="doc_007", field_path="field1"
        )

        # Then explain it
        logger.explain_pending(
            correction.correction_id, explanation_text="This is a manual explanation"
        )

        # Should be moved from inbox
        inbox_path = Path(temp_dir) / "inbox" / f"{correction.correction_id}.md"
        assert not inbox_path.exists()

        # Should be in explained/
        explained_files = list((Path(temp_dir) / "explained").rglob("*.md"))
        assert len(explained_files) == 1

    def test_explain_pending_with_llm(self, temp_dir):
        """Test explaining pending correction with LLM"""
        explainer = MockExplainer()
        logger = CorrectionLogger(base_path=temp_dir, explainer=explainer)

        # Log without auto-explain
        correction = logger.log(
            original="test", corrected="corrected", document_id="doc_008", field_path="field1"
        )

        # Explain later
        logger.explain_pending(correction.correction_id)

        # Should be moved
        inbox_path = Path(temp_dir) / "inbox" / f"{correction.correction_id}.md"
        assert not inbox_path.exists()

    def test_explain_pending_not_found(self, logger):
        """Test explaining non-existent correction"""
        with pytest.raises(ValueError, match="not found in inbox"):
            logger.explain_pending("nonexistent_id")

    def test_explain_pending_no_explainer_no_text(self, logger):
        """Test explaining without explainer or text"""
        correction = logger.log(
            original="A", corrected="B", document_id="doc_009", field_path="field1"
        )

        with pytest.raises(ValueError, match="No explainer configured"):
            logger.explain_pending(correction.correction_id)

    def test_categorize_from_text_format_error(self, logger):
        """Test text categorization for format errors"""
        category = logger._categorize_from_text("Le séparateur décimal est incorrect")
        assert category == CorrectionType.FORMAT_ERROR

    def test_categorize_from_text_business_rule(self, logger):
        """Test text categorization for business rules"""
        category = logger._categorize_from_text("Cela viole une règle métier importante")
        assert category == CorrectionType.BUSINESS_RULE

    def test_categorize_from_text_other(self, logger):
        """Test text categorization for unknown category"""
        category = logger._categorize_from_text("Something else entirely")
        assert category == CorrectionType.OTHER

    def test_multiple_corrections(self, logger, temp_dir):
        """Test logging multiple corrections"""
        corrections = []
        for i in range(5):
            corr = logger.log(
                original=f"original_{i}",
                corrected=f"corrected_{i}",
                document_id=f"doc_{i:03d}",
                field_path=f"field_{i}",
            )
            corrections.append(corr)

        # Check that all are saved
        inbox_path = Path(temp_dir) / "inbox"
        inbox_files = list(inbox_path.glob("*.md"))
        assert len(inbox_files) == 5

        # Check all IDs are unique
        ids = [c.correction_id for c in corrections]
        assert len(set(ids)) == 5
