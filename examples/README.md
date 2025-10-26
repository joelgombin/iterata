# Examples

This directory contains usage examples for the iterata library.

## Running the examples

### Option 1: After Installing from GitHub

If you installed iterata from GitHub:

```bash
pip install "git+https://github.com/joelgombin/iterata.git#egg=iterata[anthropic,cli]"
```

Then run examples directly:

```bash
# Download examples (if not already cloned)
git clone https://github.com/joelgombin/iterata.git
cd iterata/examples
python complete_workflow.py
```

### Option 2: Development Mode

If you cloned the repository:

```bash
# From the repository root
pip install -e ".[anthropic,cli]"
```

Then run any example:

```bash
python basic_usage.py
python with_auto_explain.py
python invoice_extraction.py
python pattern_analysis.py
python skill_generation.py
python complete_workflow.py
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

### 6. complete_workflow.py (NEW - Phase 4 & 5)

Production-ready complete workflow demonstrating all features:
- Using CorrectionLoop unified API
- Function decorators for automatic tracking
- YAML configuration files
- Skill generation and readiness checks
- Statistics and recommendations
- Data export (JSON, CSV)
- Best practices for production

**Use this example to**: See how all features work together in a production environment

## Next steps

After running these examples:

1. Explore the generated `corrections_*` directories to see the markdown files
2. Try modifying the examples with your own data
3. Use pattern analysis to identify areas for improvement
4. Generate Claude Skills from your corrections
5. Integrate generated skills in your production pipeline

## Using with Claude (Real LLM)

iterata includes a full Claude integration via AnthropicExplainer. To use it:

### Option 1: Direct API Usage

```python
from iterata import CorrectionLoop
from iterata.backends.anthropic import AnthropicExplainer

explainer = AnthropicExplainer(
    api_key="your-api-key",
    model="claude-sonnet-4-5-20250929"
)

loop = CorrectionLoop(
    base_path="./corrections",
    explainer=explainer,
    auto_explain=True
)
```

### Option 2: Configuration File

Create `iterata.yaml`:

```yaml
base_path: ./corrections
auto_explain: true

backend:
  provider: anthropic
  api_key: ${ANTHROPIC_API_KEY}
  model: claude-sonnet-4-5-20250929
```

Then use it:

```python
from iterata import CorrectionLoop

loop = CorrectionLoop.from_config("iterata.yaml")
```

**Note**: You'll need to install the anthropic extra:
```bash
pip install iterata[anthropic]
```
