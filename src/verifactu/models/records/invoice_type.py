"""Invoice type enumeration"""

from enum import Enum


class InvoiceType(str, Enum):
    """Invoice type enumeration"""

    # Factura (Art. 6, 7.2 y 7.3 del R.D. 1619/2012)
    FACTURA = "F1"

    # Factura simplificada y facturas sin identificación del destinatario (Art. 6.1.D del R.D. 1619/2012)
    SIMPLIFICADA = "F2"

    # Factura emitida en sustitución de facturas simplificadas facturadas y declaradas
    SUSTITUTIVA = "F3"

    # Factura rectificativa (Art 80.1 y 80.2 y error fundado en derecho)
    R1 = "R1"

    # Factura rectificativa (Art. 80.3)
    R2 = "R2"

    # Factura rectificativa (Art. 80.4)
    R3 = "R3"

    # Factura rectificativa (Resto)
    R4 = "R4"

    # Factura rectificativa en facturas simplificadas
    R5 = "R5"
