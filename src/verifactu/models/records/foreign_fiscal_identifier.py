"""Foreign fiscal identifier model"""

from __future__ import annotations

import re
from pydantic import Field, field_validator, model_validator
from verifactu.models.model import Model
from verifactu.models.records.foreign_id_type import ForeignIdType


class ForeignFiscalIdentifier(Model):
    """
    Foreign fiscal identifier (non-Spanish)

    Identificador fiscal de fuera de España

    @field Caberecera/ObligadoEmision
    @field Caberecera/Representante
    @field RegistroAlta/Tercero
    @field IDDestinatario
    """

    # Nombre-razón social
    # @field NombreRazon
    name: str = Field(..., max_length=120, description="Name or company name (max 120 characters)")

    # Código del país (ISO 3166-1 alpha-2 codes)
    # @field IDOtro/CodigoPais
    country: str = Field(..., min_length=2, max_length=2, description="Country code (ISO 3166-1 alpha-2)")

    # Clave para establecer el tipo de identificación en el país de residencia
    # @field IDOtro/IDType
    type: ForeignIdType = Field(..., description="Foreign ID type")

    # Número de identificación en el país de residencia
    # @field IDOtro/ID
    value: str = Field(..., max_length=20, description="ID value (max 20 characters)")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not blank"""
        if not v or not v.strip():
            raise ValueError("name cannot be blank")
        return v

    @field_validator("country")
    @classmethod
    def validate_country_format(cls, v: str) -> str:
        """Validate country is a valid 2-letter code"""
        if not v or not v.strip():
            raise ValueError("country cannot be blank")
        if not re.match(r"^[A-Z]{2}$", v):
            raise ValueError("country must be a 2-letter uppercase code (ISO 3166-1 alpha-2)")
        return v

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: str) -> str:
        """Validate value is not blank"""
        if not v or not v.strip():
            raise ValueError("value cannot be blank")
        return v

    @model_validator(mode="after")
    def validate_country_not_es(self) -> "ForeignFiscalIdentifier":
        """Validate country is not ES"""
        if self.country == "ES":
            raise ValueError('Country code cannot be "ES", use the FiscalIdentifier model instead')
        return self
