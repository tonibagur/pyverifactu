"""Query response item model for individual invoice records"""

from dataclasses import dataclass, field as dataclass_field
from datetime import datetime
from typing import Optional, List

from ..records.invoice_identifier import InvoiceIdentifier
from .query_record_status import QueryRecordStatus


@dataclass
class QueryRecipient:
    """Recipient information in query response"""

    name: Optional[str] = None
    """Name of recipient (NombreRazon)"""

    nif: Optional[str] = None
    """Spanish NIF (NIF)"""

    foreign_id: Optional[str] = None
    """Foreign ID (IDOtro)"""

    country_code: Optional[str] = None
    """Country code for foreign recipients (CodigoPais)"""


@dataclass
class QueryBreakdownItem:
    """Tax breakdown item in query response"""

    tax_type: Optional[str] = None
    """Tax type - IVA, IGIC, IPSI (Impuesto)"""

    regime_type: Optional[str] = None
    """Tax regime code (ClaveRegimen)"""

    operation_type: Optional[str] = None
    """Operation qualification (CalificacionOperacion)"""

    tax_rate: Optional[str] = None
    """Tax rate percentage (TipoImpositivo)"""

    base_amount: Optional[str] = None
    """Tax base amount (BaseImponibleOimporteNoSujeto)"""

    tax_amount: Optional[str] = None
    """Tax amount (CuotaRepercutida)"""


@dataclass
class QueryPreviousRecord:
    """Information about the previous record in the chain"""

    issuer_nif: Optional[str] = None
    """NIF of the issuer of the previous invoice (IDEmisorFactura)"""

    invoice_number: Optional[str] = None
    """Invoice number of the previous invoice (NumSerieFactura)"""

    issue_date: Optional[datetime] = None
    """Issue date of the previous invoice (FechaExpedicionFactura)"""

    hash: Optional[str] = None
    """Hash of the previous record (Huella)"""


@dataclass
class QueryResponseItem:
    """
    Individual invoice record from query response

    Represents RegistroRespuestaConsultaType from AEAT.
    Contains detailed information about each invoice in the query results.
    """

    invoice_id: InvoiceIdentifier
    """Invoice identification (IDFactura)"""

    issuer_name: Optional[str] = None
    """Issuer name (NombreRazonEmisor)"""

    invoice_type: Optional[str] = None
    """Invoice type code (TipoFactura)"""

    corrective_type: Optional[str] = None
    """Corrective invoice type (TipoRectificativa)"""

    operation_date: Optional[datetime] = None
    """Date of operation (FechaOperacion)"""

    registration_date: Optional[datetime] = None
    """Date of registration (FechaHoraHusoGenRegistro)"""

    total_amount: Optional[str] = None
    """Total invoice amount (ImporteTotal)"""

    total_tax_amount: Optional[str] = None
    """Total tax amount (CuotaTotal)"""

    description: Optional[str] = None
    """Operation description (DescripcionOperacion)"""

    recipients: List[QueryRecipient] = dataclass_field(default_factory=list)
    """List of recipients (Destinatarios)"""

    breakdown: List[QueryBreakdownItem] = dataclass_field(default_factory=list)
    """Tax breakdown details (Desglose)"""

    hash: Optional[str] = None
    """Record hash (Huella)"""

    status: Optional[QueryRecordStatus] = None
    """Record status (EstadoRegistro)"""

    last_modified: Optional[datetime] = None
    """Last modification timestamp (TimestampUltimaModificacion)"""

    error_code: Optional[str] = None
    """Error code if any (CodigoErrorRegistro)"""

    error_description: Optional[str] = None
    """Error description if any (DescripcionErrorRegistro)"""

    csv: Optional[str] = None
    """CSV code from presentation (CSV)"""

    presentation_timestamp: Optional[datetime] = None
    """Presentation timestamp (TimestampPresentacion)"""

    is_first_record: bool = False
    """Whether this is the first record in the chain (PrimerRegistro=S)"""

    previous_record: Optional[QueryPreviousRecord] = None
    """Information about the previous record in the chain (RegistroAnterior)"""
