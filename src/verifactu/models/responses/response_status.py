"""Response status enumeration (Estado global del envío)"""

from enum import Enum


class ResponseStatus(str, Enum):
    """Response status enumeration"""

    # Todos los registros de facturación de la remisión tienen estado "Correcto"
    CORRECT = "Correcto"

    # Algunos registros de la remisión tienen estado "Incorrecto" o "AceptadoConErrores"
    PARTIALLY_CORRECT = "ParcialmenteCorrecto"

    # Todos los registros de la remisión tienen estado "Incorrecto"
    INCORRECT = "Incorrecto"
