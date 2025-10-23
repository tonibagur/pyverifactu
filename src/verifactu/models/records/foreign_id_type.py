"""Foreign ID type enumeration"""

from enum import Enum


class ForeignIdType(str, Enum):
    """Foreign ID type enumeration"""

    # NIF-IVA
    VAT = "02"

    # Pasaporte
    PASSPORT = "03"

    # Documento oficial de identificación expedido por el país o territorio de residencia
    NATIONAL_ID = "04"

    # Certificado de residencia
    RESIDENCE = "05"

    # Otro documento probatorio
    OTHER = "06"

    # No censado
    UNREGISTERED = "07"
