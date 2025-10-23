# PyVerifactu

Python library for generating and submitting invoice records to the Spanish tax authority (AEAT) using the VERI*FACTU system.

This is a Python port of [Verifactu-PHP](https://github.com/tonibagur/Verifactu-PHP), maintaining file-by-file and model-by-model correspondence for easy maintenance and synchronization.

> **Note**: The package name on PyPI is `pyverifactu`, but the Python module name is `verifactu` (i.e., you install with `pip install pyverifactu` but import as `from verifactu import ...`).

## Requirements

- Python 3.8 or higher

## Installation

From PyPI:

```bash
pip install pyverifactu
```

For development (from source):

```bash
pip install -e .
pip install -e ".[dev]"  # with dev dependencies
```

## Usage

```python
from datetime import datetime
from verifactu.models.computer_system import ComputerSystem
from verifactu.models.records import (
    RegistrationRecord,
    InvoiceIdentifier,
    BreakdownDetails,
    FiscalIdentifier,
    InvoiceType,
    TaxType,
    RegimeType,
    OperationType,
)
from verifactu.services.aeat_client import AeatClient

# Create an invoice record
record = RegistrationRecord()
record.invoice_id = InvoiceIdentifier(
    issuer_id="A12345678",
    invoice_number="FACT-2025-001",
    issue_date=datetime(2025, 1, 1)
)
record.issuer_name = "Example Company SL"
record.invoice_type = InvoiceType.FACTURA
record.description = "Test invoice"

# Add breakdown
breakdown = BreakdownDetails(
    tax_type=TaxType.IVA,
    regime_type=RegimeType.C01,
    operation_type=OperationType.SUBJECT,
    tax_rate="21.00",
    base_amount="10.00",
    tax_amount="2.10"
)
record.breakdown = [breakdown]
record.total_tax_amount = "2.10"
record.total_amount = "12.10"

# Add recipient
recipient = FiscalIdentifier(name="John Doe", nif="12345678A")
record.recipients = [recipient]

# Calculate hash
record.hashed_at = datetime.now()
record.hash = record.calculate_hash()

# Validate
record.validate()

# Submit to AEAT (requires certificate)
system = ComputerSystem(
    vendor_name="Your Company Name",
    vendor_nif="A12345678",
    name="Test System",
    id="PA",
    version="1.0.0",
    installation_number="1234",
    only_supports_verifactu=True,
    supports_multiple_taxpayers=False,
    has_multiple_taxpayers=False
)

taxpayer = FiscalIdentifier(name="Example Company SL", nif="A12345678")
client = AeatClient(system, taxpayer)
client.set_certificate("/path/to/cert.pfx", "password")
client.set_production(False)  # Use test environment

response = await client.send([record])
print(f"Status: {response.status}")
print(f"CSV: {response.csv}")
```

## Testing

Run tests with pytest:

```bash
pytest
```

With coverage:

```bash
pytest --cov=verifactu --cov-report=html
```

## Code Quality

Format code with black:

```bash
black src tests
```

Lint with ruff:

```bash
ruff check src tests
```

Type check with mypy:

```bash
mypy src
```

## Project Structure

This project mirrors the PHP version structure:

```
src/verifactu/
├── models/
│   ├── model.py (base class)
│   ├── computer_system.py
│   ├── records/
│   │   ├── record.py (abstract base)
│   │   ├── registration_record.py
│   │   ├── cancellation_record.py
│   │   ├── invoice_identifier.py
│   │   ├── breakdown_details.py
│   │   ├── fiscal_identifier.py
│   │   ├── foreign_fiscal_identifier.py
│   │   ├── invoice_type.py (enum)
│   │   ├── tax_type.py (enum)
│   │   ├── operation_type.py (enum)
│   │   ├── regime_type.py (enum)
│   │   ├── corrective_type.py (enum)
│   │   └── foreign_id_type.py (enum)
│   └── responses/
│       ├── aeat_response.py
│       ├── response_item.py
│       ├── response_status.py (enum)
│       ├── item_status.py (enum)
│       └── record_type.py (enum)
├── services/
│   ├── aeat_client.py
│   └── qr_generator.py
└── exceptions/
    ├── aeat_exception.py
    └── invalid_model_exception.py
```

## Exención de responsabilidad
Esta librería se proporciona sin una declaración responsable al no ser un Sistema Informático de Facturación (SIF).
pyverifactu es una herramienta para crear SIFs, es tu responsabilidad auditar su código y usarlo de acuerdo a la normativa vigente.

Para más información, consulta el [Artículo 13 del RD 1007/2023](https://www.boe.es/buscar/act.php?id=BOE-A-2023-24840#a1-5).

## License

MIT License - see LICENSE file for details.

## Links

- Original PHP Version: https://github.com/josemmo/Verifactu-PHP
