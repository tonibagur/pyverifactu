"""Fiscal identifier model"""

from __future__ import annotations

from typing import Optional
from pydantic import Field, field_validator
from verifactu.models.model import Model


class FiscalIdentifier(Model):
    """
    Fiscal identifier (Spanish NIF)

    Identificador fiscal

    @field Caberecera/ObligadoEmision
    @field Caberecera/Representante
    """

    # Nombre-razón social
    # @field NombreRazon
    name: str = Field(..., max_length=120, description="Name or company name (max 120 characters)")

    # Número de identificación fiscal (NIF)
    # @field NIF
    nif: str = Field(..., min_length=9, max_length=9, description="NIF (exactly 9 characters)")

    def __init__(self, name: Optional[str] = None, nif: Optional[str] = None, **data: dict) -> None:
        """
        Class constructor

        Args:
            name: Name or company name
            nif: NIF (Spanish tax ID)
            **data: Additional data
        """
        if name is not None:
            data["name"] = name
        if nif is not None:
            data["nif"] = nif
        super().__init__(**data)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not blank"""
        if not v or not v.strip():
            raise ValueError("name cannot be blank")
        return v

    @field_validator("nif")
    @classmethod
    def validate_nif(cls, v: str) -> str:
        """Validate nif is not blank"""
        if not v or not v.strip():
            raise ValueError("nif cannot be blank")
        return v
