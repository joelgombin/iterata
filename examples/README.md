# Examples

This directory contains usage examples for the iterata library.

## Running the examples

Make sure you have installed iterata first:

```bash
pip install -e ..
```

Then run any example:

```bash
python basic_usage.py
python with_auto_explain.py
python invoice_extraction.py
python pattern_analysis.py
python skill_generation.py
```

## Examples overview

### 1. basic_usage.py

Demonstrates the core functionality:
- Creating a CorrectionLogger
- Logging corrections with context
- Adding explanations manually
- Loading and reviewing corrections

**Use this example to**: Get started with iterata basics

### 2. with_auto_explain.py

Shows how to use automatic explanation generation:
- Using MockExplainer for automatic categorization
- Enabling auto-explain mode
- Overriding with human explanations

**Use this example to**: Learn about automated correction explanation

### 3. invoice_extraction.py

A realistic scenario simulating invoice data extraction:
- Processing multiple invoices
- Logging field-level corrections
- Adding domain-specific explanations
- Generating statistics

**Use this example to**: See how iterata fits into a real ML pipeline

### 4. pattern_analysis.py (NEW - Phase 2)

Advanced pattern detection and statistical analysis:
- Detecting recurring patterns (by category and field)
- Identifying transformation patterns
- Computing detailed statistics
- Getting actionable recommendations
- Exporting data (JSON, CSV)

**Use this example to**: Learn how to analyze correction patterns and get insights for improvement

### 5. skill_generation.py (NEW - Phase 3)

Complete workflow from corrections to Claude Skill generation:
- Logging corrections from document extraction
- Checking readiness for skill generation
- Generating a complete Claude Skill with:
  - SKILL.md documentation
  - Business rules by category
  - Few-shot learning examples (JSON)
  - Validation scripts
- Using the generated skill

**Use this example to**: See the complete end-to-end workflow and generate production-ready Claude Skills

## Next steps

After running these examples:

1. Explore the generated `corrections_*` directories to see the markdown files
2. Try modifying the examples with your own data
3. Use pattern analysis to identify areas for improvement
4. Generate Claude Skills from your corrections
5. Integrate generated skills in your production pipeline

## Using with real LLMs

To use with Claude instead of MockExplainer:

```python
from iterata import CorrectionLogger
from iterata.backends.anthropic import AnthropicExplainer

explainer = AnthropicExplainer(
    api_key="your-api-key",
    model="claude-sonnet-4-5-20250929"
)

logger = CorrectionLogger(
    base_path="./corrections",
    explainer=explainer,
    auto_explain=True
)
```

Note: You'll need to install the anthropic extra:
```bash
pip install iterata[anthropic]
```
