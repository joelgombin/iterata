"""
Basic usage example of iterata

This example demonstrates how to:
1. Initialize a CorrectionLogger
2. Log corrections
3. Add explanations
4. Load and review corrections
"""

from iterata import CorrectionLogger

# Initialize the logger
logger = CorrectionLogger(base_path="./corrections_example")

print("=== Basic Usage Example ===\n")

# Example 1: Log a simple correction
print("1. Logging a decimal format correction...")
correction1 = logger.log(
    original="1.234,56",
    corrected="1234.56",
    document_id="invoice_001.pdf",
    field_path="total_amount",
    context={
        "model": "claude-sonnet-4",
        "extraction_method": "vision",
        "document_type": "invoice",
    },
)
print(f"   ✓ Saved correction {correction1.correction_id[:8]}...")

# Example 2: Log with confidence score
print("\n2. Logging a vendor name correction with confidence score...")
correction2 = logger.log(
    original="ACME",
    corrected="ACME Corporation",
    document_id="invoice_002.pdf",
    field_path="vendor_name",
    confidence_before=0.65,
    corrector_id="user_alice",
    context={"model": "claude-sonnet-4", "document_type": "invoice"},
)
print(f"   ✓ Saved correction {correction2.correction_id[:8]}...")

# Example 3: Log with human explanation
print("\n3. Logging a date correction...")
correction3 = logger.log(
    original="01/02/2024",
    corrected="2024-02-01",
    document_id="invoice_003.pdf",
    field_path="invoice_date",
    corrector_id="user_bob",
    context={"document_type": "invoice"},
)
print(f"   ✓ Saved correction {correction3.correction_id[:8]}...")

# Add explanation to the third correction
print("\n4. Adding explanation to correction 3...")
logger.explain_pending(
    correction3.correction_id,
    explanation_text="Le format de date devrait être ISO 8601 (YYYY-MM-DD)",
)
print("   ✓ Explanation added and correction moved to 'explained'")

# Load and display statistics
print("\n5. Loading corrections statistics...")
all_corrections = logger.storage.load_corrections(status="all")
inbox_corrections = logger.storage.load_corrections(status="inbox")
explained_corrections = logger.storage.load_corrections(status="explained")

print(f"   Total corrections: {len(all_corrections)}")
print(f"   Pending in inbox: {len(inbox_corrections)}")
print(f"   Explained: {len(explained_corrections)}")

# Display pending corrections
print("\n6. Pending corrections to explain:")
for corr in inbox_corrections:
    print(f"   - {corr.correction_id[:8]}... | {corr.field_path}")
    print(f"     {corr.original_value} → {corr.corrected_value}")

print("\n✓ Example completed successfully!")
print(f"Check the './corrections_example' directory to see the stored corrections.")
