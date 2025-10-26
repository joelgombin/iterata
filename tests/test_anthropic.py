import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from iterata.backends.anthropic import AnthropicExplainer
from iterata import Correction, Explanation, CorrectionType, ExplanationType


@pytest.fixture
def sample_correction():
    """Create a sample correction for testing"""
    return Correction(
        correction_id="test_123",
        document_id="invoice_001.pdf",
        field_path="total_amount",
        original_value="1,234.56",
        corrected_value="1234.56",
        confidence_before=0.85,
        corrector_id="user_alice",
    )


@pytest.fixture
def mock_anthropic_response():
    """Create a mock response from Anthropic API"""
    response_data = {
        "explanation_text": "Format décimal incorrect : la virgule doit être remplacée par un point",
        "correction_type": "format_error",
        "category": "format_error",
        "automation_potential": 0.95,
        "business_rule": None,
        "tags": ["decimal", "format", "numbers"],
    }

    mock_content = Mock()
    mock_content.text = json.dumps(response_data)

    mock_response = Mock()
    mock_response.content = [mock_content]

    return mock_response


class TestAnthropicExplainer:
    def test_init_with_api_key(self):
        """Test initialization with explicit API key"""
        with patch("iterata.backends.anthropic.Anthropic") as MockAnthropic:
            explainer = AnthropicExplainer(api_key="test-key-123")

            MockAnthropic.assert_called_once_with(api_key="test-key-123")
            assert explainer.model == "claude-sonnet-4-5-20250929"

    def test_init_with_custom_model(self):
        """Test initialization with custom model"""
        with patch("iterata.backends.anthropic.Anthropic"):
            explainer = AnthropicExplainer(
                api_key="test-key", model="claude-opus-4-20250514"
            )

            assert explainer.model == "claude-opus-4-20250514"

    def test_init_from_env(self):
        """Test initialization with API key from environment"""
        with patch("iterata.backends.anthropic.Anthropic") as MockAnthropic:
            explainer = AnthropicExplainer()

            # Should use environment variable or None
            MockAnthropic.assert_called_once()

    def test_build_prompt(self, sample_correction):
        """Test prompt building"""
        with patch("iterata.backends.anthropic.Anthropic"):
            explainer = AnthropicExplainer(api_key="test-key")

            prompt = explainer._build_prompt(sample_correction)

            assert "invoice_001.pdf" in prompt
            assert "total_amount" in prompt
            assert "1,234.56" in prompt
            assert "1234.56" in prompt

    def test_explain_success(self, sample_correction, mock_anthropic_response):
        """Test successful explanation"""
        with patch("iterata.backends.anthropic.Anthropic") as MockAnthropic:
            mock_client = Mock()
            mock_client.messages.create.return_value = mock_anthropic_response
            MockAnthropic.return_value = mock_client

            explainer = AnthropicExplainer(api_key="test-key")
            explanation = explainer.explain(sample_correction)

            assert isinstance(explanation, Explanation)
            assert explanation.correction_id == "test_123"
            assert "Format décimal incorrect" in explanation.explanation_text
            assert explanation.correction_type == CorrectionType.FORMAT_ERROR
            assert explanation.category == ExplanationType.FORMAT_ERROR
            assert explanation.automation_potential == 0.95
            assert "decimal" in explanation.tags

    def test_explain_api_call_parameters(self, sample_correction, mock_anthropic_response):
        """Test that API is called with correct parameters"""
        with patch("iterata.backends.anthropic.Anthropic") as MockAnthropic:
            mock_client = Mock()
            mock_client.messages.create.return_value = mock_anthropic_response
            MockAnthropic.return_value = mock_client

            explainer = AnthropicExplainer(api_key="test-key")
            explainer.explain(sample_correction)

            # Verify the API call
            mock_client.messages.create.assert_called_once()
            call_kwargs = mock_client.messages.create.call_args[1]

            assert call_kwargs["model"] == "claude-sonnet-4-5-20250929"
            assert call_kwargs["max_tokens"] == 1024
            assert len(call_kwargs["messages"]) == 1
            assert call_kwargs["messages"][0]["role"] == "user"

    def test_explain_with_context(self, mock_anthropic_response):
        """Test explanation with additional context"""
        correction_with_context = Correction(
            document_id="doc.pdf",
            field_path="field",
            original_value="test",
            corrected_value="fixed",
            context={"model": "gpt-4", "extraction_method": "OCR"},
        )

        with patch("iterata.backends.anthropic.Anthropic") as MockAnthropic:
            mock_client = Mock()
            mock_client.messages.create.return_value = mock_anthropic_response
            MockAnthropic.return_value = mock_client

            explainer = AnthropicExplainer(api_key="test-key")
            prompt = explainer._build_prompt(correction_with_context)

            # Context should be included in prompt
            assert "gpt-4" in prompt or "OCR" in prompt

    def test_explain_json_parse_error(self, sample_correction):
        """Test handling of invalid JSON response"""
        with patch("iterata.backends.anthropic.Anthropic") as MockAnthropic:
            mock_client = Mock()

            # Invalid JSON response
            mock_content = Mock()
            mock_content.text = "This is not valid JSON"
            mock_response = Mock()
            mock_response.content = [mock_content]

            mock_client.messages.create.return_value = mock_response
            MockAnthropic.return_value = mock_client

            explainer = AnthropicExplainer(api_key="test-key")

            with pytest.raises(json.JSONDecodeError):
                explainer.explain(sample_correction)

    def test_explain_missing_fields(self, sample_correction):
        """Test handling of response with missing fields"""
        with patch("iterata.backends.anthropic.Anthropic") as MockAnthropic:
            mock_client = Mock()

            # Response missing required fields
            mock_content = Mock()
            mock_content.text = json.dumps({"explanation_text": "Test explanation"})
            mock_response = Mock()
            mock_response.content = [mock_content]

            mock_client.messages.create.return_value = mock_response
            MockAnthropic.return_value = mock_client

            explainer = AnthropicExplainer(api_key="test-key")
            explanation = explainer.explain(sample_correction)

            # Should use defaults for missing fields
            assert explanation.explanation_text == "Test explanation"
            assert explanation.correction_type == CorrectionType.OTHER
            assert explanation.category == ExplanationType.OTHER

    def test_explain_with_business_rule(self, sample_correction, mock_anthropic_response):
        """Test explanation with business rule"""
        with patch("iterata.backends.anthropic.Anthropic") as MockAnthropic:
            mock_client = Mock()

            # Response with business rule
            response_data = {
                "explanation_text": "Vendor name must be full legal name",
                "correction_type": "business_rule",
                "category": "business_rule",
                "automation_potential": 0.8,
                "business_rule": "Always use full legal entity name for vendors",
                "tags": ["vendor", "business_rule"],
            }

            mock_content = Mock()
            mock_content.text = json.dumps(response_data)
            mock_response = Mock()
            mock_response.content = [mock_content]

            mock_client.messages.create.return_value = mock_response
            MockAnthropic.return_value = mock_client

            explainer = AnthropicExplainer(api_key="test-key")
            explanation = explainer.explain(sample_correction)

            assert explanation.business_rule == "Always use full legal entity name for vendors"
            assert explanation.correction_type == CorrectionType.BUSINESS_RULE

    def test_explain_api_error(self, sample_correction):
        """Test handling of API errors"""
        with patch("iterata.backends.anthropic.Anthropic") as MockAnthropic:
            mock_client = Mock()
            mock_client.messages.create.side_effect = Exception("API Error")
            MockAnthropic.return_value = mock_client

            explainer = AnthropicExplainer(api_key="test-key")

            with pytest.raises(Exception) as exc_info:
                explainer.explain(sample_correction)

            assert "API Error" in str(exc_info.value)

    def test_explain_different_correction_types(self):
        """Test explanations for different correction types"""
        with patch("iterata.backends.anthropic.Anthropic") as MockAnthropic:
            mock_client = Mock()

            correction_types = [
                ("format_error", CorrectionType.FORMAT_ERROR, ExplanationType.FORMAT_ERROR),
                ("business_rule", CorrectionType.BUSINESS_RULE, ExplanationType.BUSINESS_RULE),
                ("model_error", CorrectionType.MODEL_ERROR, ExplanationType.MODEL_ERROR),
                ("extraction_error", CorrectionType.EXTRACTION_ERROR, ExplanationType.EXTRACTION_ERROR),
            ]

            for type_str, corr_type, expl_type in correction_types:
                response_data = {
                    "explanation_text": f"Test {type_str}",
                    "correction_type": type_str,
                    "category": type_str,
                    "automation_potential": 0.5,
                    "business_rule": None,
                    "tags": [type_str],
                }

                mock_content = Mock()
                mock_content.text = json.dumps(response_data)
                mock_response = Mock()
                mock_response.content = [mock_content]

                mock_client.messages.create.return_value = mock_response
                MockAnthropic.return_value = mock_client

                explainer = AnthropicExplainer(api_key="test-key")

                correction = Correction(
                    document_id="doc.pdf",
                    field_path="field",
                    original_value="test",
                    corrected_value="fixed",
                )

                explanation = explainer.explain(correction)

                assert explanation.correction_type == corr_type
                assert explanation.category == expl_type

    def test_automation_potential_range(self, sample_correction):
        """Test that automation potential is within valid range"""
        with patch("iterata.backends.anthropic.Anthropic") as MockAnthropic:
            mock_client = Mock()

            # Test various automation potential values
            for potential in [0.0, 0.5, 0.95, 1.0]:
                response_data = {
                    "explanation_text": "Test",
                    "correction_type": "format_error",
                    "category": "format_error",
                    "automation_potential": potential,
                    "business_rule": None,
                    "tags": [],
                }

                mock_content = Mock()
                mock_content.text = json.dumps(response_data)
                mock_response = Mock()
                mock_response.content = [mock_content]

                mock_client.messages.create.return_value = mock_response
                MockAnthropic.return_value = mock_client

                explainer = AnthropicExplainer(api_key="test-key")
                explanation = explainer.explain(sample_correction)

                assert 0.0 <= explanation.automation_potential <= 1.0
