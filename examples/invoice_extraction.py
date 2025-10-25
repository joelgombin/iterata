"""
Realistic invoice extraction example

This example simulates a real-world scenario where an ML model extracts data
from invoices, and human reviewers correct mistakes.
"""

from iterata import CorrectionLogger
from datetime import datetime
import json

# Simulated ML extraction results
ml_extractions = [
    {
        "document_id": "INV-2024-001.pdf",
        "extracted": {
            "invoice_number": "INV-001",
            "date": "01/15/2024",
            "vendor": "Acme Inc",
            "total": "1.234,56",
            "currency": "EUR",
        },
        "corrected": {
            "invoice_number": "INV-0001",  # Missing leading zero
            "date": "2024-01-15",  # Wrong format
            "vendor": "ACME Inc.",  # Wrong capitalization and missing dot
            "total": "1234.56",  # Wrong decimal separator
            "currency": "EUR",
        },
        "explanations": {
            "invoice_number": "Le numéro devrait avoir 4 chiffres avec des zéros en tête",
            "date": "Format de date devrait être ISO 8601",
            "vendor": "Nom de société avec capitalisation correcte et point final",
            "total": "Séparateur décimal devrait être un point, pas une virgule",
        },
    },
    {
        "document_id": "INV-2024-002.pdf",
        "extracted": {
            "invoice_number": "INV-002",
            "date": "02/28/2024",
            "vendor": "TechCorp",
            "total": "5.678,90",
            "currency": "EUR",
        },
        "corrected": {
            "invoice_number": "INV-0002",
            "date": "2024-02-28",
            "vendor": "TechCorp Ltd.",
            "total": "5678.90",
            "currency": "EUR",
        },
        "explanations": {
            "invoice_number": "Format avec zéros en tête",
            "date": "Format ISO 8601",
            "vendor": "Nom légal complet avec suffixe Ltd.",
            "total": "Séparateur décimal incorrect",
        },
    },
    {
        "document_id": "INV-2024-003.pdf",
        "extracted": {
            "invoice_number": "INV-3",
            "date": "03/01/2024",
            "vendor": "Global Services",
            "total": "12,345.67",
            "currency": "USD",
        },
        "corrected": {
            "invoice_number": "INV-0003",
            "date": "2024-03-01",
            "vendor": "Global Services LLC",
            "total": "12345.67",  # Remove thousands separator
            "currency": "USD",
        },
        "explanations": {
            "invoice_number": "Format standardisé avec 4 chiffres",
            "date": "Format ISO 8601",
            "vendor": "Inclure le suffixe légal LLC",
            "total": "Pas de séparateur de milliers dans notre système",
        },
    },
]

# Initialize logger
logger = CorrectionLogger(base_path="./corrections_invoices")

print("=== Invoice Extraction Corrections ===\n")
print("Simulating human review of ML extractions...\n")

correction_count = 0

for invoice in ml_extractions:
    doc_id = invoice["document_id"]
    print(f"Processing {doc_id}:")

    for field, original_value in invoice["extracted"].items():
        corrected_value = invoice["corrected"][field]

        # Only log if there's a correction
        if original_value != corrected_value:
            correction_count += 1

            # Log the correction
            correction = logger.log(
                original=original_value,
                corrected=corrected_value,
                document_id=doc_id,
                field_path=f"invoice.{field}",
                corrector_id="human_reviewer",
                context={
                    "model": "claude-sonnet-4",
                    "extraction_method": "vision",
                    "document_type": "invoice",
                    "review_date": datetime.now().isoformat(),
                },
            )

            # Add human explanation
            if field in invoice["explanations"]:
                logger.explain_pending(
                    correction.correction_id, explanation_text=invoice["explanations"][field]
                )

            print(f"  ✓ {field}: {original_value} → {corrected_value}")

    print()

# Generate statistics
print("=== Summary ===\n")
all_corrections = logger.storage.load_corrections(status="all")
explained = logger.storage.load_corrections(status="explained")

print(f"Total corrections: {len(all_corrections)}")
print(f"Explained: {len(explained)}")
print(f"Documents processed: {len(ml_extractions)}")

# Analyze by field
field_corrections = {}
for corr in all_corrections:
    field = corr.field_path
    if field not in field_corrections:
        field_corrections[field] = 0
    field_corrections[field] += 1

print("\nCorrections by field:")
for field, count in sorted(field_corrections.items(), key=lambda x: x[1], reverse=True):
    print(f"  {field}: {count}")

print("\n✓ Invoice extraction corrections logged successfully!")
print("Next steps:")
print("  1. Review corrections in './corrections_invoices/'")
print("  2. Analyze patterns to identify systematic issues")
print("  3. Generate a Claude Skill to improve future extractions")
