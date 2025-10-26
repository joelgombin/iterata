import pytest
import tempfile
import shutil
from iterata import with_correction_tracking, track_corrections, CorrectionLoop


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


class TestWithCorrectionTracking:
    def test_basic_decoration(self, temp_dir):
        """Test basic function decoration"""

        @with_correction_tracking(base_path=temp_dir)
        def extract_data(doc_path: str) -> dict:
            return {"field": "value"}

        result = extract_data("test.pdf")

        assert result == {"field": "value"}
        assert hasattr(extract_data, "log_correction")
        assert hasattr(extract_data, "get_stats")
        assert hasattr(extract_data, "get_summary")
        assert hasattr(extract_data, "update_skill")
        assert hasattr(extract_data, "_iterata_loop")

    def test_log_correction_method(self, temp_dir):
        """Test the log_correction method attached to decorated function"""

        @with_correction_tracking(base_path=temp_dir)
        def extract_data(doc_path: str) -> dict:
            return {"amount": "1,234.56"}

        result = extract_data("test.pdf")

        # Log a correction
        correction = extract_data.log_correction(
            original=result["amount"],
            corrected="1234.56",
            document_id="test.pdf",
            field_path="amount",
        )

        assert correction.correction_id is not None
        assert correction.original_value == "1,234.56"
        assert correction.corrected_value == "1234.56"
        assert correction.context["function"] == "extract_data"

    def test_get_stats_method(self, temp_dir):
        """Test the get_stats method attached to decorated function"""

        @with_correction_tracking(base_path=temp_dir)
        def extract_data(doc_path: str) -> dict:
            return {"field": "value"}

        # Log some corrections
        for i in range(3):
            extract_data.log_correction(
                original=f"test_{i}",
                corrected=f"fixed_{i}",
                document_id=f"doc_{i}.pdf",
                field_path="field",
            )

        stats = extract_data.get_stats()

        assert stats["total_corrections"] == 3

    def test_function_context_added(self, temp_dir):
        """Test that function name is added to context"""

        @with_correction_tracking(base_path=temp_dir)
        def my_extraction_function(doc_path: str) -> dict:
            return {"field": "value"}

        correction = my_extraction_function.log_correction(
            original="test", corrected="fixed", document_id="doc.pdf"
        )

        assert correction.context["function"] == "my_extraction_function"

    def test_custom_context_preserved(self, temp_dir):
        """Test that custom context is preserved along with function name"""

        @with_correction_tracking(base_path=temp_dir)
        def extract_data(doc_path: str) -> dict:
            return {"field": "value"}

        custom_context = {"model": "gpt-4", "version": "1.0"}

        correction = extract_data.log_correction(
            original="test",
            corrected="fixed",
            document_id="doc.pdf",
            context=custom_context,
        )

        assert correction.context["function"] == "extract_data"
        assert correction.context["model"] == "gpt-4"
        assert correction.context["version"] == "1.0"

    def test_with_skill_path(self, temp_dir):
        """Test decoration with skill path"""
        skill_path = f"{temp_dir}/skill"

        @with_correction_tracking(base_path=temp_dir, skill_path=skill_path)
        def extract_data(doc_path: str) -> dict:
            return {"field": "value"}

        assert extract_data._iterata_loop.skill_path is not None

    def test_with_auto_explain(self, temp_dir):
        """Test decoration with auto-explain enabled"""
        from iterata.backends.mock import MockExplainer

        explainer = MockExplainer()

        @with_correction_tracking(
            base_path=temp_dir, auto_explain=True, explainer=explainer
        )
        def extract_data(doc_path: str) -> dict:
            return {"field": "value"}

        correction = extract_data.log_correction(
            original="test", corrected="fixed", document_id="doc.pdf"
        )

        # Should be auto-explained
        loop = extract_data._iterata_loop
        explained = loop.storage.load_corrections(status="explained")
        assert len(explained) == 1

    def test_multiple_decorated_functions(self, temp_dir):
        """Test multiple decorated functions with separate tracking"""
        temp_dir_1 = f"{temp_dir}/func1"
        temp_dir_2 = f"{temp_dir}/func2"

        @with_correction_tracking(base_path=temp_dir_1)
        def extract_invoices(doc_path: str) -> dict:
            return {"amount": "100"}

        @with_correction_tracking(base_path=temp_dir_2)
        def extract_receipts(doc_path: str) -> dict:
            return {"total": "200"}

        # Log corrections to each
        extract_invoices.log_correction(
            original="100", corrected="100.00", document_id="inv.pdf"
        )
        extract_receipts.log_correction(
            original="200", corrected="200.00", document_id="rec.pdf"
        )

        # Each should have their own stats
        stats_1 = extract_invoices.get_stats()
        stats_2 = extract_receipts.get_stats()

        assert stats_1["total_corrections"] == 1
        assert stats_2["total_corrections"] == 1

    def test_wrapped_function_preserves_metadata(self, temp_dir):
        """Test that wrapper preserves original function metadata"""

        @with_correction_tracking(base_path=temp_dir)
        def extract_data(doc_path: str) -> dict:
            """Extract data from document"""
            return {"field": "value"}

        assert extract_data.__name__ == "extract_data"
        assert extract_data.__doc__ == "Extract data from document"


class TestTrackCorrections:
    def test_with_existing_loop(self, temp_dir):
        """Test decorator with existing CorrectionLoop instance"""
        loop = CorrectionLoop(base_path=temp_dir)

        @track_corrections(loop)
        def extract_data(doc_path: str) -> dict:
            return {"field": "value"}

        result = extract_data("test.pdf")

        assert result == {"field": "value"}
        assert hasattr(extract_data, "log_correction")
        assert hasattr(extract_data, "_iterata_loop")
        assert extract_data._iterata_loop is loop

    def test_shared_loop_instance(self, temp_dir):
        """Test multiple functions sharing the same loop instance"""
        loop = CorrectionLoop(base_path=temp_dir)

        @track_corrections(loop)
        def extract_invoices(doc_path: str) -> dict:
            return {"amount": "100"}

        @track_corrections(loop)
        def extract_receipts(doc_path: str) -> dict:
            return {"total": "200"}

        # Log corrections from both functions
        extract_invoices.log_correction(
            original="100", corrected="100.00", document_id="inv.pdf"
        )
        extract_receipts.log_correction(
            original="200", corrected="200.00", document_id="rec.pdf"
        )

        # Both should share the same stats
        stats = loop.get_stats()
        assert stats["total_corrections"] == 2

    def test_function_context_in_shared_loop(self, temp_dir):
        """Test that function context is correctly set even with shared loop"""
        loop = CorrectionLoop(base_path=temp_dir)

        @track_corrections(loop)
        def function_a(doc_path: str) -> dict:
            return {"field": "value"}

        @track_corrections(loop)
        def function_b(doc_path: str) -> dict:
            return {"field": "value"}

        corr_a = function_a.log_correction(
            original="test_a", corrected="fixed_a", document_id="doc_a.pdf"
        )
        corr_b = function_b.log_correction(
            original="test_b", corrected="fixed_b", document_id="doc_b.pdf"
        )

        assert corr_a.context["function"] == "function_a"
        assert corr_b.context["function"] == "function_b"


class TestDecoratorIntegration:
    def test_complete_workflow(self, temp_dir):
        """Test complete workflow with decorated function"""

        @with_correction_tracking(
            base_path=temp_dir, skill_path=f"{temp_dir}/skill"
        )
        def extract_invoice_data(invoice_path: str) -> dict:
            # Simulated extraction
            return {
                "amount": "1,234.56",
                "date": "01/15/2024",
                "vendor": "ACME",
            }

        # Extract data
        result = extract_invoice_data("invoice_001.pdf")

        # Log corrections
        extract_invoice_data.log_correction(
            original=result["amount"],
            corrected="1234.56",
            document_id="invoice_001.pdf",
            field_path="amount",
        )
        extract_invoice_data.log_correction(
            original=result["date"],
            corrected="2024-01-15",
            document_id="invoice_001.pdf",
            field_path="date",
        )

        # Get stats
        stats = extract_invoice_data.get_stats()
        assert stats["total_corrections"] == 2

        # Add more corrections to enable skill generation
        loop = extract_invoice_data._iterata_loop
        for i in range(10):
            corr = extract_invoice_data.log_correction(
                original=f"test_{i}",
                corrected=f"fixed_{i}",
                document_id=f"doc_{i}.pdf",
            )
            # Explain the correction so it's counted for skill readiness
            loop.logger.explain_pending(corr.correction_id, explanation_text="Test correction")

        # Check readiness
        readiness = extract_invoice_data.check_readiness()
        assert readiness["corrections_count"] >= 10

    def test_decorator_with_additional_log_kwargs(self, temp_dir):
        """Test that additional kwargs are passed to log method"""

        @with_correction_tracking(base_path=temp_dir)
        def extract_data(doc_path: str) -> dict:
            return {"field": "value"}

        correction = extract_data.log_correction(
            original="test",
            corrected="fixed",
            document_id="doc.pdf",
            field_path="test_field",
            confidence_before=0.85,
            corrector_id="user_123",
        )

        assert correction.field_path == "test_field"
        assert correction.confidence_before == 0.85
        assert correction.corrector_id == "user_123"
