"""Base invoice record model"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, TYPE_CHECKING
import re
from pydantic import Field, field_validator, model_validator

from verifactu.models.model import Model
from verifactu.models.records.invoice_identifier import InvoiceIdentifier

if TYPE_CHECKING:
    from verifactu.models.computer_system import ComputerSystem


class Record(Model, ABC):
    """
    Base invoice record

    Abstract base class for all invoice records (registration and cancellation).
    """

    # ID de factura
    # @field IDFactura
    invoice_id: InvoiceIdentifier = Field(..., description="Invoice identifier")

    # ID de factura del registro anterior
    # @field Encadenamiento/RegistroAnterior
    previous_invoice_id: Optional[InvoiceIdentifier] = Field(
        None, description="Previous invoice identifier"
    )

    # Primeros 64 caracteres de la huella o hash del registro de facturación anterior
    # @field Encadenamiento/RegistroAnterior/Huella
    previous_hash: Optional[str] = Field(
        None, min_length=64, max_length=64, description="Previous record hash (64 hex characters)"
    )

    # Huella o hash de cierto contenido de este registro de facturación
    # @field Huella
    hash: str = Field(
        "", min_length=0, max_length=64, description="Record hash (64 hex characters)"
    )

    # Fecha, hora y huso horario de generación del registro de facturación
    # @field FechaHoraHusoGenRegistro
    hashed_at: datetime = Field(..., description="Hash generation timestamp")

    # Indicador de rechazo previo
    # @field RechazoPrevio
    previous_rejection: Optional[str] = Field(
        None, description="Previous rejection indicator (S/N/X)"
    )

    # Indicador de subsanación
    # @field Subsanacion
    correction: Optional[str] = Field(None, description="Correction indicator (S/N)")

    # Referencia externa
    # @field RefExterna
    external_reference: Optional[str] = Field(
        None, max_length=60, description="External reference (max 60 characters)"
    )

    @field_validator("previous_hash")
    @classmethod
    def validate_previous_hash_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate previous hash format (64 uppercase hex characters)"""
        if v is not None and not re.match(r"^[0-9A-F]{64}$", v):
            raise ValueError("previous_hash must be 64 uppercase hexadecimal characters")
        return v

    @field_validator("hash")
    @classmethod
    def validate_hash_format(cls, v: str) -> str:
        """Validate hash format (64 uppercase hex characters)"""
        # Allow empty hash during construction (will be validated later)
        if v == "":
            return v
        if not re.match(r"^[0-9A-F]{64}$", v):
            raise ValueError("hash must be 64 uppercase hexadecimal characters")
        return v

    @field_validator("previous_rejection")
    @classmethod
    def validate_previous_rejection(cls, v: Optional[str]) -> Optional[str]:
        """Validate previous rejection is S, N, or X"""
        if v is not None and v not in ("S", "N", "X"):
            raise ValueError("previous_rejection must be 'S', 'N', or 'X'")
        return v

    @field_validator("correction")
    @classmethod
    def validate_correction(cls, v: Optional[str]) -> Optional[str]:
        """Validate correction is S or N"""
        if v is not None and v not in ("S", "N"):
            raise ValueError("correction must be 'S' or 'N'")
        return v

    @model_validator(mode="after")
    def validate_hash_value(self) -> "Record":
        """Validate hash matches calculated value"""
        # Only validate hash if it's been set (not empty)
        if self.hash and self.hash != "":
            expected_hash = self.calculate_hash()
            if self.hash != expected_hash:
                raise ValueError(f"Invalid hash, expected value {expected_hash}")
        return self

    @model_validator(mode="after")
    def validate_previous_invoice_consistency(self) -> "Record":
        """Validate previous invoice and hash are both provided or both None"""
        if self.previous_invoice_id is not None and self.previous_hash is None:
            raise ValueError("Previous hash is required if previous invoice ID is provided")
        elif self.previous_hash is not None and self.previous_invoice_id is None:
            raise ValueError("Previous invoice ID is required if previous hash is provided")
        return self

    @model_validator(mode="after")
    def validate_correction_fields(self) -> "Record":
        """Validate correction fields relationships"""
        # RechazoPrevio='X' solo si Subsanacion='S'
        if self.previous_rejection == "X" and self.correction != "S":
            raise ValueError('previous_rejection can only be "X" if correction is "S"')

        # Subsanacion='N' no puede coexistir con RechazoPrevio='S' o 'X'
        if self.correction == "N" and self.previous_rejection in ("S", "X"):
            raise ValueError('correction cannot be "N" if previous_rejection is "S" or "X"')

        # Subsanacion='S' requiere RechazoPrevio='S' o 'X' (no puede ser 'N')
        if self.correction == "S" and self.previous_rejection == "N":
            raise ValueError(
                'correction can only be "S" if previous_rejection is "S" or "X" (not "N")'
            )

        return self

    @abstractmethod
    def calculate_hash(self) -> str:
        """
        Calculate record hash

        Returns:
            Expected record hash (64 uppercase hex characters)
        """
        pass

    @abstractmethod
    def get_record_element_name(self) -> str:
        """
        Get record element name for XML export

        Returns:
            XML element name
        """
        pass

    @abstractmethod
    def export_custom_properties(self, record_element: any) -> None:
        """
        Export custom record properties to XML

        Args:
            record_element: XML record element
        """
        pass

    def export(self, xml: any, system: "ComputerSystem") -> None:
        """
        Export record to XML

        Args:
            xml: XML root element
            system: Computer system information
        """
        record_element_name = self.get_record_element_name()
        record_element = xml.add(f"sum1:{record_element_name}")
        record_element.add("sum1:IDVersion", "1.0")

        self.export_custom_properties(record_element)

        encadenamiento_element = record_element.add("sum1:Encadenamiento")
        if self.previous_invoice_id is None:
            encadenamiento_element.add("sum1:PrimerRegistro", "S")
        else:
            registro_anterior_element = encadenamiento_element.add("sum1:RegistroAnterior")
            registro_anterior_element.add("sum1:IDEmisorFactura", self.previous_invoice_id.issuer_id)
            registro_anterior_element.add(
                "sum1:NumSerieFactura", self.previous_invoice_id.invoice_number
            )
            registro_anterior_element.add(
                "sum1:FechaExpedicionFactura",
                self.previous_invoice_id.issue_date.strftime("%d-%m-%Y"),
            )
            registro_anterior_element.add("sum1:Huella", self.previous_hash)

        sistema_informatico_element = record_element.add("sum1:SistemaInformatico")
        sistema_informatico_element.add("sum1:NombreRazon", system.vendor_name)
        sistema_informatico_element.add("sum1:NIF", system.vendor_nif)
        sistema_informatico_element.add("sum1:NombreSistemaInformatico", system.name)
        sistema_informatico_element.add("sum1:IdSistemaInformatico", system.id)
        sistema_informatico_element.add("sum1:Version", system.version)
        sistema_informatico_element.add("sum1:NumeroInstalacion", system.installation_number)
        sistema_informatico_element.add(
            "sum1:TipoUsoPosibleSoloVerifactu", "S" if system.only_supports_verifactu else "N"
        )
        sistema_informatico_element.add(
            "sum1:TipoUsoPosibleMultiOT", "S" if system.supports_multiple_taxpayers else "N"
        )
        sistema_informatico_element.add(
            "sum1:IndicadorMultiplesOT", "S" if system.has_multiple_taxpayers else "N"
        )

        record_element.add("sum1:FechaHoraHusoGenRegistro", self.hashed_at.isoformat())
        record_element.add("sum1:TipoHuella", "01")  # SHA-256
        record_element.add("sum1:Huella", self.hash)
