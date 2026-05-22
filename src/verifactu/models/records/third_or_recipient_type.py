"""Issued by Third or Recipient type enumeration (Autofacturas)"""
"""Identificador que especifica si la factura ha sido expedida materialmente por un tercero o por el destinatario (contraparte)"""

from enum import Enum


class ThirdOrRecipientType(str, Enum):
    """Issued by Third or Recipient type enumeration"""

    # Emitido por Tercero
    THIRD = "T"

    # Emitido por Destinatario (contraparte)
    RECIPIENT = "D"