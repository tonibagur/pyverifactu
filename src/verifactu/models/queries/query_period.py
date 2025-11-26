"""Query period model for AEAT invoice consultation"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class QueryPeriod:
    """
    Period for invoice queries (PeriodoImputacion)

    Represents the tax period to query invoices for.
    """

    year: int
    """Tax year (Ejercicio) - 4 digit year"""

    month: int
    """Tax month (Periodo) - 1-12"""

    def __post_init__(self) -> None:
        """Validate period values"""
        if self.year < 2000 or self.year > 9999:
            raise ValueError(f"Invalid year: {self.year}. Must be between 2000 and 9999.")
        if self.month < 1 or self.month > 12:
            raise ValueError(f"Invalid month: {self.month}. Must be between 1 and 12.")

    @property
    def ejercicio(self) -> str:
        """Get year as 4-digit string for XML"""
        return str(self.year)

    @property
    def periodo(self) -> str:
        """Get month as 2-digit string for XML"""
        return f"{self.month:02d}"
