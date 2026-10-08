"""Invoice identifier model"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import Field, field_validator
from verifactu.models.model import Model
from verifactu.exceptions.import_exception import ImportException
from verifactu.models.xml_utils import XmlInput, build, get_text, parse_date, to_element


class InvoiceIdentifier(Model):
    """
    Invoice identifier

    Identificador de factura
    """

    # Número de identificación fiscal (NIF) del obligado a expedir la factura
    # @field IDFactura/IDEmisorFactura
    issuer_id: str = Field(
        ..., min_length=9, max_length=9, description="Issuer ID (exactly 9 characters)"
    )

    # Nº Serie + Nº Factura que identifica a la factura emitida
    # @field IDFactura/NumSerieFactura
    invoice_number: str = Field(..., max_length=60, description="Invoice number (max 60 characters)")

    # Fecha de expedición de la factura
    # NOTE: Time part will be ignored.
    # @field IDFactura/FechaExpedicionFactura
    issue_date: datetime = Field(..., description="Issue date")

    def __init__(
        self,
        issuer_id: Optional[str] = None,
        invoice_number: Optional[str] = None,
        issue_date: Optional[datetime] = None,
        **data: dict,
    ) -> None:
        """
        Class constructor

        Args:
            issuer_id: Issuer ID
            invoice_number: Invoice number
            issue_date: Issue date
            **data: Additional data
        """
        if issuer_id is not None:
            data["issuer_id"] = issuer_id
        if invoice_number is not None:
            data["invoice_number"] = invoice_number
        if issue_date is not None:
            data["issue_date"] = issue_date
        super().__init__(**data)

    @field_validator("issuer_id")
    @classmethod
    def validate_issuer_id(cls, v: str) -> str:
        """Validate issuer_id is not blank"""
        if not v or not v.strip():
            raise ValueError("issuer_id cannot be blank")
        return v

    @field_validator("invoice_number")
    @classmethod
    def validate_invoice_number(cls, v: str) -> str:
        """Validate invoice_number is not blank"""
        if not v or not v.strip():
            raise ValueError("invoice_number cannot be blank")
        return v

    def equals(self, other: "InvoiceIdentifier") -> bool:
        """
        Compare instance against another invoice identifier

        Args:
            other: Other invoice identifier

        Returns:
            Whether instances are equal
        """
        return (
            self.issuer_id == other.issuer_id
            and self.invoice_number == other.invoice_number
            and self.issue_date.date() == other.issue_date.date()
        )

    @classmethod
    def from_xml(cls, xml: XmlInput) -> "InvoiceIdentifier":
        """
        Import instance from XML element

        Accepts both regular (``IDEmisorFactura``...) and cancellation
        (``IDEmisorFacturaAnulada``...) element names.

        Args:
            xml: XML element (or string) containing the identifier fields

        Returns:
            Invoice identifier

        Raises:
            ImportException: If failed to parse XML
        """
        element = to_element(xml)
        issuer_id = get_text(element, "sum1:IDEmisorFactura")
        if issuer_id is None:
            issuer_id = get_text(element, "sum1:IDEmisorFacturaAnulada")
        if issuer_id is None:
            raise ImportException("Missing <sum1:IDEmisorFactura /> element")

        invoice_number = get_text(element, "sum1:NumSerieFactura")
        if invoice_number is None:
            invoice_number = get_text(element, "sum1:NumSerieFacturaAnulada")
        if invoice_number is None:
            raise ImportException("Missing <sum1:NumSerieFactura /> element")

        raw_issue_date = get_text(element, "sum1:FechaExpedicionFactura")
        if raw_issue_date is None:
            raw_issue_date = get_text(element, "sum1:FechaExpedicionFacturaAnulada")
        if raw_issue_date is None:
            raise ImportException("Missing <sum1:FechaExpedicionFactura /> element")
        issue_date = parse_date(raw_issue_date, "FechaExpedicionFactura")

        return build(cls, issuer_id=issuer_id, invoice_number=invoice_number, issue_date=issue_date)
