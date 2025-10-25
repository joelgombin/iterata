"""
Pattern Analysis Example

This example demonstrates how to:
1. Log multiple corrections
2. Detect recurring patterns
3. Analyze statistics
4. Get recommendations for improvement
"""

from iterata import CorrectionLogger, PatternDetector, Statistics
from datetime import datetime

print("=== Pattern Analysis Example ===\n")

# Initialize logger
logger = CorrectionLogger(base_path="./corrections_patterns")

print("1. Logging 30 corrections to build a pattern database...\n")

# Simulate corrections from different categories
corrections_data = [
    # Decimal format errors (15 corrections)
    *[
        {
            "original": f"1.{i:03d},50",
            "corrected": f"1{i:03d}.50",
            "document_id": f"invoice_{i:04d}.pdf",
            "field_path": "invoice.amount",
            "explanation": "Le séparateur décimal français (virgule) doit être un point",
        }
        for i in range(15)
    ],
    # Date format errors (8 corrections)
    *[
        {
            "original": f"{i+1:02d}/01/2024",
            "corrected": f"2024-01-{i+1:02d}",
            "document_id": f"invoice_{100+i:04d}.pdf",
            "field_path": "invoice.date",
            "explanation": "Format de date ISO 8601 requis",
        }
        for i in range(8)
    ],
    # Vendor name errors (7 corrections)
    *[
        {
            "original": f"ACME{i}",
            "corrected": f"ACME Corporation {i}",
            "document_id": f"invoice_{200+i:04d}.pdf",
            "field_path": "invoice.vendor_name",
            "explanation": "Le nom complet de la société est requis (règle métier)",
        }
        for i in range(7)
    ],
]

# Log all corrections with explanations
for idx, data in enumerate(corrections_data, 1):
    corr = logger.log(
        original=data["original"],
        corrected=data["corrected"],
        document_id=data["document_id"],
        field_path=data["field_path"],
        confidence_before=0.75,
        corrector_id="analyst_team",
        context={"batch": "2024-01", "model": "claude-sonnet-4"},
    )
    logger.explain_pending(corr.correction_id, explanation_text=data["explanation"])

    if idx % 10 == 0:
        print(f"   Logged {idx}/{len(corrections_data)} corrections...")

print(f"   ✓ Logged all {len(corrections_data)} corrections\n")

# Initialize pattern detector and statistics
detector = PatternDetector(logger.storage)
stats = Statistics(logger.storage)

# === PATTERN DETECTION ===
print("2. Detecting patterns (min 3 occurrences)...\n")

patterns = detector.detect_patterns(min_occurrences=3)
print(f"   Found {len(patterns)} patterns:\n")

for i, pattern in enumerate(patterns, 1):
    print(f"   Pattern {i}:")
    print(f"   - Category: {pattern.category.value}")
    print(f"   - Description: {pattern.description}")
    print(f"   - Frequency: {pattern.frequency} occurrences")
    print(f"   - Impact: {pattern.impact}")
    print(f"   - Automation potential: {pattern.automation_potential:.0%}")
    print(f"   - First seen: {pattern.first_seen.strftime('%Y-%m-%d %H:%M')}")
    print(f"   - Last seen: {pattern.last_seen.strftime('%Y-%m-%d %H:%M')}")
    print()

# === FIELD-BASED PATTERNS ===
print("3. Detecting field-based patterns...\n")

field_patterns = detector.detect_patterns_by_field(min_occurrences=3)
print(f"   Found {len(field_patterns)} problematic fields:\n")

for pattern in field_patterns:
    print(f"   - {pattern.description}")
    print(f"     Frequency: {pattern.frequency}, Impact: {pattern.impact}")

# === TRANSFORMATION PATTERNS ===
print("\n4. Detecting transformation patterns...\n")

transformations = detector.detect_transformation_patterns(min_occurrences=3)
print(f"   Found {len(transformations)} transformation types:\n")

for transfo in transformations:
    print(f"   - Pattern: {transfo['pattern']}")
    print(f"     Frequency: {transfo['frequency']} times")
    print(f"     Examples:")
    for ex in transfo["examples"][:2]:  # Show first 2 examples
        print(f"       {ex['field']}: '{ex['original']}' → '{ex['corrected']}'")
    print()

# === STATISTICS ===
print("5. Computing statistics...\n")

stats_result = stats.compute()

print(f"   Total corrections: {stats_result['total_corrections']}")
print(f"   Explained: {stats_result['corrections_explained']}")
print(f"   Pending: {stats_result['corrections_pending']}")
print(f"   Explanation rate: {stats_result['correction_rate']:.1%}")
print()

print("   Categories breakdown:")
for category, count in sorted(
    stats_result["categories"].items(), key=lambda x: x[1], reverse=True
):
    print(f"   - {category}: {count}")
print()

print("   Top fields with corrections:")
for field, count in list(stats_result["top_fields"].items())[:5]:
    print(f"   - {field}: {count}")

# === DETAILED STATISTICS ===
print("\n6. Detailed statistics...\n")

detailed = stats.compute_detailed()

print(f"   Corrector stats:")
print(f"   - Total correctors: {detailed['corrector_stats']['total_correctors']}")
for corrector, count in detailed["corrector_stats"]["corrections_by_corrector"].items():
    print(f"   - {corrector}: {count} corrections")

print(f"\n   Confidence stats:")
conf_stats = detailed["confidence_stats"]
print(
    f"   - Average confidence before correction: {conf_stats['average_confidence']:.2%}"
)
print(f"   - Low confidence corrections (<0.5): {conf_stats['low_confidence_corrections']}")

# === PATTERN SUMMARY ===
print("\n7. Pattern summary...\n")

summary = detector.get_pattern_summary()
print(f"   Total patterns: {summary['total_patterns']}")
print(f"   High impact: {summary['high_impact_count']}")
print(f"   Medium impact: {summary['medium_impact_count']}")
print(f"   Low impact: {summary['low_impact_count']}")
print(f"   Highly automatable (>70%): {summary['highly_automatable_count']}")

print("\n   Top 3 most frequent patterns:")
for i, pattern in enumerate(summary["top_patterns"][:3], 1):
    print(f"   {i}. {pattern.description} ({pattern.frequency} times)")

print("\n   Top 3 most automatable patterns:")
for i, pattern in enumerate(summary["most_automatable"][:3], 1):
    print(
        f"   {i}. {pattern.description} ({pattern.automation_potential:.0%} automation potential)"
    )

# === RECOMMENDATIONS ===
print("\n8. Getting recommendations...\n")

recommendations = stats.get_recommendations()

print(f"   Generated {len(recommendations)} recommendations:\n")

for i, rec in enumerate(recommendations[:5], 1):  # Show top 5
    print(f"   {i}. [{rec['priority'].upper()}] {rec['title']}")
    print(f"      Type: {rec['type']}")
    print(f"      Reason: {rec['reason']}")
    print()

# === TEXT SUMMARY ===
print("9. Text summary:\n")
summary_text = stats.get_summary()
print(summary_text)

# === EXPORT ===
print("\n10. Export capabilities:")
print("   - JSON export available: stats.export_stats_json()")
print("   - CSV export available: stats.export_stats_csv()")
print()

# Save JSON export to file
import json

json_data = json.loads(stats.export_stats_json())
with open("./corrections_patterns/stats_export.json", "w") as f:
    json.dump(json_data, f, indent=2)

print("   ✓ Exported detailed statistics to stats_export.json")

# Save CSV export to file
csv_data = stats.export_stats_csv()
with open("./corrections_patterns/corrections_export.csv", "w") as f:
    f.write(csv_data)

print("   ✓ Exported corrections to corrections_export.csv")

print("\n" + "=" * 50)
print("✓ Pattern analysis completed successfully!")
print("=" * 50)

print("\nKey Insights:")
print(f"  • {len(patterns)} distinct patterns detected")
print(
    f"  • {summary['highly_automatable_count']} patterns with high automation potential"
)
print(f"  • {len(recommendations)} actionable recommendations generated")

print("\nNext steps:")
print("  1. Review high-impact patterns")
print("  2. Implement rules for highly automatable corrections")
print("  3. Create training data for the model from correction patterns")
print("  4. Generate a Claude Skill from these insights (Phase 3)")

print(f"\nFiles saved in: ./corrections_patterns/")
