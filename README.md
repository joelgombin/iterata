# iterata

**Learn from human corrections to continuously improve your ML models.**

iterata helps you capture, analyze, and learn from human corrections on ML outputs. It creates a feedback loop that makes your models smarter over time by:

1. Logging corrections in a human-readable format (Markdown + YAML)
2. Analyzing patterns in corrections to identify recurring issues
3. Automatically generating Claude Skills that prevent future errors
4. Tracking improvement metrics over time

## Installation

```bash
pip install iterata

# With Claude support
pip install iterata[anthropic]

# With CLI tools
pip install iterata[cli]
```

## Quick Start

```python
from iterata import CorrectionLogger

# Initialize
logger = CorrectionLogger(base_path="./corrections")

# Log a correction
logger.log(
    original="1.234,56",
    corrected="1234.56",
    document_id="invoice_001.pdf",
    field_path="total_amount"
)
```

After collecting corrections:

```python
from iterata import CorrectionLoop

loop = CorrectionLoop(
    base_path="./corrections",
    skill_path="./my-skill"
)

# Generate a Claude Skill from your corrections
loop.update_skill()
```

## Features

- **Zero vendor lock-in**: Data stored as markdown files
- **Obsidian-compatible**: Browse corrections like a knowledge base
- **LLM-powered explanations**: Automatic categorization with Claude/GPT
- **Skill generation**: Auto-create Claude Skills from patterns
- **Progressive**: Start simple, add sophistication as needed

## Documentation

See [examples/](examples/) for complete usage examples.

## License

MIT
