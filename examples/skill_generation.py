"""
Skill Generation Example

This example demonstrates how to:
1. Log corrections over time
2. Analyze patterns
3. Generate a complete Claude Skill
4. Use the generated skill

This is the complete workflow: from corrections to production skill.
"""

from iterata import CorrectionLogger, SkillGenerator
from pathlib import Path

print("=== Skill Generation Example ===\n")
print("This example shows the complete workflow from logging corrections")
print("to generating a production-ready Claude Skill.\n")

# === STEP 1: Log Corrections ===
print("STEP 1: Logging corrections from document extraction...\n")

logger = CorrectionLogger(base_path="./corrections_for_skill")

# Simulate 30+ corrections across different categories
corrections_data = [
    # Decimal format errors (15 corrections)
    *[
        {
            "original": f"1.{i:03d},50",
            "corrected": f"1{i:03d}.50",
            "document_id": f"invoice_{i:04d}.pdf",
            "field_path": "invoice.total_amount",
            "explanation": "Le séparateur décimal français (virgule) doit être converti en point",
        }
        for i in range(15)
    ],
    # Date format errors (10 corrections)
    *[
        {
            "original": f"{i+1:02d}/01/2024",
            "corrected": f"2024-01-{i+1:02d}",
            "document_id": f"invoice_{100+i:04d}.pdf",
            "field_path": "invoice.invoice_date",
            "explanation": "Format de date doit suivre la norme ISO 8601 (YYYY-MM-DD)",
        }
        for i in range(10)
    ],
    # Vendor name completeness (8 corrections)
    *[
        {
            "original": f"ACME{i}",
            "corrected": f"ACME Corporation {i}",
            "document_id": f"invoice_{200+i:04d}.pdf",
            "field_path": "invoice.vendor_name",
            "explanation": "Le nom complet légal de l'entreprise est requis (règle métier)",
        }
        for i in range(8)
    ],
]

print(f"Logging {len(corrections_data)} corrections...")

for idx, data in enumerate(corrections_data, 1):
    corr = logger.log(
        original=data["original"],
        corrected=data["corrected"],
        document_id=data["document_id"],
        field_path=data["field_path"],
        confidence_before=0.75,
        corrector_id="validation_team",
        context={"batch": "2024-Q1", "model": "claude-sonnet-4", "doc_type": "invoice"},
    )
    logger.explain_pending(corr.correction_id, explanation_text=data["explanation"])

    if idx % 10 == 0:
        print(f"  ... logged {idx}/{len(corrections_data)}")

print(f"✓ Logged all {len(corrections_data)} corrections\n")

# === STEP 2: Check if ready to generate skill ===
print("STEP 2: Checking if we have enough data to generate a skill...\n")

generator = SkillGenerator(logger.storage)
readiness = generator.can_generate_skill(min_corrections=25)

print(f"Readiness check:")
print(f"  Corrections: {readiness['corrections_count']}/{readiness['min_required']}")
print(f"  Patterns detected: {readiness['patterns_count']}")
print(f"  Status: {readiness['reason']}")
print(f"  Ready: {'✓ Yes' if readiness['ready'] else '✗ No'}\n")

if not readiness["ready"]:
    print("⚠ Not enough data to generate skill yet. Add more corrections!\n")
    exit(0)

# === STEP 3: Generate the skill ===
print("STEP 3: Generating Claude Skill...\n")

skill_path = "./invoice-extraction-skill"
skill_name = "invoice-extraction-expert"

print(f"Generating skill: {skill_name}")
print(f"Output directory: {skill_path}\n")

skill_file = generator.generate_skill(
    skill_path=skill_path,
    skill_name=skill_name,
    min_corrections=25,
    min_pattern_occurrences=3,
)

print(f"✓ Skill generated successfully!\n")

# === STEP 4: Explore generated files ===
print("STEP 4: Exploring generated skill structure...\n")

skill_dir = Path(skill_path)

print(f"Generated files:")
print(f"  📄 {skill_file.name} - Main skill documentation")
print(f"  📄 README.md - Usage instructions")
print(f"  📁 rules/ - Business rules by category")

rules_dir = skill_dir / "rules"
if rules_dir.exists():
    for rule_file in sorted(rules_dir.glob("*.md")):
        print(f"    - {rule_file.name}")

print(f"  📁 examples/ - JSON examples for few-shot learning")
print(f"    - corrections.json - General correction examples")
print(f"    - patterns.json - Pattern-specific examples")

print(f"  📁 scripts/ - Validation utilities")
print(f"    - validate_extraction.py - Automated validation script")

print()

# === STEP 5: Preview the skill ===
print("STEP 5: Previewing SKILL.md content...\n")

with open(skill_file, encoding="utf-8") as f:
    lines = f.readlines()

print("=" * 70)
# Print first 30 lines
for line in lines[:30]:
    print(line, end="")
print("\n" + "=" * 70)
print(f"... ({len(lines)} total lines)\n")

# === STEP 6: Show skill stats ===
print("STEP 6: Skill statistics...\n")

# Read README to show stats
readme_file = skill_dir / "README.md"
with open(readme_file, encoding="utf-8") as f:
    readme_content = f.read()

# Extract overview section
import re

match = re.search(r"## Overview\n\n(.*?)\n\n", readme_content, re.DOTALL)
if match:
    print(match.group(1))

print()

# === STEP 7: Show example usage ===
print("STEP 7: How to use this skill...\n")

print("🎯 Claude Code Integration:")
print(f"   Copy the skill to your Claude Code skills directory:")
print(f"   $ cp -r {skill_path} ~/.claude/skills/")
print()

print("🔍 Standalone Validation:")
print(f"   Run the validation script on extraction results:")
print(f"   $ python {skill_path}/scripts/validate_extraction.py input.json")
print()

print("📚 Review Business Rules:")
print(f"   Check the rules directory for category-specific guidance:")
print(f"   $ ls {skill_path}/rules/")
print()

# === STEP 8: Demonstrate validation script ===
print("STEP 8: Testing the validation script...\n")

import json
import subprocess

# Create a test input
test_data = {
    "invoice_number": "INV-2024-001",
    "total_amount": "1.234,56",  # Wrong format (will be corrected)
    "invoice_date": "15/01/2024",  # Wrong format (will be corrected)
    "vendor_name": "ACME",  # Incomplete (should be flagged)
}

test_file = Path(skill_path) / "test_input.json"
with open(test_file, "w") as f:
    json.dump(test_data, f, indent=2)

print(f"Test input:")
print(json.dumps(test_data, indent=2))
print()

# Run validation script
print(f"Running validation...")
try:
    result = subprocess.run(
        ["python3", str(skill_dir / "scripts" / "validate_extraction.py"), str(test_file)],
        capture_output=True,
        text=True,
        timeout=5,
    )

    if result.returncode == 0:
        output = json.loads(result.stdout)
        print(f"✓ Validation completed\n")
        print(f"Corrected data:")
        print(json.dumps(output["data"], indent=2))
        print()

        if output["corrections_count"] > 0:
            print(f"Applied {output['corrections_count']} automatic corrections:")
            for corr in output["corrections_applied"]:
                print(f"  - {corr['field']}: '{corr['original']}' → '{corr['corrected']}'")
    else:
        print(f"Script output: {result.stderr}")

except Exception as e:
    print(f"Note: Could not run validation script: {e}")

print()

# === STEP 9: Next steps ===
print("STEP 9: Next steps and continuous improvement...\n")

print("🔄 Continuous Improvement Workflow:")
print("  1. Continue logging corrections as you process documents")
print("  2. Periodically check readiness: generator.can_generate_skill()")
print("  3. Regenerate skill when new patterns emerge:")
print(f"     generator.generate_skill(skill_path='{skill_path}')")
print("  4. Review updated rules and patterns")
print("  5. Integrate learned corrections into your ML pipeline")
print()

print("📊 Monitoring:")
print("  - Track correction rates over time")
print("  - Identify fields with highest error rates")
print("  - Measure impact of skill-based improvements")
print()

print("🚀 Production Integration:")
print("  - Use skill with Claude Code for document extraction")
print("  - Apply validation script in your data pipeline")
print("  - Train your team using the documented rules")
print("  - Share skill across your organization")
print()

# === Final summary ===
print("=" * 70)
print("✓ Skill Generation Complete!")
print("=" * 70)
print()
print(f"Skill location: {skill_path}/")
print(f"Main documentation: {skill_file}")
print(f"Total corrections used: {len(corrections_data)}")
print()
print("Your skill is ready to use! See README.md for usage instructions.")
print()

# Cleanup test file
if test_file.exists():
    test_file.unlink()
