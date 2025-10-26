# iterata Usage Guide

Complete guide for using iterata in your ML pipelines.

## Table of Contents

- [Quick Start](#quick-start)
- [Basic Concepts](#basic-concepts)
- [API Levels](#api-levels)
- [Configuration](#configuration)
- [Pattern Detection](#pattern-detection)
- [Skill Generation](#skill-generation)
- [Production Workflows](#production-workflows)
- [Best Practices](#best-practices)

## Quick Start

### 1. Installation

> **Note**: iterata is currently in beta. Install directly from GitHub.

```bash
# Full installation (recommended)
pip install "git+https://github.com/joelgombin/iterata.git#egg=iterata[anthropic,cli]"
```

Or for development:

```bash
git clone https://github.com/joelgombin/iterata.git
cd iterata
pip install -e ".[anthropic,cli,dev]"
```

### 2. Initialize a Project

```bash
iterata init --path ./corrections --skill-path ./my-skill
```

This creates:
- `./corrections/` - Directory for storing corrections
- `iterata.yaml` - Configuration file

### 3. Log Your First Correction

```python
from iterata import CorrectionLoop

loop = CorrectionLoop.from_config("iterata.yaml")

# Log a correction
loop.log(
    original="1.234,56",
    corrected="1234.56",
    document_id="invoice_001.pdf",
    field_path="total_amount"
)
```

### 4. Check Progress

```bash
iterata stats --config iterata.yaml
```

### 5. Generate a Skill

Once you have enough corrections (default: 25):

```bash
iterata update-skill --config iterata.yaml
```

## Basic Concepts

### Correction

A **correction** represents a single human fix to a model output:

```python
{
    "correction_id": "abc123",
    "document_id": "invoice_001.pdf",
    "field_path": "total_amount",
    "original_value": "1.234,56",
    "corrected_value": "1234.56",
    "timestamp": "2024-01-15T10:30:00",
    "confidence_before": 0.85,
    "corrector_id": "alice"
}
```

### Explanation

An **explanation** categorizes why the correction was needed:

```python
{
    "correction_id": "abc123",
    "explanation_text": "Decimal separator error",
    "correction_type": "FORMAT_ERROR",
    "category": "format_error",
    "automation_potential": 0.95,
    "tags": ["decimal", "format"]
}
```

### Pattern

A **pattern** is a recurring type of correction:

```python
{
    "category": "format_error",
    "subcategory": "decimal_format",
    "frequency": 15,
    "impact": "high",
    "automation_potential": 0.95,
    "description": "Decimal separator (comma to dot)"
}
```

### Skill

A **skill** is a complete package for Claude containing:
- Documentation of common errors
- Business rules
- Few-shot examples
- Validation scripts

## API Levels

iterata offers 4 levels of API, from simplest to most advanced:

### Level 1: CorrectionLogger

Perfect for getting started or simple use cases.

```python
from iterata import CorrectionLogger

logger = CorrectionLogger(base_path="./corrections")

# Log a correction
logger.log(
    original="test",
    corrected="fixed",
    document_id="doc.pdf",
    field_path="field_name"
)

# Add explanation later
logger.explain_pending(
    correction_id="abc123",
    explanation_text="This was a typo"
)
```

**Use when**: You just need to log corrections without advanced features.

### Level 2: CorrectionLoop

Unified API with all features integrated.

```python
from iterata import CorrectionLoop

loop = CorrectionLoop(
    base_path="./corrections",
    skill_path="./my-skill",
    auto_explain=True  # Optional: auto-explain with LLM
)

# Log correction
loop.log(original="test", corrected="fixed", document_id="doc.pdf")

# Get statistics
stats = loop.get_stats()
recommendations = loop.get_recommendations()

# Check if ready for skill generation
if loop.check_skill_readiness()["ready"]:
    loop.update_skill()

# Export data
json_data = loop.export_stats_json()
csv_data = loop.export_stats_csv()
```

**Use when**: You want full programmatic control with all features.

### Level 3: Decorators

Seamlessly integrate correction tracking into your functions.

```python
from iterata import with_correction_tracking

@with_correction_tracking(
    base_path="./corrections",
    skill_path="./my-skill",
    auto_explain=True
)
def extract_invoice(invoice_path: str) -> dict:
    # Your extraction logic
    return extract_data(invoice_path)

# Use normally
result = extract_invoice("invoice.pdf")

# Log corrections when needed
extract_invoice.log_correction(
    original=result["amount"],
    corrected="1234.56",
    document_id="invoice.pdf",
    field_path="amount"
)

# Access stats
stats = extract_invoice.get_stats()
```

**Use when**: You want to track corrections for specific functions.

### Level 4: CLI

Command-line interface for interactive workflows.

```bash
# Initialize
iterata init --path ./corrections

# View stats
iterata stats --config iterata.yaml

# Check readiness
iterata check --config iterata.yaml

# Generate skill
iterata update-skill --config iterata.yaml --name my-skill
```

**Use when**: You prefer command-line tools or need scripts.

## Configuration

### YAML Configuration File

Create `iterata.yaml`:

```yaml
# Required
base_path: ./corrections          # Where to store corrections
skill_path: ./my-skill            # Where to generate skills

# Optional
auto_explain: true                # Auto-explain corrections
min_corrections_for_skill: 25     # Minimum before skill generation

# Backend configuration (optional)
backend:
  provider: anthropic             # or "openai" or "mock"
  api_key: ${ANTHROPIC_API_KEY}   # Use env var
  model: claude-sonnet-4-5-20250929
```

### Environment Variables

Set your API key:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

The config file uses `${VAR_NAME}` syntax for environment variables.

### Programmatic Configuration

```python
from iterata import CorrectionLoop
from iterata.backends.anthropic import AnthropicExplainer

# Manual configuration
loop = CorrectionLoop(
    base_path="./corrections",
    skill_path="./my-skill",
    explainer=AnthropicExplainer(api_key="sk-ant-..."),
    auto_explain=True,
    min_corrections_for_skill=25
)

# From config file
loop = CorrectionLoop.from_config("iterata.yaml")
```

## Pattern Detection

iterata automatically detects patterns in your corrections.

### Categories of Patterns

1. **Format Errors**: Consistent formatting issues
   - Decimal separators (comma vs dot)
   - Date formats (MM/DD/YYYY vs YYYY-MM-DD)
   - Number formatting (spaces, thousands separators)

2. **Business Rules**: Domain-specific rules
   - Vendor name standardization
   - Address formatting
   - Unit conversions

3. **Model Errors**: Systematic ML model mistakes
   - Consistent misclassifications
   - OCR errors for specific characters

4. **Extraction Errors**: Field-specific issues
   - Missing values
   - Wrong field extraction
   - Boundary detection errors

### Using Pattern Detection

```python
from iterata import Statistics, PatternDetector
from iterata.core import MarkdownStorage

storage = MarkdownStorage("./corrections")
detector = PatternDetector(storage)

# Detect all patterns
patterns = detector.detect_patterns(min_occurrences=3)

for pattern in patterns:
    print(f"Pattern: {pattern.description}")
    print(f"Frequency: {pattern.frequency}")
    print(f"Automation potential: {pattern.automation_potential}")
    print(f"Impact: {pattern.impact}")

# Detect by field
field_patterns = detector.detect_patterns_by_field()

# Detect transformation patterns
transformations = detector.detect_transformation_patterns()
```

### Pattern Metrics

Each pattern includes:

- **Frequency**: How often it occurs
- **Impact**: High/medium/low based on frequency
- **Automation Potential**: 0-1 score (how easily automated)
- **Description**: Human-readable summary
- **Examples**: Sample corrections

## Skill Generation

### When to Generate

Check if you're ready:

```python
readiness = loop.check_skill_readiness()

if readiness["ready"]:
    print(f"Ready! {readiness['corrections_count']} corrections")
    print(f"Patterns detected: {readiness['patterns_count']}")
else:
    print(readiness["reason"])
```

### Generating a Skill

```python
result = loop.update_skill(skill_name="invoice-extraction")

print(f"Skill generated at: {result['skill_file']}")
print(f"Used {result['total_corrections']} corrections")
print(f"Detected {result['patterns_count']} patterns")
```

Or via CLI:

```bash
iterata update-skill --config iterata.yaml --name invoice-extraction
```

### What Gets Generated

The skill package includes:

```
invoice-extraction/
├── SKILL.md                          # Main documentation
├── README.md                         # Usage guide
├── rules/
│   ├── format_error.md              # Business rules by category
│   ├── business_rule.md
│   ├── extraction_error.md
│   └── model_error.md
├── examples/
│   └── corrections_examples.json     # Few-shot examples
└── scripts/
    └── validate.py                   # Validation script
```

### Using Generated Skills

#### With Claude Code

1. Copy the skill to your Claude Code skills directory
2. Reference it in your prompts:

```python
# Tell Claude Code to use the skill
"""
Use the invoice-extraction skill when processing invoices.
"""
```

#### With Claude API

Include the skill content in your system prompt:

```python
with open("my-skill/SKILL.md") as f:
    skill_content = f.read()

system_prompt = f"""You are an expert invoice extractor.

{skill_content}

Follow the rules and examples carefully."""
```

## Production Workflows

### Workflow 1: Batch Processing with Corrections

```python
from iterata import CorrectionLoop

loop = CorrectionLoop.from_config("iterata.yaml")

def process_invoices(invoice_paths):
    for path in invoice_paths:
        # Extract with your model
        result = your_model.extract(path)

        # Show to human reviewer
        corrected = human_review(result)

        # Log corrections
        for field, value in corrected.items():
            if value != result.get(field):
                loop.log(
                    original=result.get(field),
                    corrected=value,
                    document_id=path,
                    field_path=field
                )

    # Weekly: check and update skill
    if loop.check_skill_readiness()["ready"]:
        loop.update_skill()
```

### Workflow 2: Real-time with Decorators

```python
from iterata import with_correction_tracking

@with_correction_tracking(
    base_path="./corrections",
    skill_path="./invoice-skill",
    auto_explain=True
)
def extract_invoice(path: str) -> dict:
    return your_model.extract(path)

# In your review UI
def on_correction_submitted(original_result, corrected_result, doc_id):
    for field, corrected_value in corrected_result.items():
        original_value = original_result.get(field)
        if original_value != corrected_value:
            extract_invoice.log_correction(
                original=original_value,
                corrected=corrected_value,
                document_id=doc_id,
                field_path=field
            )
```

### Workflow 3: Scheduled Skill Updates

```python
import schedule
from iterata import CorrectionLoop

loop = CorrectionLoop.from_config("iterata.yaml")

def update_skill_if_ready():
    readiness = loop.check_skill_readiness()

    if readiness["ready"]:
        print(f"Updating skill with {readiness['corrections_count']} corrections")
        result = loop.update_skill()
        print(f"Skill updated: {result['skill_file']}")

        # Deploy new skill
        deploy_skill(result['skill_file'])
    else:
        print(f"Not ready yet: {readiness['reason']}")

# Run weekly on Monday at 9am
schedule.every().monday.at("09:00").do(update_skill_if_ready)
```

## Best Practices

### 1. Logging Corrections

**DO:**
- Log corrections as soon as they're made
- Include relevant context (confidence scores, model versions)
- Use descriptive field paths (`invoice.line_items[0].amount` not just `amount`)
- Add corrector IDs to track who makes corrections

**DON'T:**
- Batch corrections too long (log immediately)
- Skip explanations (they're valuable for patterns)
- Use generic document IDs (be specific)

### 2. Pattern Detection

**DO:**
- Review patterns regularly (weekly/monthly)
- Set appropriate min_occurrences thresholds
- Focus on high automation potential patterns first
- Track pattern changes over time

**DON'T:**
- Set thresholds too low (creates noise)
- Ignore low-frequency high-impact patterns
- Generate skills too early (wait for patterns to emerge)

### 3. Skill Generation

**DO:**
- Wait for at least 20-30 corrections
- Regenerate skills periodically (monthly)
- Version your skills (git)
- Test new skills before deploying

**DON'T:**
- Generate with too few corrections
- Forget to update production systems with new skills
- Skip validation scripts

### 4. Team Workflows

**DO:**
- Share correction databases across team
- Standardize field naming conventions
- Document common correction types
- Review skill updates as a team

**DON'T:**
- Have each person maintain separate corrections
- Change field naming mid-project
- Deploy skill updates without review

### 5. Data Management

**DO:**
- Commit correction files to git
- Use descriptive document IDs
- Back up correction databases regularly
- Archive old corrections periodically

**DON'T:**
- Delete old corrections (archive instead)
- Store sensitive data in corrections
- Skip version control

## Advanced Features

### Custom Explainers

Create your own explainer:

```python
from iterata.backends.base import BaseExplainer
from iterata import Correction, Explanation, ExplanationType

class MyCustomExplainer(BaseExplainer):
    def explain(self, correction: Correction) -> Explanation:
        # Your logic here
        return Explanation(
            correction_id=correction.correction_id,
            explanation_text="Custom explanation",
            correction_type=CorrectionType.OTHER,
            category=ExplanationType.OTHER,
            automation_potential=0.5,
            tags=["custom"]
        )

# Use it
loop = CorrectionLoop(
    base_path="./corrections",
    explainer=MyCustomExplainer(),
    auto_explain=True
)
```

### Shared Loop Between Functions

```python
from iterata import CorrectionLoop, track_corrections

# Create one loop
loop = CorrectionLoop(base_path="./corrections")

# Share across multiple functions
@track_corrections(loop)
def extract_invoices(path):
    return extract(path)

@track_corrections(loop)
def extract_receipts(path):
    return extract(path)

# All corrections go to the same database
# Single skill generated from all corrections
```

### Export and Integration

```python
# Export to JSON
json_data = loop.export_stats_json()

# Export to CSV
csv_data = loop.export_stats_csv()

# Get recommendations
recommendations = loop.get_recommendations()

# Get detailed statistics
detailed = loop.get_detailed_stats()

# Custom analysis
from iterata.core import MarkdownStorage
storage = MarkdownStorage("./corrections")
all_corrections = storage.load_corrections()

# Your custom analysis
# ...
```

## Troubleshooting

### "Not enough corrections"

You need at least `min_corrections_for_skill` corrections (default: 10).

**Solution**: Keep logging corrections or use `force=True`:

```python
loop.update_skill(force=True)
```

### "No patterns detected"

Your corrections may not have recurring patterns yet.

**Solution**:
- Log more corrections
- Lower `min_occurrences` threshold
- Check that explanations are being added

### "Skill generation fails"

**Solution**:
- Check that `skill_path` is configured
- Ensure you have write permissions
- Check that corrections are explained

### API rate limits

When using auto-explain with Claude/GPT, you may hit rate limits.

**Solution**:
- Use batch explanation instead of auto-explain
- Add delays between explanations
- Use MockExplainer for development

## Examples

See the `examples/` directory for complete working examples:

- **basic_usage.py** - Simple logging
- **with_auto_explain.py** - Auto-explanation
- **invoice_extraction.py** - Realistic scenario
- **pattern_analysis.py** - Pattern detection
- **skill_generation.py** - Skill creation
- **complete_workflow.py** - Full production workflow

## Getting Help

- 📖 Check [README.md](README.md) for overview
- 🔧 See [DEVELOPMENT.md](DEVELOPMENT.md) for development details
- 💡 Browse examples for code samples
- 🐛 Report issues on GitHub
