# Installation Guide

iterata is currently in **beta** and not yet published on PyPI. You can install it directly from GitHub.

## Quick Installation

### Option 1: Full Installation (Recommended)

Install with all features (Claude integration + CLI):

```bash
pip install "git+https://github.com/joelgombin/iterata.git#egg=iterata[anthropic,cli]"
```

### Option 2: Core Only

Install just the core functionality:

```bash
pip install git+https://github.com/joelgombin/iterata.git
```

### Option 3: With Specific Extras

```bash
# With Claude support only
pip install "git+https://github.com/joelgombin/iterata.git#egg=iterata[anthropic]"

# With CLI tools only
pip install "git+https://github.com/joelgombin/iterata.git#egg=iterata[cli]"
```

## Development Installation

For contributing or running examples:

```bash
# Clone the repository
git clone https://github.com/joelgombin/iterata.git
cd iterata

# Install in editable mode with all dependencies
pip install -e ".[anthropic,cli,dev]"

# Verify installation
iterata --version

# Run tests
pytest -v

# Run examples
python examples/complete_workflow.py
```

## Install from Specific Branch/Tag

```bash
# Install from a specific branch
pip install "git+https://github.com/joelgombin/iterata.git@branch-name#egg=iterata[anthropic,cli]"

# Install from a specific tag/release
pip install "git+https://github.com/joelgombin/iterata.git@v1.0.0#egg=iterata[anthropic,cli]"

# Install from a specific commit
pip install "git+https://github.com/joelgombin/iterata.git@abc1234#egg=iterata[anthropic,cli]"
```

## Verify Installation

After installation, verify everything works:

```bash
# Check version
python -c "import iterata; print(iterata.__version__)"

# Check CLI (if installed with [cli])
iterata --help

# Test import
python -c "from iterata import CorrectionLoop; print('✓ iterata installed successfully')"
```

## Dependencies

### Core Dependencies (always installed)
- `pyyaml>=6.0`
- `python-frontmatter>=1.0.0`
- `pydantic>=2.0.0`

### Optional Dependencies

**Anthropic** (`[anthropic]`):
- `anthropic>=0.40.0` - For Claude API integration and auto-explanations

**CLI** (`[cli]`):
- `click>=8.0` - Command-line interface framework
- `rich>=13.0` - Beautiful terminal formatting

**Development** (`[dev]`):
- `pytest>=7.0` - Testing framework
- `pytest-cov>=4.0` - Coverage reporting
- `black>=23.0` - Code formatting
- `ruff>=0.1.0` - Linting
- `mypy>=1.0` - Type checking

## Requirements

- Python 3.9 or higher
- pip (Python package installer)
- git (for installing from GitHub)

## Troubleshooting

### "command not found: git"

Install git:
- **macOS**: `brew install git` or download from https://git-scm.com/
- **Linux**: `sudo apt-get install git` (Ubuntu/Debian) or `sudo yum install git` (RedHat/CentOS)
- **Windows**: Download from https://git-scm.com/

### "No module named 'iterata'"

Make sure you installed with the correct syntax:
```bash
pip install "git+https://github.com/joelgombin/iterata.git"
```

Note the quotes around the URL when using extras like `[anthropic,cli]`.

### Permission errors

Use a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install "git+https://github.com/joelgombin/iterata.git#egg=iterata[anthropic,cli]"
```

Or install with `--user`:
```bash
pip install --user "git+https://github.com/joelgombin/iterata.git#egg=iterata[anthropic,cli]"
```

### SSL certificate errors

If you encounter SSL errors:
```bash
pip install --trusted-host github.com "git+https://github.com/joelgombin/iterata.git#egg=iterata[anthropic,cli]"
```

## Updating

To update to the latest version:

```bash
pip install --upgrade --force-reinstall "git+https://github.com/joelgombin/iterata.git#egg=iterata[anthropic,cli]"
```

## Uninstalling

```bash
pip uninstall iterata
```

## Virtual Environment (Recommended)

Always use a virtual environment:

```bash
# Create virtual environment
python -m venv iterata-env

# Activate (Linux/macOS)
source iterata-env/bin/activate

# Activate (Windows)
iterata-env\Scripts\activate

# Install iterata
pip install "git+https://github.com/joelgombin/iterata.git#egg=iterata[anthropic,cli]"

# When done
deactivate
```

## Docker

Example Dockerfile:

```dockerfile
FROM python:3.11-slim

# Install git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install iterata
RUN pip install "git+https://github.com/joelgombin/iterata.git#egg=iterata[anthropic,cli]"

# Verify installation
RUN iterata --version

WORKDIR /app
```

## Next Steps

After installation:
1. See [README.md](README.md) for quick start guide
2. Read [USAGE.md](USAGE.md) for comprehensive documentation
3. Try examples in `examples/` directory
4. Check [DEVELOPMENT.md](DEVELOPMENT.md) for development details

## PyPI Release

iterata will be available on PyPI soon. Once published, you'll be able to install with:

```bash
pip install iterata[anthropic,cli]
```

Stay tuned!
