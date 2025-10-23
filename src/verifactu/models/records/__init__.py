"""Invoice record models"""

# Enums
from .invoice_type import InvoiceType
from .tax_type import TaxType
from .operation_type import OperationType
from .regime_type import RegimeType
from .corrective_type import CorrectiveType
from .foreign_id_type import ForeignIdType

# Models
from .invoice_identifier import InvoiceIdentifier
from .fiscal_identifier import FiscalIdentifier
from .foreign_fiscal_identifier import ForeignFiscalIdentifier
from .breakdown_details import BreakdownDetails

# Records
from .record import Record
from .registration_record import RegistrationRecord
from .cancellation_record import CancellationRecord

__all__ = [
    # Enums
    "InvoiceType",
    "TaxType",
    "OperationType",
    "RegimeType",
    "CorrectiveType",
    "ForeignIdType",
    # Models
    "InvoiceIdentifier",
    "FiscalIdentifier",
    "ForeignFiscalIdentifier",
    "BreakdownDetails",
    # Records
    "Record",
    "RegistrationRecord",
    "CancellationRecord",
]
