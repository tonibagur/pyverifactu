"""Tax type enumeration"""

from enum import Enum


class TaxType(str, Enum):
    """Tax type enumeration"""

    # Impuesto sobre el Valor Añadido (IVA)
    IVA = "01"

    # Impuesto sobre la Producción, los Servicios y la Importación (IPSI) de Ceuta y Melilla
    IPSI = "02"

    # Impuesto General Indirecto Canario (IGIC)
    IGIC = "03"

    # Otros
    OTHER = "05"
