"""Query filter model for AEAT invoice consultation"""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from .query_period import QueryPeriod


@dataclass
class QueryFilter:
    """
    Filter parameters for invoice queries (FiltroConsulta)

    Represents the filter criteria for querying invoices from AEAT.
    """

    period: QueryPeriod
    """Tax period to query (PeriodoImputacion) - required"""

    invoice_number: Optional[str] = None
    """Invoice number to search for (NumSerieFactura) - optional"""

    counterparty_nif: Optional[str] = None
    """NIF of the counterparty/recipient (Contraparte) - optional"""

    date_from: Optional[date] = None
    """Start date for invoice issue date filter (FechaExpedicionFactura/Desde) - optional"""

    date_to: Optional[date] = None
    """End date for invoice issue date filter (FechaExpedicionFactura/Hasta) - optional"""

    external_reference: Optional[str] = None
    """External reference (RefExterna) - optional"""

    pagination_key: Optional[str] = None
    """Pagination key for fetching next page (ClavePaginacion) - optional"""

    show_issuer_name: bool = True
    """Include issuer name in response (MostrarNombreRazonEmisor) - increases response time"""

    show_computer_system: bool = False
    """Include computer system info in response (MostrarSistemaInformatico) - must be N for recipient queries"""

    def __post_init__(self) -> None:
        """Validate filter values"""
        if self.date_from and self.date_to:
            if self.date_from > self.date_to:
                raise ValueError("date_from cannot be after date_to")
