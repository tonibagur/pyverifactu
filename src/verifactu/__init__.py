"""
Verifactu-Python

Python library for generating and submitting invoice records to the Spanish tax authority (AEAT)
using the VERI*FACTU system.
"""

__version__ = "1.0.0"

from .models import Model, ComputerSystem
from .models.records import (
    InvoiceType,
    TaxType,
    OperationType,
    RegimeType,
    CorrectiveType,
    ForeignIdType,
    InvoiceIdentifier,
    FiscalIdentifier,
    ForeignFiscalIdentifier,
    BreakdownDetails,
    Record,
    RegistrationRecord,
    CancellationRecord,
)
from .models.responses import (
    ResponseStatus,
    ItemStatus,
    RecordType,
    ResponseItem,
    AeatResponse,
)
from .services import AeatClient
from .exceptions import AeatException, InvalidModelException

# Rebuild models for Python 3.8 compatibility with Pydantic v2
# This ensures forward references are properly resolved
Record.model_rebuild()
RegistrationRecord.model_rebuild()
CancellationRecord.model_rebuild()

__all__ = [
    "__version__",
    # Base
    "Model",
    "ComputerSystem",
    # Enums
    "InvoiceType",
    "TaxType",
    "OperationType",
    "RegimeType",
    "CorrectiveType",
    "ForeignIdType",
    "ResponseStatus",
    "ItemStatus",
    "RecordType",
    "ResponseItem",
    "AeatResponse",
    # Services
    "AeatClient",
    # Models
    "InvoiceIdentifier",
    "FiscalIdentifier",
    "ForeignFiscalIdentifier",
    "BreakdownDetails",
    # Records
    "Record",
    "RegistrationRecord",
    "CancellationRecord",
    # Exceptions
    "AeatException",
    "InvalidModelException",
]
