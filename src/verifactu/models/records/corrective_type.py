"""Corrective type enumeration (Tipo de factura rectificativa)"""

from enum import Enum


class CorrectiveType(str, Enum):
    """Corrective type enumeration"""

    # Por sustitución
    # Se emite una factura rectificativa que sustituye completamente a la factura original.
    # La factura original queda anulada.
    SUBSTITUTION = "S"

    # Por diferencias
    # Se emite una factura rectificativa que complementa la factura original, corrigiendo
    # únicamente las diferencias en importes o datos específicos.
    # La factura original sigue siendo válida.
    DIFFERENCES = "I"
