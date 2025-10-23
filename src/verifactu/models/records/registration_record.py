"""Registration record model"""

from __future__ import annotations

import hashlib
import re
from typing import List, Optional, Union
from pydantic import Field, field_validator, model_validator

from verifactu.models.records.record import Record
from verifactu.models.records.invoice_type import InvoiceType
from verifactu.models.records.corrective_type import CorrectiveType
from verifactu.models.records.invoice_identifier import InvoiceIdentifier
from verifactu.models.records.fiscal_identifier import FiscalIdentifier
from verifactu.models.records.foreign_fiscal_identifier import ForeignFiscalIdentifier
from verifactu.models.records.breakdown_details import BreakdownDetails


class RegistrationRecord(Record):
    """
    Registration record (invoice registration)

    Registro de alta de una factura

    @field RegistroAlta
    """

    # Indicador de subsanación de un registro de facturación de alta previamente generado
    # @field Subsanacion
    is_correction: bool = Field(False, description="Is correction flag")

    # Nombre-razón social del obligado a expedir la factura
    # @field NombreRazonEmisor
    issuer_name: str = Field(..., max_length=120, description="Issuer name (max 120 characters)")

    # Especificación del tipo de factura
    # @field TipoFactura
    invoice_type: InvoiceType = Field(..., description="Invoice type")

    # Descripción del objeto de la factura
    # @field DescripcionOperacion
    description: str = Field(..., max_length=500, description="Invoice description (max 500 characters)")

    # Destinatarios de la factura
    # @field Destinatarios
    recipients: List[Union[FiscalIdentifier, ForeignFiscalIdentifier]] = Field(
        default_factory=list, max_length=1000, description="Invoice recipients (max 1000)"
    )

    # Tipo de factura rectificativa
    # @field TipoRectificativa
    corrective_type: Optional[CorrectiveType] = Field(None, description="Corrective type")

    # Listado de facturas rectificadas
    # @field FacturasRectificadas
    corrected_invoices: List[InvoiceIdentifier] = Field(
        default_factory=list, description="Corrected invoices"
    )

    # Base imponible rectificada (para facturas rectificativas por diferencias)
    # @field ImporteRectificacion/BaseRectificada
    corrected_base_amount: Optional[str] = Field(None, description="Corrected base amount")

    # Cuota repercutida o soportada rectificada (para facturas rectificativas por diferencias)
    # @field ImporteRectificacion/CuotaRectificada
    corrected_tax_amount: Optional[str] = Field(None, description="Corrected tax amount")

    # Listado de facturas sustituidas
    # @field FacturasSustituidas
    replaced_invoices: List[InvoiceIdentifier] = Field(
        default_factory=list, description="Replaced invoices"
    )

    # Desglose de la factura
    # @field Desglose
    breakdown: List[BreakdownDetails] = Field(
        default_factory=list, min_length=1, max_length=12, description="Invoice breakdown (1-12 items)"
    )

    # Importe total de la cuota (sumatorio de la Cuota Repercutida y Cuota de Recargo de Equivalencia)
    # @field CuotaTotal
    total_tax_amount: str = Field(..., description="Total tax amount")

    # Importe total de la factura
    # @field ImporteTotal
    total_amount: str = Field(..., description="Total invoice amount")

    @field_validator("issuer_name", "description")
    @classmethod
    def validate_not_blank(cls, v: str) -> str:
        """Validate field is not blank"""
        if not v or not v.strip():
            raise ValueError("Field cannot be blank")
        return v

    @field_validator("total_tax_amount", "total_amount")
    @classmethod
    def validate_amount_format(cls, v: str) -> str:
        """Validate amount format"""
        if not v or not v.strip():
            raise ValueError("Amount cannot be blank")
        if not re.match(r"^-?\d{1,12}\.\d{2}$", v):
            raise ValueError("Amount must match format -?\\d{1,12}.\\d{2} (e.g., '100.00')")
        return v

    @field_validator("corrected_base_amount", "corrected_tax_amount")
    @classmethod
    def validate_corrected_amount_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate corrected amount format"""
        if v is not None and not re.match(r"^-?\d{1,12}\.\d{2}$", v):
            raise ValueError("Amount must match format -?\\d{1,12}.\\d{2} (e.g., '100.00')")
        return v

    @model_validator(mode="after")
    def validate_totals(self) -> "RegistrationRecord":
        """Validate total amounts match breakdown"""
        if not self.breakdown or not self.total_tax_amount or not self.total_amount:
            return self

        expected_total_tax_amount = 0.0
        total_base_amount = 0.0

        for details in self.breakdown:
            if details.tax_amount is None or details.base_amount is None:
                return self
            expected_total_tax_amount += float(details.tax_amount)
            total_base_amount += float(details.base_amount)

        expected_total_tax_amount_str = f"{expected_total_tax_amount:.2f}"
        if self.total_tax_amount != expected_total_tax_amount_str:
            raise ValueError(
                f"Expected total tax amount of {expected_total_tax_amount_str}, "
                f"got {self.total_tax_amount}"
            )

        # Validate total amount with tolerance
        valid_total_amount = False
        best_total_amount = total_base_amount + expected_total_tax_amount

        for tolerance in [0, -0.01, 0.01, -0.02, 0.02]:
            expected_total_amount = f"{best_total_amount + tolerance:.2f}"
            if self.total_amount == expected_total_amount:
                valid_total_amount = True
                break

        if not valid_total_amount:
            best_total_amount_str = f"{best_total_amount:.2f}"
            raise ValueError(
                f"Expected total amount of {best_total_amount_str}, got {self.total_amount}"
            )

        return self

    @model_validator(mode="after")
    def validate_recipients(self) -> "RegistrationRecord":
        """Validate recipients based on invoice type"""
        has_recipients = len(self.recipients) > 0

        if self.invoice_type in (InvoiceType.SIMPLIFICADA, InvoiceType.R5):
            if has_recipients:
                raise ValueError("This type of invoice cannot have recipients")
        elif not has_recipients:
            raise ValueError("This type of invoice requires at least one recipient")

        return self

    @model_validator(mode="after")
    def validate_corrective_details(self) -> "RegistrationRecord":
        """Validate corrective invoice details"""
        is_corrective = self.invoice_type in (
            InvoiceType.R1,
            InvoiceType.R2,
            InvoiceType.R3,
            InvoiceType.R4,
            InvoiceType.R5,
        )

        # Corrective type
        if is_corrective and self.corrective_type is None:
            raise ValueError("Missing type for corrective invoice")
        elif not is_corrective and self.corrective_type is not None:
            raise ValueError("This type of invoice cannot have a corrective type")

        # Corrected invoices
        if not is_corrective and len(self.corrected_invoices) > 0:
            raise ValueError("This type of invoice cannot have corrected invoices")

        # Corrected amounts
        if self.corrective_type == CorrectiveType.SUBSTITUTION:
            if self.corrected_base_amount is None:
                raise ValueError("Missing corrected base amount for corrective invoice by substitution")
            if self.corrected_tax_amount is None:
                raise ValueError("Missing corrected tax amount for corrective invoice by substitution")
        else:
            if self.corrected_base_amount is not None:
                raise ValueError("This invoice cannot have a corrected base amount")
            if self.corrected_tax_amount is not None:
                raise ValueError("This invoice cannot have a corrected tax amount")

        return self

    @model_validator(mode="after")
    def validate_replaced_invoices(self) -> "RegistrationRecord":
        """Validate replaced invoices"""
        if self.invoice_type != InvoiceType.SUSTITUTIVA and len(self.replaced_invoices) > 0:
            raise ValueError("This type of invoice cannot have replaced invoices")
        return self

    def calculate_hash(self) -> str:
        """
        Calculate record hash

        Returns:
            Expected record hash (64 uppercase hex characters)
        """
        # Format datetime without microseconds (same format as XML)
        # Use local timezone like PHP does with format('c')
        import time

        dt = self.hashed_at

        # If no timezone info, add local timezone (like PHP does)
        if dt.tzinfo is None:
            # Get local timezone offset
            if time.daylight and time.localtime().tm_isdst:
                # Daylight saving time is in effect
                offset_seconds = -time.altzone
            else:
                # Standard time
                offset_seconds = -time.timezone

            from datetime import timezone, timedelta
            local_tz = timezone(timedelta(seconds=offset_seconds))
            dt = dt.replace(tzinfo=local_tz)

        # Format: YYYY-MM-DDTHH:MM:SS+HH:MM (no microseconds!)
        dt_str = dt.strftime('%Y-%m-%dT%H:%M:%S')

        # Add timezone offset in format +HH:MM
        offset = dt.utcoffset()
        if offset is not None:
            total_seconds = int(offset.total_seconds())
            hours, remainder = divmod(abs(total_seconds), 3600)
            minutes = remainder // 60
            sign = '+' if total_seconds >= 0 else '-'
            dt_str += f'{sign}{hours:02d}:{minutes:02d}'
        else:
            dt_str += '+00:00'

        # NOTE: Values should NOT be escaped as that what the AEAT says ¯\_(ツ)_/¯
        payload = (
            f"IDEmisorFactura={self.invoice_id.issuer_id}"
            f"&NumSerieFactura={self.invoice_id.invoice_number}"
            f"&FechaExpedicionFactura={self.invoice_id.issue_date.strftime('%d-%m-%Y')}"
            f"&TipoFactura={self.invoice_type.value}"
            f"&CuotaTotal={self.total_tax_amount}"
            f"&ImporteTotal={self.total_amount}"
            f"&Huella={self.previous_hash or ''}"
            f"&FechaHoraHusoGenRegistro={dt_str}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()

    def get_record_element_name(self) -> str:
        """Get record element name for XML export"""
        return "RegistroAlta"

    def export_custom_properties(self, record_element: any) -> None:
        """Export custom record properties to XML"""
        # Implementation would go here for XML export
        # This requires an XML library which we'll implement when needed
        pass
