import pytest
from datetime import datetime
from iterata.core.models import (
    Correction,
    CorrectionType,
    Explanation,
    ExplanationType,
    Pattern,
    IterataConfig,
)


class TestCorrection:
    def test_correction_creation(self):
        """Test basic correction creation"""
        correction = Correction(
            document_id="doc_001",
            field_path="invoice.total",
            original_value="1,234.56",
            corrected_value="1234.56",
        )

        assert correction.document_id == "doc_001"
        assert correction.field_path == "invoice.total"
        assert correction.original_value == "1,234.56"
        assert correction.corrected_value == "1234.56"
        assert correction.correction_id is not None
        assert isinstance(correction.timestamp, datetime)

    def test_correction_with_context(self):
        """Test correction with additional context"""
        correction = Correction(
            document_id="doc_002",
            field_path="invoice.date",
            original_value="01/02/2024",
            corrected_value="2024-02-01",
            context={"model": "claude-3", "confidence": 0.95},
        )

        assert correction.context["model"] == "claude-3"
        assert correction.context["confidence"] == 0.95

    def test_correction_with_confidence(self):
        """Test correction with confidence score"""
        correction = Correction(
            document_id="doc_003",
            field_path="invoice.vendor",
            original_value="ACME Corp",
            corrected_value="ACME Corporation",
            confidence_before=0.75,
            corrector_id="user_123",
        )

        assert correction.confidence_before == 0.75
        assert correction.corrector_id == "user_123"


class TestExplanation:
    def test_explanation_creation(self):
        """Test basic explanation creation"""
        explanation = Explanation(
            correction_id="corr_001",
            explanation_type=ExplanationType.HUMAN_PROVIDED,
            category=CorrectionType.FORMAT_ERROR,
            description="The decimal separator should be a dot, not a comma",
            explainer_id="user_456",
        )

        assert explanation.correction_id == "corr_001"
        assert explanation.explanation_type == ExplanationType.HUMAN_PROVIDED
        assert explanation.category == CorrectionType.FORMAT_ERROR
        assert "decimal separator" in explanation.description
        assert explanation.explainer_id == "user_456"

    def test_explanation_with_tags(self):
        """Test explanation with tags and confidence"""
        explanation = Explanation(
            correction_id="corr_002",
            explanation_type=ExplanationType.LLM_INFERRED,
            category=CorrectionType.BUSINESS_RULE,
            subcategory="tax_calculation",
            description="VAT should be 20% for this product category",
            confidence=0.92,
            explainer_id="claude-3",
            tags=["tax", "vat", "business_logic"],
        )

        assert explanation.subcategory == "tax_calculation"
        assert explanation.confidence == 0.92
        assert len(explanation.tags) == 3
        assert "vat" in explanation.tags


class TestPattern:
    def test_pattern_creation(self):
        """Test pattern creation"""
        pattern = Pattern(
            pattern_id="pattern_001",
            category=CorrectionType.FORMAT_ERROR,
            description="Decimal separator confusion (comma vs dot)",
            frequency=15,
            first_seen=datetime(2024, 1, 1),
            last_seen=datetime(2024, 1, 15),
            correction_ids=["c1", "c2", "c3"],
            impact="high",
            automation_potential=0.95,
        )

        assert pattern.pattern_id == "pattern_001"
        assert pattern.frequency == 15
        assert pattern.impact == "high"
        assert pattern.automation_potential == 0.95
        assert len(pattern.correction_ids) == 3


class TestIterataConfig:
    def test_config_creation(self):
        """Test configuration creation"""
        config = IterataConfig(
            base_path="./corrections",
            skill_path="./my-skill",
            auto_explain=True,
            backend="anthropic",
        )

        assert config.base_path == "./corrections"
        assert config.skill_path == "./my-skill"
        assert config.auto_explain is True
        assert config.backend == "anthropic"

    def test_config_defaults(self):
        """Test configuration with default values"""
        config = IterataConfig(base_path="./corrections")

        assert config.skill_path is None
        assert config.auto_explain is False
        assert config.backend is None
        assert config.min_corrections_for_skill == 10
        assert config.explanation_confidence_threshold == 0.8


class TestCorrectionType:
    def test_correction_types(self):
        """Test all correction type enum values"""
        assert CorrectionType.FORMAT_ERROR == "format_error"
        assert CorrectionType.BUSINESS_RULE == "business_rule"
        assert CorrectionType.MODEL_LIMITATION == "model_limitation"
        assert CorrectionType.CONTEXT_MISSING == "context_missing"
        assert CorrectionType.OCR_ERROR == "ocr_error"
        assert CorrectionType.OTHER == "other"


class TestExplanationType:
    def test_explanation_types(self):
        """Test all explanation type enum values"""
        assert ExplanationType.HUMAN_PROVIDED == "human_provided"
        assert ExplanationType.LLM_INFERRED == "llm_inferred"
        assert ExplanationType.VALIDATED == "validated"
