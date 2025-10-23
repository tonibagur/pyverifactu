"""Record type enumeration (Tipo de registro)"""

from enum import Enum


class RecordType(str, Enum):
    """Record type enumeration"""

    # Registro
    REGISTRATION = "Alta"

    # Anulación
    CANCELLATION = "Anulacion"
