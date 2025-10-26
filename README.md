# iterata

![Version](https://img.shields.io/badge/version-1.0.0--beta-blue)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-122%20passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-75%25-yellow)

**Learn from human corrections to continuously improve your ML models.**

iterata helps you capture, analyze, and learn from human corrections on ML outputs. It creates a feedback loop that makes your models smarter over time by:

1. **Logging** corrections in human-readable format (Markdown + YAML)
2. **Analyzing** patterns to identify recurring issues
3. **Generating** Claude Skills that prevent future errors
4. **Tracking** improvement metrics over time

## Features

- **Zero vendor lock-in**: Data stored as markdown files
- **Obsidian-compatible**: Browse corrections like a knowledge base
- **LLM-powered explanations**: Automatic categorization with Claude/GPT
- **Pattern detection**: Identify recurring correction patterns automatically
- **Skill generation**: Auto-create Claude Skills from patterns
- **Progressive**: Start simple, add sophistication as needed
- **Production-ready**: CLI, decorators, and unified API

## Installation

> **Note**: iterata is currently in beta. Install directly from GitHub. PyPI release coming soon.
> **📖 Full installation guide**: See [INSTALL.md](INSTALL.md) for detailed instructions, troubleshooting, and all options.

### From GitHub (Recommended)

```bash
# Core functionality
pip install git+https://github.com/joelgombin/iterata.git

# With Claude support
pip install "git+https://github.com/joelgombin/iterata.git#egg=iterata[anthropic]"

# With CLI tools
pip install "git+https://github.com/joelgombin/iterata.git#egg=iterata[cli]"

# Full installation (recommended)
pip install "git+https://github.com/joelgombin/iterata.git#egg=iterata[anthropic,cli]"
```

### Development Installation

For development or to run examples:

```bash
# Clone the repository
git clone https://github.com/joelgombin/iterata.git
cd iterata

# Install in editable mode with all dependencies
pip install -e ".[anthropic,cli,dev]"

# Run tests
pytest

# Run examples
python examples/complete_workflow.py
```

## Quick Start

### Level 1: Simple Logging

```python
from iterata import CorrectionLogger

# Initialize logger
logger = CorrectionLogger(base_path="./corrections")

# Log a correction
logger.log(
    original="1.234,56",
    corrected="1234.56",
    document_id="invoice_001.pdf",
    field_path="total_amount"
)
```

### Level 2: Complete Workflow

```python
from iterata import CorrectionLoop

# Initialize with auto-explanation
loop = CorrectionLoop(
    base_path="./corrections",
    skill_path="./my-skill",
    auto_explain=True
)

# Log corrections
loop.log(
    original="1.234,56",
    corrected="1234.56",
    document_id="invoice_001.pdf",
    field_path="total_amount"
)

# Get statistics
stats = loop.get_stats()
print(f"Total corrections: {stats['total_corrections']}")

# Generate Claude Skill when ready
if loop.check_skill_readiness()["ready"]:
    result = loop.update_skill()
    print(f"Skill generated: {result['skill_file']}")
```

### Level 3: Decorators

```python
from iterata import with_correction_tracking

@with_correction_tracking(base_path="./corrections")
def extract_invoice_data(invoice_path: str) -> dict:
    # Your extraction logic here
    return {
        "amount": "1.234,56",
        "date": "01/15/2024",
        "vendor": "ACME Corp"
    }

# Use the function normally
result = extract_invoice_data("invoice.pdf")

# Log corrections when needed
extract_invoice_data.log_correction(
    original=result["amount"],
    corrected="1234.56",
    document_id="invoice.pdf",
    field_path="amount"
)

# Get stats
stats = extract_invoice_data.get_stats()
```

### Level 4: CLI

```bash
# Initialize a new project
iterata init --path ./my-corrections --skill-path ./my-skill

# View statistics
iterata stats --config iterata.yaml

# Check if ready to generate skill
iterata check --config iterata.yaml

# Generate or update skill
iterata update-skill --config iterata.yaml
```

## Configuration

Create `iterata.yaml`:

```yaml
base_path: ./corrections
skill_path: ./my-skill
auto_explain: true
min_corrections_for_skill: 25

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

## What Gets Generated?

When you generate a Claude Skill, iterata creates:

```
my-skill/
├── SKILL.md                    # Main skill documentation
├── README.md                   # Usage guide
├── rules/                      # Business rules by category
│   ├── format_error.md
│   ├── business_rule.md
│   └── ...
├── examples/                   # Few-shot learning examples (JSON)
│   └── corrections_examples.json
└── scripts/                    # Validation scripts
    └── validate.py
```

This skill can be used directly with Claude Code or Claude.ai to improve future extractions.

## Examples

See the [examples/](examples/) directory for complete usage examples:

- `basic_usage.py` - Core functionality
- `with_auto_explain.py` - Auto-explanation with MockExplainer
- `invoice_extraction.py` - Realistic invoice processing
- `pattern_analysis.py` - Pattern detection and statistics
- `skill_generation.py` - Skill generation workflow
- `complete_workflow.py` - Full production workflow

## Use Cases

### Document Extraction
Capture corrections on invoices, receipts, contracts, etc. and automatically generate Claude Skills that improve extraction accuracy.

### Data Validation
Log validation corrections and identify systematic data quality issues.

### Content Moderation
Track moderation decisions and build consistent policies.

### Classification Tasks
Learn from reclassification corrections to improve model accuracy.

## Architecture

```
┌─────────────────┐
│  Your ML Model  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│ Human Reviewer  │────▶│ iterata Logger   │
└─────────────────┘     └────────┬─────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
           ┌─────────────┐ ┌──────────┐ ┌─────────┐
           │  Markdown   │ │ Pattern  │ │  Stats  │
           │   Storage   │ │ Detector │ │ Engine  │
           └─────────────┘ └──────────┘ └─────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ Skill Generator │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  Claude Skill   │
                        │  (ready to use) │
                        └─────────────────┘
```

## API Overview

### Core Classes

- **`CorrectionLogger`** - Log corrections with optional auto-explanation
- **`CorrectionLoop`** - Unified API combining all functionality
- **`MarkdownStorage`** - Human-readable storage backend
- **`PatternDetector`** - Identify recurring patterns
- **`Statistics`** - Compute metrics and recommendations
- **`SkillGenerator`** - Generate Claude Skills from patterns

### Backends

- **`MockExplainer`** - Simple rule-based explainer for testing
- **`AnthropicExplainer`** - Claude-powered automatic categorization

### Decorators

- **`@with_correction_tracking`** - Track corrections for a function
- **`@track_corrections`** - Use with existing CorrectionLoop

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
python3 -m pytest -v

# Run with coverage
python3 -m pytest --cov=src/iterata --cov-report=term-missing

# Run specific example
python3 examples/complete_workflow.py
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development status.

## Data Format

Corrections are stored as Markdown files with YAML frontmatter:

```markdown
---
correction_id: abc123
timestamp: 2024-01-15T10:30:00
document_id: invoice_001.pdf
field_path: total_amount
status: explained
category: format_error
tags: [decimal, format]
---

# Correction: total_amount

**Original**: 1.234,56
**Corrected**: 1234.56

**Explanation**: Decimal separator error - comma should be replaced with dot for proper numerical format.

**Automation Potential**: 95%
```

This format is:
- Human-readable
- Version-control friendly
- Obsidian-compatible
- Easy to review and annotate

## Performance

- **Lightweight**: Minimal dependencies
- **Fast**: Pattern detection on 1000+ corrections in <1 second
- **Scalable**: Works with thousands of corrections
- **Efficient**: Only processes new data when updating skills

## Testing

- **122 tests** covering all functionality
- **75% overall coverage** (95%+ on core components)
- Comprehensive mocking for API backends
- Integration tests for complete workflows

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please read our contributing guidelines and submit pull requests.

## Citation

If you use iterata in your research or production systems, please cite:

```bibtex
@software{iterata2024,
  title = {iterata: Learn from human corrections to improve ML models},
  author = {Your Name},
  year = {2024},
  url = {https://github.com/yourusername/iterata}
}
```

## Support

- 📖 Documentation: See [examples/](examples/) and [DEVELOPMENT.md](DEVELOPMENT.md)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/iterata/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/iterata/discussions)
