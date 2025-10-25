import pytest
import tempfile
import shutil
from iterata import CorrectionLogger, Statistics
from datetime import datetime, timedelta


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def logger_with_data(temp_dir):
    """Create a logger with comprehensive test data"""
    logger = CorrectionLogger(base_path=temp_dir)

    # Add various types of corrections
    # Format errors (5)
    for i in range(5):
        corr = logger.log(
            original=f"1,{i}00",
            corrected=f"1.{i}00",
            document_id=f"invoice_{i:03d}.pdf",
            field_path="amount",
            confidence_before=0.85,
            corrector_id="user_alice",
        )
        logger.explain_pending(corr.correction_id, explanation_text="Format décimal incorrect")

    # Business rules (3)
    for i in range(3):
        corr = logger.log(
            original="ACME",
            corrected="ACME Corporation",
            document_id=f"invoice_{100+i}.pdf",
            field_path="vendor_name",
            confidence_before=0.70,
            corrector_id="user_bob",
        )
        logger.explain_pending(
            corr.correction_id, explanation_text="Nom complet requis (règle métier)"
        )

    # Date format (4)
    for i in range(4):
        corr = logger.log(
            original=f"0{i+1}/01/2024",
            corrected=f"2024-01-0{i+1}",
            document_id=f"invoice_{200+i}.pdf",
            field_path="date",
            confidence_before=0.60,
            corrector_id="user_alice",
        )
        logger.explain_pending(corr.correction_id, explanation_text="Format de date ISO 8601")

    # Leave 2 in inbox (not explained)
    for i in range(2):
        logger.log(
            original=f"pending{i}",
            corrected=f"fixed{i}",
            document_id=f"invoice_{300+i}.pdf",
            field_path="other_field",
            corrector_id="user_charlie",
        )

    return logger


class TestStatistics:
    def test_init(self, temp_dir):
        """Test statistics initialization"""
        logger = CorrectionLogger(base_path=temp_dir)
        stats = Statistics(logger.storage)

        assert stats.storage is not None
        assert stats.pattern_detector is not None

    def test_compute_empty(self, temp_dir):
        """Test compute with no corrections"""
        logger = CorrectionLogger(base_path=temp_dir)
        stats = Statistics(logger.storage)

        result = stats.compute()

        assert result["total_corrections"] == 0
        assert result["corrections_explained"] == 0
        assert result["corrections_pending"] == 0
        assert result["patterns_count"] == 0
        assert result["correction_rate"] == 0

    def test_compute_basic(self, logger_with_data):
        """Test basic statistics computation"""
        stats = Statistics(logger_with_data.storage)
        result = stats.compute()

        assert result["total_corrections"] == 14  # 12 explained + 2 pending
        assert result["corrections_explained"] == 12
        assert result["corrections_pending"] == 2
        assert result["correction_rate"] == 12 / 14

        # Check categories
        assert "categories" in result
        assert len(result["categories"]) > 0

        # Check top fields
        assert "top_fields" in result
        assert len(result["top_fields"]) > 0

    def test_compute_detailed(self, logger_with_data):
        """Test detailed statistics computation"""
        stats = Statistics(logger_with_data.storage)
        result = stats.compute_detailed()

        # Should have all basic stats
        assert "total_corrections" in result
        assert "corrections_explained" in result

        # Plus detailed stats
        assert "field_patterns" in result
        assert "transformation_patterns" in result
        assert "pattern_summary" in result
        assert "corrector_stats" in result
        assert "confidence_stats" in result
        assert "document_stats" in result
        assert "inbox_corrections" in result

        assert result["inbox_corrections"] == 2

    def test_categories_breakdown(self, logger_with_data):
        """Test category breakdown in statistics"""
        stats = Statistics(logger_with_data.storage)
        result = stats.compute()

        categories = result["categories"]

        # Should have format_error and business_rule
        assert "format_error" in categories
        assert "business_rule" in categories

        # Check counts (date format errors are also categorized as format_error)
        # 5 amount + 4 date = 9 format_errors
        assert categories["format_error"] == 9
        assert categories["business_rule"] == 3

    def test_top_fields(self, logger_with_data):
        """Test top fields statistics"""
        stats = Statistics(logger_with_data.storage)
        result = stats.compute()

        top_fields = result["top_fields"]

        # Should have amount, vendor_name, date, other_field
        assert "amount" in top_fields
        assert "vendor_name" in top_fields
        assert "date" in top_fields

        # Check that amount has most corrections (5)
        assert top_fields["amount"] == 5

    def test_corrector_stats(self, logger_with_data):
        """Test corrector statistics"""
        stats = Statistics(logger_with_data.storage)
        result = stats.compute_detailed()

        corrector_stats = result["corrector_stats"]

        assert corrector_stats["total_correctors"] == 3
        assert "corrections_by_corrector" in corrector_stats

        # alice should have most corrections (5 + 4 = 9)
        corrections_by = corrector_stats["corrections_by_corrector"]
        assert corrections_by["user_alice"] == 9
        assert corrections_by["user_bob"] == 3
        assert corrections_by["user_charlie"] == 2

    def test_confidence_stats(self, logger_with_data):
        """Test confidence statistics"""
        stats = Statistics(logger_with_data.storage)
        result = stats.compute_detailed()

        conf_stats = result["confidence_stats"]

        assert conf_stats["corrections_with_confidence"] == 12
        assert conf_stats["average_confidence"] is not None
        assert 0 <= conf_stats["average_confidence"] <= 1
        assert conf_stats["low_confidence_corrections"] >= 0

    def test_document_stats(self, logger_with_data):
        """Test document statistics"""
        stats = Statistics(logger_with_data.storage)
        result = stats.compute_detailed()

        doc_stats = result["document_stats"]

        assert doc_stats["total_documents"] == 14
        assert "corrections_per_document" in doc_stats
        assert "average_corrections_per_doc" in doc_stats

        # Each document has 1 correction in our test data
        assert doc_stats["average_corrections_per_doc"] == 1.0

    def test_time_stats(self, logger_with_data):
        """Test temporal statistics"""
        stats = Statistics(logger_with_data.storage)
        result = stats.compute()

        time_stats = result["time_stats"]

        assert "first_correction" in time_stats
        assert "last_correction" in time_stats
        assert "corrections_last_7_days" in time_stats
        assert "corrections_last_30_days" in time_stats

        # All corrections were just created, so should be in last 7 days
        assert time_stats["corrections_last_7_days"] == 14
        assert time_stats["corrections_last_30_days"] == 14

    def test_get_summary(self, logger_with_data):
        """Test summary text generation"""
        stats = Statistics(logger_with_data.storage)
        summary = stats.get_summary()

        assert isinstance(summary, str)
        assert len(summary) > 0

        # Should contain key information
        assert "Total Corrections" in summary
        assert "Explained" in summary
        assert "Pending" in summary
        assert "Patterns Detected" in summary

    def test_get_recommendations(self, logger_with_data):
        """Test recommendation generation"""
        stats = Statistics(logger_with_data.storage)
        recommendations = stats.get_recommendations()

        assert isinstance(recommendations, list)

        # Check recommendation structure
        for rec in recommendations:
            assert "priority" in rec
            assert rec["priority"] in ["high", "medium", "low"]
            assert "type" in rec
            assert "title" in rec
            assert "reason" in rec

    def test_recommendations_pending_corrections(self, temp_dir):
        """Test that recommendations include pending corrections"""
        logger = CorrectionLogger(base_path=temp_dir)

        # Add many pending corrections
        for i in range(15):
            logger.log(original=f"a{i}", corrected=f"b{i}", document_id=f"doc_{i}")

        stats = Statistics(logger.storage)
        recommendations = stats.get_recommendations()

        # Should recommend explaining pending corrections
        titles = [r["title"] for r in recommendations]
        assert any("attente" in title.lower() or "pending" in title.lower() for title in titles)

    def test_recommendations_high_impact_patterns(self, temp_dir):
        """Test recommendations for high impact patterns"""
        logger = CorrectionLogger(base_path=temp_dir)

        # Create 25 corrections with same pattern (high impact)
        for i in range(25):
            corr = logger.log(
                original=f"1,{i:03d}",
                corrected=f"1.{i:03d}",
                document_id=f"doc_{i}",
                field_path="amount",
            )
            logger.explain_pending(corr.correction_id, explanation_text="Format décimal")

        stats = Statistics(logger.storage)
        recommendations = stats.get_recommendations()

        # Should have high priority recommendations
        high_priority = [r for r in recommendations if r["priority"] == "high"]
        assert len(high_priority) > 0

    def test_export_stats_json(self, logger_with_data):
        """Test JSON export"""
        stats = Statistics(logger_with_data.storage)
        json_output = stats.export_stats_json()

        assert isinstance(json_output, str)
        assert len(json_output) > 0

        # Should be valid JSON
        import json

        data = json.loads(json_output)
        assert "total_corrections" in data

    def test_export_stats_csv(self, logger_with_data):
        """Test CSV export"""
        stats = Statistics(logger_with_data.storage)
        csv_output = stats.export_stats_csv()

        assert isinstance(csv_output, str)
        assert len(csv_output) > 0

        # Should have CSV headers
        lines = csv_output.strip().split("\n")
        assert len(lines) > 1  # At least header + 1 row

        header = lines[0]
        assert "correction_id" in header
        assert "document_id" in header
        assert "field_path" in header

    def test_time_stats_empty(self, temp_dir):
        """Test time stats with no corrections"""
        logger = CorrectionLogger(base_path=temp_dir)
        stats = Statistics(logger.storage)

        result = stats.compute()
        time_stats = result["time_stats"]

        assert time_stats["first_correction"] is None
        assert time_stats["last_correction"] is None
        assert time_stats["corrections_last_7_days"] == 0
        assert time_stats["corrections_last_30_days"] == 0

    def test_confidence_stats_none(self, temp_dir):
        """Test confidence stats when no confidence scores provided"""
        logger = CorrectionLogger(base_path=temp_dir)

        # Add corrections without confidence
        for i in range(3):
            corr = logger.log(
                original=f"a{i}", corrected=f"b{i}", document_id=f"doc_{i}", field_path="field"
            )
            logger.explain_pending(corr.correction_id, explanation_text="Test")

        stats = Statistics(logger.storage)
        result = stats.compute_detailed()

        conf_stats = result["confidence_stats"]
        assert conf_stats["corrections_with_confidence"] == 0
        assert conf_stats["average_confidence"] is None

    def test_pattern_integration(self, logger_with_data):
        """Test that statistics correctly integrates pattern detection"""
        stats = Statistics(logger_with_data.storage)
        result = stats.compute()

        # Patterns should be detected (grouping may vary based on categorization)
        assert result["patterns_count"] >= 1

        patterns = result["patterns"]
        assert len(patterns) >= 1

        # Each pattern should have the correct structure
        for pattern in patterns:
            assert "pattern_id" in pattern
            assert "frequency" in pattern
            assert "impact" in pattern

    def test_recommendations_sorting(self, logger_with_data):
        """Test that recommendations are sorted by priority"""
        stats = Statistics(logger_with_data.storage)
        recommendations = stats.get_recommendations()

        if len(recommendations) > 1:
            # Check that high priority comes before medium
            priorities = [r["priority"] for r in recommendations]
            # Find indices
            if "high" in priorities and "medium" in priorities:
                high_idx = priorities.index("high")
                medium_idx = priorities.index("medium")
                assert high_idx < medium_idx

    def test_statistics_with_only_inbox(self, temp_dir):
        """Test statistics when all corrections are in inbox"""
        logger = CorrectionLogger(base_path=temp_dir)

        for i in range(5):
            logger.log(original=f"a{i}", corrected=f"b{i}", document_id=f"doc_{i}")

        stats = Statistics(logger.storage)
        result = stats.compute()

        assert result["total_corrections"] == 5
        assert result["corrections_explained"] == 0
        assert result["corrections_pending"] == 5
        assert result["correction_rate"] == 0
        assert result["patterns_count"] == 0  # No patterns without explanations
