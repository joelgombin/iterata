"""
Complete End-to-End Workflow Example

This example demonstrates the full iterata workflow using all features:
1. CorrectionLoop for unified API
2. Decorators for function tracking
3. Pattern detection and statistics
4. Skill generation
5. CLI integration

This is the recommended way to use iterata in production.
"""

from iterata import CorrectionLoop, with_correction_tracking
from pathlib import Path

print("=== Complete iterata Workflow ===\n")
print("This example shows the recommended production workflow.\n")

# ========== PART 1: Using CorrectionLoop (Recommended) ==========

print("PART 1: Using CorrectionLoop API\n")

# Initialize with all settings
loop = CorrectionLoop(
    base_path="./complete_corrections",
    skill_path="./complete_skill",
    auto_explain=False,  # Set to True with explainer for auto-explanation
    min_corrections_for_skill=20,
)

print("✓ Initialized CorrectionLoop\n")

# Log corrections
print("Logging corrections...")

correction_data = [
    # Format errors
    ("1,234.56", "1234.56", "invoice_001.pdf", "amount", "Decimal separator"),
    ("2,345.67", "2345.67", "invoice_002.pdf", "amount", "Decimal separator"),
    ("3,456.78", "3456.78", "invoice_003.pdf", "amount", "Decimal separator"),
    ("4,567.89", "4567.89", "invoice_004.pdf", "amount", "Decimal separator"),
    ("5,678.90", "5678.90", "invoice_005.pdf", "amount", "Decimal separator"),
    # Dates
    ("01/15/2024", "2024-01-15", "invoice_006.pdf", "date", "ISO 8601 format"),
    ("02/20/2024", "2024-02-20", "invoice_007.pdf", "date", "ISO 8601 format"),
    ("03/25/2024", "2024-03-25", "invoice_008.pdf", "date", "ISO 8601 format"),
    ("04/30/2024", "2024-04-30", "invoice_009.pdf", "date", "ISO 8601 format"),
    # Vendor names
    ("ACME", "ACME Corporation", "invoice_010.pdf", "vendor", "Full legal name"),
    ("TechCo", "TechCo Inc.", "invoice_011.pdf", "vendor", "Full legal name"),
    ("GlobalServ", "GlobalServ LLC", "invoice_012.pdf", "vendor", "Full legal name"),
]

for orig, corr, doc_id, field, reason in correction_data:
    correction = loop.log(
        original=orig,
        corrected=corr,
        document_id=doc_id,
        field_path=field,
        confidence_before=0.75,
        corrector_id="team",
    )

    # Manually explain (or use auto_explain=True with an explainer)
    loop.logger.explain_pending(correction.correction_id, explanation_text=reason)

print(f"✓ Logged {len(correction_data)} corrections\n")

# Get statistics
print("Getting statistics...\n")
stats = loop.get_stats()

print(f"Total corrections: {stats['total_corrections']}")
print(f"Explained: {stats['corrections_explained']}")
print(f"Patterns: {stats['patterns_count']}")
print(f"Explanation rate: {stats['correction_rate']:.0%}\n")

# Check if ready for skill generation
print("Checking skill readiness...\n")
readiness = loop.check_skill_readiness()

print(f"Ready: {readiness['ready']}")
print(f"Corrections: {readiness['corrections_count']}/{readiness['min_required']}")
print(f"Reason: {readiness['reason']}\n")

# Get recommendations
print("Getting recommendations...\n")
recommendations = loop.get_recommendations()

if recommendations:
    print(f"Found {len(recommendations)} recommendations:\n")
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"  {i}. [{rec['priority'].upper()}] {rec['title']}")
        print(f"     {rec['reason']}\n")

# ========== PART 2: Using Decorators ==========

print("\nPART 2: Using Decorators for Function Tracking\n")


# Decorator approach
@with_correction_tracking(base_path="./decorator_corrections")
def extract_invoice_data(invoice_path: str) -> dict:
    """Simulated extraction function"""
    # In reality, this would call your ML model
    return {
        "amount": "1,234.56",  # Wrong format
        "date": "01/15/2024",  # Wrong format
        "vendor": "ACME",  # Incomplete
    }


# Use the decorated function
print("Using decorated function...")
result = extract_invoice_data("invoice_test.pdf")
print(f"Extracted: {result}\n")

# Log corrections using the attached method
print("Logging corrections via decorator...")

extract_invoice_data.log_correction(
    original=result["amount"],
    corrected="1234.56",
    document_id="invoice_test.pdf",
    field_path="amount",
)

extract_invoice_data.log_correction(
    original=result["date"],
    corrected="2024-01-15",
    document_id="invoice_test.pdf",
    field_path="date",
)

print("✓ Corrections logged via decorator\n")

# Get stats from decorated function
decorator_stats = extract_invoice_data.get_stats()
print(f"Decorator stats: {decorator_stats['total_corrections']} corrections\n")

# ========== PART 3: Generate Skill (if ready) ==========

print("\nPART 3: Skill Generation\n")

# Add more corrections to meet minimum
print("Adding more corrections to meet minimum threshold...\n")

for i in range(15):
    correction = loop.log(
        original=f"test_{i}",
        corrected=f"fixed_{i}",
        document_id=f"doc_{i}.pdf",
        field_path="test_field",
        corrector_id="team",
    )
    loop.logger.explain_pending(correction.correction_id, explanation_text="Test correction")

readiness = loop.check_skill_readiness()
print(f"Readiness: {readiness['ready']} ({readiness['corrections_count']} corrections)\n")

if readiness["ready"]:
    print("Generating skill...\n")

    result = loop.update_skill(skill_name="complete-extraction-skill")

    if result["updated"]:
        print(f"✓ Skill generated!")
        print(f"  Location: {result['skill_file']}")
        print(f"  Corrections used: {result['total_corrections']}")
        print(f"  Patterns detected: {result['patterns_detected']}\n")

        # Show generated files
        skill_dir = Path("./complete_skill")
        if skill_dir.exists():
            print("Generated files:")
            print(f"  📄 SKILL.md")
            print(f"  📄 README.md")
            print(f"  📁 rules/ ({len(list((skill_dir / 'rules').glob('*.md')))} files)")
            print(f"  📁 examples/")
            print(f"  📁 scripts/\n")

# ========== PART 4: Export Data ==========

print("\nPART 4: Data Export\n")

# Export as JSON
json_export = loop.export_stats_json()
print(f"JSON export: {len(json_export)} characters")

# Export as CSV
csv_export = loop.export_stats_csv()
lines = csv_export.count("\n")
print(f"CSV export: {lines} lines\n")

# Save exports
with open("./complete_corrections/stats.json", "w") as f:
    f.write(json_export)

with open("./complete_corrections/corrections.csv", "w") as f:
    f.write(csv_export)

print("✓ Exports saved\n")

# ========== PART 5: Summary ==========

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70 + "\n")

summary = loop.get_summary()
print(summary)

print("\n" + "=" * 70)
print("NEXT STEPS")
print("=" * 70 + "\n")

print("1. Production Integration:")
print("   - Use CorrectionLoop in your extraction pipeline")
print("   - Enable auto_explain with AnthropicExplainer for automation")
print("   - Set up periodic skill regeneration")
print()

print("2. CLI Usage:")
print("   - Initialize: iterata init --path ./corrections")
print("   - Check stats: iterata stats --config iterata.yaml")
print("   - Update skill: iterata update-skill --config iterata.yaml")
print()

print("3. Monitoring:")
print("   - Track correction rates over time")
print("   - Review patterns monthly")
print("   - Regenerate skills when significant patterns emerge")
print()

print("4. Team Workflow:")
print("   - Share generated skills across team")
print("   - Document business rules in rules/")
print("   - Use validation scripts in production")
print()

print("✓ Complete workflow demonstrated!")
print(f"\nFiles created:")
print(f"  - ./complete_corrections/ - All corrections and metadata")
print(f"  - ./complete_skill/ - Generated Claude Skill")
print(f"  - ./decorator_corrections/ - Corrections from decorated function")
print()
