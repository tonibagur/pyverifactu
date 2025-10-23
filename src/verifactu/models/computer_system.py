"""Computer system model"""

from __future__ import annotations

from pydantic import Field, field_validator
from verifactu.models.model import Model


class ComputerSystem(Model):
    """
    Computer system

    @field SistemaInformatico
    """

    # Nombre-razón social de la persona o entidad productora
    # @field NombreRazon
    vendor_name: str = Field(
        ..., max_length=120, description="Vendor name or company name (max 120 characters)"
    )

    # NIF de la persona o entidad productora
    # @field NIF
    vendor_nif: str = Field(
        ..., min_length=9, max_length=9, description="Vendor NIF (exactly 9 characters)"
    )

    # Nombre dado por la persona o entidad productora a su sistema informático de facturación (SIF)
    # @field NombreSistemaInformatico
    name: str = Field(..., max_length=30, description="System name (max 30 characters)")

    # Código identificativo dado por la persona o entidad productora a su sistema
    # informático de facturación (SIF)
    # @field IdSistemaInformatico
    id: str = Field(..., min_length=1, max_length=2, description="System ID (max 2 characters)")

    # Identificación de la versión del sistema informático de facturación (SIF)
    # @field Version
    version: str = Field(..., max_length=50, description="System version (max 50 characters)")

    # Número de instalación del sistema informático de facturación (SIF) utilizado
    # @field NumeroInstalacion
    installation_number: str = Field(
        ..., max_length=100, description="Installation number (max 100 characters)"
    )

    # Especifica si solo puede funcionar como "VERI*FACTU" o también puede funcionar como
    # "no VERI*FACTU" (offline)
    # @field TipoUsoPosibleSoloVerifactu
    only_supports_verifactu: bool = Field(
        ..., description="Whether system only supports VERI*FACTU mode"
    )

    # Especifica si permite llevar independientemente la facturación de varios obligados tributarios
    # @field TipoUsoPosibleMultiOT
    supports_multiple_taxpayers: bool = Field(
        ..., description="Whether system supports multiple taxpayers"
    )

    # En el momento de la generación de este registro, está soportando la facturación de más de un
    # obligado tributario
    # @field IndicadorMultiplesOT
    has_multiple_taxpayers: bool = Field(
        ..., description="Whether system currently has multiple taxpayers"
    )

    @field_validator("vendor_name", "name", "version", "installation_number")
    @classmethod
    def validate_not_blank(cls, v: str) -> str:
        """Validate field is not blank"""
        if not v or not v.strip():
            raise ValueError("Field cannot be blank")
        return v

    @field_validator("vendor_nif")
    @classmethod
    def validate_vendor_nif(cls, v: str) -> str:
        """Validate vendor_nif is not blank"""
        if not v or not v.strip():
            raise ValueError("vendor_nif cannot be blank")
        return v

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate id is not blank"""
        if not v or not v.strip():
            raise ValueError("id cannot be blank")
        return v
