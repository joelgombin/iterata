import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from iterata import CorrectionLogger, PatternDetector
from iterata.core.models import CorrectionType


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def logger_with_corrections(temp_dir):
    """Create a logger and add some test corrections"""
    logger = CorrectionLogger(base_path=temp_dir)

    # Add format error corrections (decimal separator)
    for i in range(5):
        corr = logger.log(
            original=f"1.{i}34,56",
            corrected=f"1{i}34.56",
            document_id=f"doc_{i:03d}.pdf",
            field_path="amount",
        )
        logger.explain_pending(
            corr.correction_id,
            explanation_text="Le séparateur décimal devrait être un point",
        )

    # Add business rule corrections
    for i in range(3):
        corr = logger.log(
            original=f"ACME{i}",
            corrected=f"ACME Corporation {i}",
            document_id=f"doc_{100+i}.pdf",
            field_path="vendor_name",
        )
        logger.explain_pending(
            corr.correction_id, explanation_text="Le nom complet de la société est requis"
        )

    # Add date format corrections
    for i in range(4):
        corr = logger.log(
            original=f"01/0{i+1}/2024",
            corrected=f"2024-01-0{i+1}",
            document_id=f"doc_{200+i}.pdf",
            field_path="invoice_date",
        )
        logger.explain_pending(
            corr.correction_id, explanation_text="Format de date ISO 8601 requis"
        )

    return logger


class TestPatternDetector:
    def test_init(self, temp_dir):
        """Test pattern detector initialization"""
        logger = CorrectionLogger(base_path=temp_dir)
        detector = PatternDetector(logger.storage)

        assert detector.storage is not None

    def test_detect_patterns_empty(self, temp_dir):
        """Test pattern detection with no corrections"""
        logger = CorrectionLogger(base_path=temp_dir)
        detector = PatternDetector(logger.storage)

        patterns = detector.detect_patterns()
        assert len(patterns) == 0

    def test_detect_patterns_below_threshold(self, temp_dir):
        """Test that patterns below min_occurrences are filtered out"""
        logger = CorrectionLogger(base_path=temp_dir)

        # Add only 2 corrections (below default threshold of 3)
        for i in range(2):
            corr = logger.log(
                original=f"test{i}", corrected=f"corrected{i}", document_id=f"doc_{i}"
            )
            logger.explain_pending(corr.correction_id, explanation_text="Test explanation")

        detector = PatternDetector(logger.storage)
        patterns = detector.detect_patterns(min_occurrences=3)

        assert len(patterns) == 0

    def test_detect_patterns(self, logger_with_corrections):
        """Test basic pattern detection"""
        detector = PatternDetector(logger_with_corrections.storage)
        patterns = detector.detect_patterns(min_occurrences=3)

        # Should detect at least some patterns (grouping by category may vary)
        assert len(patterns) >= 1

        # Check that patterns have required fields
        for pattern in patterns:
            assert pattern.pattern_id is not None
            assert pattern.category in CorrectionType
            assert pattern.frequency >= 3
            assert pattern.impact in ["low", "medium", "high"]
            assert 0 <= pattern.automation_potential <= 1

    def test_pattern_impact_assessment(self, logger_with_corrections):
        """Test impact assessment logic"""
        detector = PatternDetector(logger_with_corrections.storage)

        # 5 corrections = low impact
        assert detector._assess_impact(5) == "low"

        # 10 corrections = medium impact
        assert detector._assess_impact(10) == "medium"

        # 20+ corrections = high impact
        assert detector._assess_impact(25) == "high"

    def test_detect_patterns_by_field(self, logger_with_corrections):
        """Test pattern detection grouped by field"""
        detector = PatternDetector(logger_with_corrections.storage)
        field_patterns = detector.detect_patterns_by_field(min_occurrences=3)

        # Should find patterns for amount, vendor_name, and invoice_date
        assert len(field_patterns) >= 3

        # Check that we have the expected fields
        field_paths = [p.description for p in field_patterns]
        assert any("amount" in desc for desc in field_paths)
        assert any("vendor_name" in desc for desc in field_paths)
        assert any("invoice_date" in desc for desc in field_paths)

    def test_detect_transformation_patterns(self, logger_with_corrections):
        """Test transformation pattern detection"""
        detector = PatternDetector(logger_with_corrections.storage)
        transformations = detector.detect_transformation_patterns(min_occurrences=3)

        # Should find transformation patterns
        assert len(transformations) >= 1

        # Check structure of transformation patterns
        for transfo in transformations:
            assert "pattern" in transfo
            assert "frequency" in transfo
            assert "examples" in transfo
            assert "correction_ids" in transfo
            assert transfo["frequency"] >= 3

    def test_infer_transformation_pattern_decimal(self, temp_dir):
        """Test decimal separator transformation inference"""
        logger = CorrectionLogger(base_path=temp_dir)
        detector = PatternDetector(logger.storage)

        # Comma to dot
        pattern = detector._infer_transformation_pattern("1,234", "1.234")
        assert pattern == "decimal_comma_to_dot"

        # Dot to comma
        pattern = detector._infer_transformation_pattern("1.234", "1,234")
        assert pattern == "decimal_dot_to_comma"

    def test_infer_transformation_pattern_case(self, temp_dir):
        """Test case transformation inference"""
        logger = CorrectionLogger(base_path=temp_dir)
        detector = PatternDetector(logger.storage)

        # To uppercase
        pattern = detector._infer_transformation_pattern("acme", "ACME")
        assert pattern == "to_uppercase"

        # To lowercase
        pattern = detector._infer_transformation_pattern("ACME", "acme")
        assert pattern == "to_lowercase"

        # To titlecase
        pattern = detector._infer_transformation_pattern("acme corp", "Acme Corp")
        assert pattern == "to_titlecase"

    def test_infer_transformation_pattern_spaces(self, temp_dir):
        """Test space transformation inference"""
        logger = CorrectionLogger(base_path=temp_dir)
        detector = PatternDetector(logger.storage)

        # Remove spaces
        pattern = detector._infer_transformation_pattern("1 234 567", "1234567")
        assert pattern == "remove_spaces"

        # Add spaces
        pattern = detector._infer_transformation_pattern("1234567", "1 234 567")
        assert pattern == "add_spaces"

    def test_infer_transformation_pattern_date(self, temp_dir):
        """Test date format transformation inference"""
        logger = CorrectionLogger(base_path=temp_dir)
        detector = PatternDetector(logger.storage)

        pattern = detector._infer_transformation_pattern("01/02/2024", "2024-02-01")
        assert pattern == "date_format_change"

    def test_automation_potential(self, temp_dir):
        """Test automation potential assessment"""
        logger = CorrectionLogger(base_path=temp_dir)

        # Create corrections with consistent pattern (should have high potential)
        for i in range(5):
            corr = logger.log(
                original=f"1,{i}00",
                corrected=f"1.{i}00",
                document_id=f"doc_{i}",
                field_path="amount",  # Same field
            )
            logger.explain_pending(corr.correction_id, explanation_text="Decimal separator")

        detector = PatternDetector(logger.storage)
        corrections = logger.storage.load_corrections(status="explained")
        potential = detector._assess_automation_potential(corrections)

        # Should be high because same field, same type, same transformation
        assert potential >= 0.7

    def test_get_pattern_summary(self, logger_with_corrections):
        """Test pattern summary generation"""
        detector = PatternDetector(logger_with_corrections.storage)
        summary = detector.get_pattern_summary()

        # Check that summary has all required keys
        assert "total_patterns" in summary
        assert "patterns_by_category" in summary
        assert "high_impact_count" in summary
        assert "medium_impact_count" in summary
        assert "low_impact_count" in summary
        assert "highly_automatable_count" in summary
        assert "field_patterns_count" in summary
        assert "transformation_patterns_count" in summary
        assert "top_patterns" in summary
        assert "most_automatable" in summary

        # Check that counts are reasonable
        assert summary["total_patterns"] >= 0
        assert len(summary["top_patterns"]) <= 5
        assert len(summary["most_automatable"]) <= 5

    def test_pattern_description_generation(self, logger_with_corrections):
        """Test that pattern descriptions are meaningful"""
        detector = PatternDetector(logger_with_corrections.storage)
        patterns = detector.detect_patterns(min_occurrences=3)

        for pattern in patterns:
            # Description should not be empty
            assert len(pattern.description) > 0
            # Should mention field or contain useful info
            assert "champ" in pattern.description.lower() or len(pattern.description) > 10

    def test_pattern_temporal_data(self, temp_dir):
        """Test that patterns capture temporal information"""
        logger = CorrectionLogger(base_path=temp_dir)

        # Create corrections with different timestamps
        base_time = datetime.utcnow()
        for i in range(5):
            corr = logger.log(
                original=f"test{i}", corrected=f"corrected{i}", document_id=f"doc_{i}"
            )
            # Manually adjust timestamp in the file
            logger.explain_pending(corr.correction_id, explanation_text="Test")

        detector = PatternDetector(logger.storage)
        patterns = detector.detect_patterns(min_occurrences=3)

        if patterns:
            pattern = patterns[0]
            # Should have first_seen and last_seen
            assert pattern.first_seen is not None
            assert pattern.last_seen is not None
            # last_seen should be >= first_seen
            assert pattern.last_seen >= pattern.first_seen

    def test_patterns_with_mixed_categories(self, temp_dir):
        """Test pattern detection with mixed categories"""
        logger = CorrectionLogger(base_path=temp_dir)

        # Add corrections of different categories
        for i in range(3):
            corr = logger.log(
                original="1,234", corrected="1.234", document_id=f"doc_a_{i}", field_path="amount"
            )
            logger.explain_pending(corr.correction_id, explanation_text="Format décimal")

        for i in range(4):
            corr = logger.log(
                original="ACME", corrected="ACME Corp", document_id=f"doc_b_{i}", field_path="vendor"
            )
            logger.explain_pending(
                corr.correction_id, explanation_text="Nom complet requis (règle métier)"
            )

        detector = PatternDetector(logger.storage)
        patterns = detector.detect_patterns(min_occurrences=3)

        # Should detect both patterns
        assert len(patterns) >= 2

        # Categories should be different
        categories = [p.category for p in patterns]
        assert CorrectionType.FORMAT_ERROR in categories
        assert CorrectionType.BUSINESS_RULE in categories
