# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PyVerifactu is a Python library for generating and submitting invoice records to the Spanish tax authority (AEAT) using the VERI*FACTU system. This is a Python port of [Verifactu-PHP](https://github.com/josemmo/Verifactu-PHP), maintaining file-by-file and model-by-model correspondence.

**Important**: The package name on PyPI is `pyverifactu`, but the Python module name is `verifactu` (install with `pip install pyverifactu` but import as `from verifactu import ...`).

## Development Commands

### Installation
```bash
# Install package in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/models/records/test_registration_record.py

# Run specific test method
pytest tests/models/records/test_registration_record.py::TestRegistrationRecord::test_calculates_hash_for_first_record

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=verifactu --cov-report=html
```

### Code Quality
```bash
# Format code (line length: 100)
black src tests

# Lint code
ruff check src tests

# Type check (strict mode with mypy)
mypy src
```

### Running Examples
```bash
python example.py
```

## Architecture

### Core Design Principles

1. **PHP Parity**: This codebase maintains exact correspondence with Verifactu-PHP for easier maintenance and synchronization. When modifying models or business logic, check the PHP version for reference.

2. **Pydantic-based Validation**: All models inherit from `verifactu.models.model.Model` (which extends Pydantic's `BaseModel`). Validation happens automatically on instantiation and can be triggered manually with `model.validate()`.

3. **Hash Chain Integrity**: Invoice records are cryptographically linked through SHA-256 hashes. The hash calculation is critical for AEAT compatibility - any changes to hash logic must maintain exact compatibility with PHP version.

### Key Components

#### Models (`src/verifactu/models/`)

**Base Classes**:
- `Model` (model.py): Abstract base providing Pydantic validation with `validate()` method
- `Record` (records/record.py): Abstract base for all invoice records with:
  - Hash chaining logic (previous_invoice_id, previous_hash, hash)
  - Common validation (hash format, correction fields, previous invoice consistency)
  - XML export structure
  - Abstract methods: `calculate_hash()`, `get_record_element_name()`, `export_custom_properties()`

**Record Types**:
- `RegistrationRecord`: Primary invoice registration with full breakdown, recipients, totals
- `CancellationRecord`: Invoice cancellation/correction records

**Supporting Models**:
- `InvoiceIdentifier`: Unique invoice identification (issuer_id, invoice_number, issue_date)
- `FiscalIdentifier` / `ForeignFiscalIdentifier`: Taxpayer/recipient information
- `BreakdownDetails`: Tax breakdown with self-validating tax calculation (±0.01 tolerance)
- `ComputerSystem`: Software system identification for AEAT

**Enums**:
- `InvoiceType`: FACTURA (F1), SIMPLIFICADA (F2), R1-R5 (corrective types)
- `TaxType`: IVA, IGIC, IPSI
- `OperationType`: SUBJECT, NON_SUBJECT, EXEMPT (with helper methods: `is_subject()`, `is_non_subject()`, `is_exempt()`)
- `RegimeType`: C01-C16 (tax regimes)
- `CorrectiveType`: SUBSTITUTION (S), DIFFERENCES (I)

#### Services (`src/verifactu/services/`)

- `AeatClient`: Handles SOAP communication with AEAT web service
  - Certificate management (PFX/PEM conversion)
  - XML request building with proper namespaces
  - Response parsing into `AeatResponse` objects
  - Test/production environment switching

#### Responses (`src/verifactu/models/responses/`)

- `AeatResponse`: Top-level response from AEAT (status, CSV, items, timestamps)
- `ResponseItem`: Per-invoice response details (status, error codes)
- Status enums: `ResponseStatus`, `ItemStatus`

#### Exceptions (`src/verifactu/exceptions/`)

- `InvalidModelException`: Wraps Pydantic ValidationError
- `AeatException`: AEAT communication errors

### Critical Validation Rules

**RegistrationRecord**:
- Total tax amount must exactly match sum of breakdown tax amounts
- Total amount allows ±0.02 tolerance from (base_amounts + tax_amounts)
- Full invoices (FACTURA, R1-R4) require at least one recipient
- Simplified invoices (SIMPLIFICADA, R5) cannot have recipients
- Corrective invoices (R1-R5) require `corrective_type` field
- Substitution correctives require `corrected_base_amount` and `corrected_tax_amount`

**BreakdownDetails**:
- Tax amount must match `base_amount × (tax_rate / 100)` within ±0.01 tolerance
- SUBJECT operations require tax_rate and tax_amount
- NON_SUBJECT/EXEMPT operations should not have tax_rate or tax_amount

**CancellationRecord**:
- Must have both `previous_invoice_id` and `previous_hash` (cannot be partial)
- Hash calculation excludes correction fields (previous_rejection, correction, external_reference)

**Record (base)**:
- Hash must be 64 uppercase hex characters (SHA-256)
- If `previous_invoice_id` provided, `previous_hash` is required (and vice versa)
- `previous_rejection='X'` only valid if `correction='S'`
- `correction='N'` incompatible with `previous_rejection='S'` or 'X'

### Hash Calculation

Hash calculation is the most critical component for AEAT interoperability. All tests verify that Python produces **identical** hashes to PHP:

**Test Verification Hashes**:
- First registration record: `F223F0A84F7D0C701C13C97CF10A1628FF9E46A003DDAEF3A804FBD799D82070`
- Registration with chain: `4566062C5A5D7DA4E0E876C0994071CD807962629F8D3C1F33B91EDAA65B2BA1`
- Cancellation record: `177547C0D57AC74748561D054A9CEC14B4C4EA23D1BEFD6F2E69E3A388F90C68`

When modifying hash-related code, always run hash verification tests to ensure compatibility.

## Testing Strategy

Tests are migrated from PHP (PHPUnit) to Python (pytest) maintaining exact test coverage. See TESTS_MIGRATION.md for detailed migration status.

**Test Coverage**:
- Model validation (valid/invalid cases)
- Hash calculations (with known test vectors)
- Enum helper methods
- Complex validation rules (totals, recipients, correctives)
- Edge cases and error messages

**Key Test Files**:
- `test_registration_record.py`: Most comprehensive (5 test methods, ~500 lines)
- `test_breakdown_details.py`: Tax calculation validation
- `test_cancellation_record.py`: Hash calculation and correction fields

## Python Configuration

**Target**: Python 3.8+ (for maximum compatibility)

**Key Dependencies**:
- `pydantic>=2.0.0`: Model validation
- `httpx>=0.27.0`, `requests>=2.31.0`: HTTP clients
- `lxml>=5.0.0`: XML processing
- `cryptography>=42.0.0`: Certificate handling
- `python-dateutil>=2.8.0`: Date utilities

**Code Style** (enforced by tools):
- Line length: 100 characters
- Black formatter with Python 3.8+ targets
- Ruff linting with strict rules (E, F, W, I, N, UP, B, A, C4, DTZ, T10, ICN, PIE, PYI, PT, Q, RSE, RET, SIM, TID, ARG, PLE, PLW, TRY, RUF)
- MyPy in strict mode (disallow_untyped_defs, disallow_incomplete_defs, etc.)

## Common Tasks

### Adding a New Model

1. Extend `verifactu.models.model.Model`
2. Add Pydantic field validators with `@field_validator`
3. Add cross-field validators with `@model_validator(mode="after")`
4. Implement validation in PHP counterpart for reference
5. Write pytest tests mirroring PHP tests

### Modifying Hash Calculation

**DO NOT** modify hash calculation without:
1. Checking PHP version for exact algorithm
2. Running all hash verification tests
3. Verifying test vectors still match expected values

### Adding Validation Rules

1. Add validator to model class (`@field_validator` or `@model_validator`)
2. Raise `ValueError` with descriptive message
3. Add test cases for both valid and invalid scenarios
4. Verify error messages in tests

### Working with AEAT Client

The `AeatClient` handles certificate conversion automatically:
- PFX/P12 files are converted to PEM format internally
- Supports both encrypted and unencrypted PEM certificates
- Use `set_production(False)` for test environment
- Response includes detailed error codes for debugging
