"""Response item model for AEAT responses"""

from dataclasses import dataclass, field as dataclass_field
from typing import Optional

from ..records.invoice_identifier import InvoiceIdentifier
from .item_status import ItemStatus
from .record_type import RecordType


@dataclass
class ResponseItem:
    """
    Response for a record submission

    Represents RespuestaLinea from AEAT response
    """

    invoice_id: InvoiceIdentifier
    """ID de factura (IDFactura)"""

    record_type: RecordType
    """Tipo de registro de operación (TipoOperacion)"""

    status: ItemStatus
    """Estado del envío del registro (EstadoRegistro)"""

    is_correction: bool = False
    """Indicador de subsanación (Subsanacion)"""

    error_code: Optional[str] = None
    """Código de error (CodigoErrorRegistro)"""

    error_description: Optional[str] = None
    """Descripción del error (DescripcionErrorRegistro)"""
