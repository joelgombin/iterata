"""
Auto-explain example with MockExplainer

This example demonstrates how to use iterata with automatic explanation generation.
In production, you would use AnthropicExplainer instead of MockExplainer.
"""

from iterata import CorrectionLogger
from iterata.backends.mock import MockExplainer

# Initialize with auto-explain enabled
explainer = MockExplainer()
logger = CorrectionLogger(base_path="./corrections_auto", explainer=explainer, auto_explain=True)

print("=== Auto-Explain Example ===\n")

# When auto_explain is True, corrections are automatically explained and moved to 'explained/'
print("1. Logging corrections with auto-explain enabled...")

corrections = [
    {
        "original": "1,234.56",
        "corrected": "1234.56",
        "document_id": "doc_001.pdf",
        "field_path": "amount",
    },
    {
        "original": "20/12/2024",
        "corrected": "2024-12-20",
        "document_id": "doc_002.pdf",
        "field_path": "date",
    },
    {
        "original": "ACME",
        "corrected": "ACME Corp",
        "document_id": "doc_003.pdf",
        "field_path": "vendor",
    },
]

for i, data in enumerate(corrections, 1):
    corr = logger.log(**data)
    print(f"   {i}. Logged and explained: {corr.field_path} ({corr.correction_id[:8]}...)")

# Check that all corrections were explained automatically
print("\n2. Checking statistics...")
inbox = logger.storage.load_corrections(status="inbox")
explained = logger.storage.load_corrections(status="explained")

print(f"   Inbox: {len(inbox)} corrections")
print(f"   Explained: {len(explained)} corrections")

if len(explained) == 3:
    print("\n✓ All corrections were automatically explained!")
else:
    print("\n✗ Something went wrong with auto-explain")

# Example with human-provided explanation (overrides LLM)
print("\n3. Logging with human explanation...")
corr = logger.log(
    original="TVA 20%",
    corrected="VAT 20%",
    document_id="doc_004.pdf",
    field_path="tax_label",
    human_explanation="La taxe devrait être indiquée en anglais pour les documents internationaux",
    corrector_id="user_charlie",
)
print(f"   ✓ Correction explained by human: {corr.correction_id[:8]}...")

print("\n✓ Auto-explain example completed!")
print("Check './corrections_auto/explained/' to see the explained corrections.")
