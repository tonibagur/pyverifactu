# Verifactu-Python Installation Guide

## Prerequisites

- Python 3.8 or higher
- pip or conda package manager

## Installation with Conda (Recommended)

If you have a conda environment named `verifactu`, activate it and install:

```bash
conda activate verifactu
cd /Users/toni/dev/Verifactu-PHP/python
pip install -e .
```

## Installation with pip

```bash
cd /Users/toni/dev/Verifactu-PHP/python
pip install -e .
```

## Development Installation

To install with development dependencies:

```bash
pip install -e ".[dev]"
```

## Running the Example

After installation, you can run the example:

```bash
cd /Users/toni/dev/Verifactu-PHP/python
python example.py
```

This will demonstrate:
- Creating an invoice registration record
- Setting up recipients and breakdown details
- Calculating and validating hashes
- Computer system configuration

## Project Structure

```
python/
├── src/verifactu/          # Main package
│   ├── models/              # Data models
│   │   ├── records/         # Invoice records (registration, cancellation)
│   │   └── responses/       # AEAT response models
│   ├── services/            # Services (AEAT client, QR generator)
│   └── exceptions/          # Custom exceptions
├── tests/                   # Unit tests (pytest)
├── example.py               # Usage example
├── pyproject.toml           # Package configuration
└── README.md                # Package documentation
```

## Running Tests

To run the unit tests (once ported):

```bash
pytest
```

With coverage:

```bash
pytest --cov=verifactu --cov-report=html
```

## Code Quality Tools

Format code:
```bash
black src tests
```

Lint code:
```bash
ruff check src tests
```

Type checking:
```bash
mypy src
```

## Next Steps

1. Install the package in your conda environment
2. Run `python example.py` to test basic functionality
3. Review the test files once they are ported
4. Use the library in your projects

## Troubleshooting

### Import Errors

If you get import errors, make sure you installed the package:
```bash
pip install -e .
```

### Missing Dependencies

If you get missing dependency errors:
```bash
pip install pydantic httpx lxml cryptography python-dateutil
```

### Conda Environment Issues

If you can't activate the conda environment:
```bash
# List available environments
conda env list

# Create the environment if it doesn't exist
conda create -n verifactu python=3.11
conda activate verifactu
```
