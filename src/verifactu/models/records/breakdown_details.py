"""Breakdown details model"""

from __future__ import annotations

import re
from typing import Optional
from pydantic import Field, field_validator, model_validator
from verifactu.models.model import Model
from verifactu.models.records.tax_type import TaxType
from verifactu.models.records.regime_type import RegimeType
from verifactu.models.records.operation_type import OperationType


class BreakdownDetails(Model):
    """
    Breakdown details

    Detalle de desglose

    @field DetalleDesglose
    """

    # Impuesto de aplicación
    # @field Impuesto
    tax_type: TaxType = Field(..., description="Tax type")

    # Clave que identifica el tipo de régimen del impuesto o una operación con trascendencia tributaria
    # @field ClaveRegimen
    regime_type: RegimeType = Field(..., description="Regime type")

    # Clave de la operación sujeta y no exenta, clave de la operación no sujeta, o causa de la exención
    # @field CalificacionOperacion
    # @field OperacionExenta
    operation_type: OperationType = Field(..., description="Operation type")

    # Magnitud dineraria sobre la que se aplica el tipo impositivo / Importe no sujeto
    # @field BaseImponibleOimporteNoSujeto
    base_amount: str = Field(..., description="Base amount (format: -?\\d{1,12}.\\d{2})")

    # Porcentaje aplicado sobre la base imponible para calcular la cuota
    # @field TipoImpositivo
    tax_rate: Optional[str] = Field(
        None, description="Tax rate percentage (format: \\d{1,3}.\\d{2})"
    )

    # Cuota resultante de aplicar a la base imponible el tipo impositivo
    # @field CuotaRepercutida
    tax_amount: Optional[str] = Field(
        None, description="Tax amount (format: -?\\d{1,12}.\\d{2})"
    )

    @field_validator("base_amount")
    @classmethod
    def validate_base_amount(cls, v: str) -> str:
        """Validate base amount format"""
        if not v or not v.strip():
            raise ValueError("base_amount cannot be blank")
        if not re.match(r"^-?\d{1,12}\.\d{2}$", v):
            raise ValueError(
                "base_amount must match format -?\\d{1,12}.\\d{2} (e.g., '100.00' or '-100.00')"
            )
        return v

    @field_validator("tax_rate")
    @classmethod
    def validate_tax_rate(cls, v: Optional[str]) -> Optional[str]:
        """Validate tax rate format"""
        if v is not None and not re.match(r"^\d{1,3}\.\d{2}$", v):
            raise ValueError("tax_rate must match format \\d{1,3}.\\d{2} (e.g., '21.00')")
        return v

    @field_validator("tax_amount")
    @classmethod
    def validate_tax_amount_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate tax amount format"""
        if v is not None and not re.match(r"^-?\d{1,12}\.\d{2}$", v):
            raise ValueError(
                "tax_amount must match format -?\\d{1,12}.\\d{2} (e.g., '21.00' or '-21.00')"
            )
        return v

    @model_validator(mode="after")
    def validate_operation_type_rules(self) -> "BreakdownDetails":
        """Validate operation type rules"""
        if self.operation_type.is_subject():
            if self.tax_rate is None:
                raise ValueError("Tax rate must be defined for subject operation types")
            if self.tax_amount is None:
                raise ValueError("Tax amount must be defined for subject operation types")
        else:
            if self.tax_rate is not None:
                raise ValueError(
                    "Tax rate cannot be defined for non-subject or exempt operation types"
                )
            if self.tax_amount is not None:
                raise ValueError(
                    "Tax amount cannot be defined for non-subject or exempt operation types"
                )
        return self

    @model_validator(mode="after")
    def validate_tax_amount_calculation(self) -> "BreakdownDetails":
        """Validate tax amount calculation"""
        if self.base_amount is None or self.tax_rate is None or self.tax_amount is None:
            return self

        valid_tax_amount = False
        best_tax_amount = float(self.base_amount) * (float(self.tax_rate) / 100)

        # Check with tolerance of ±0.02
        for tolerance in [0, -0.01, 0.01, -0.02, 0.02]:
            expected_tax_amount = f"{best_tax_amount + tolerance:.2f}"
            if self.tax_amount == expected_tax_amount:
                valid_tax_amount = True
                break

        if not valid_tax_amount:
            best_tax_amount_str = f"{best_tax_amount:.2f}"
            raise ValueError(
                f"Expected tax amount of {best_tax_amount_str}, got {self.tax_amount}"
            )

        return self
