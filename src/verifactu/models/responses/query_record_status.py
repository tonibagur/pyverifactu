"""Query record status enum"""

from enum import Enum


class QueryRecordStatus(str, Enum):
    """
    Status of a record in query response (EstadoRegistro)

    Represents the current state of an invoice record in AEAT.
    """

    CORRECT = "Correcto"
    """Invoice was accepted without errors"""

    ACCEPTED_WITH_ERRORS = "AceptadoConErrores"
    """Invoice was accepted but with some warnings/errors"""

    CANCELLED = "Anulado"
    """Invoice has been cancelled"""
