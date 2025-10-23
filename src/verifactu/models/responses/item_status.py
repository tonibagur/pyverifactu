"""Item status enumeration (Estado del envío de un registro)"""

from enum import Enum


class ItemStatus(str, Enum):
    """Item status enumeration"""

    # El registro de facturación es totalmente correcto y se registra en el sistema
    CORRECT = "Correcto"

    # El registro de facturación tiene errores que no provocan su rechazo
    ACCEPTED_WITH_ERRORS = "AceptadoConErrores"

    # El registro de facturación tiene errores que provocan su rechazo
    INCORRECT = "Incorrecto"
