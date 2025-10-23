"""Operation type enumeration"""

from enum import Enum


class OperationType(str, Enum):
    """Operation type enumeration"""

    # Operación sujeta y no exenta - Sin inversión del sujeto pasivo
    SUBJECT = "S1"

    # Operación sujeta y no exenta - Con inversión del sujeto pasivo
    PASSIVE_SUBJECT = "S2"

    # Operación no sujeta - Artículos 7, 14 y otros
    NON_SUBJECT = "N1"

    # Operación no sujeta por reglas de localización
    NON_SUBJECT_BY_LOCATION = "N2"

    # Exenta por el artículo 20
    EXEMPT_BY_ARTICLE_20 = "E1"

    # Exenta por el artículo 21
    EXEMPT_BY_ARTICLE_21 = "E2"

    # Exenta por el artículo 22
    EXEMPT_BY_ARTICLE_22 = "E3"

    # Exenta por los artículos 23 y 24
    EXEMPT_BY_ARTICLES_23_AND_24 = "E4"

    # Exenta por el artículo 25
    EXEMPT_BY_ARTICLE_25 = "E5"

    # Exenta por otros
    EXEMPT_BY_OTHER = "E6"

    def is_subject(self) -> bool:
        """
        Is subject operation

        Returns:
            Whether is a subject operation type
        """
        return self in (OperationType.SUBJECT, OperationType.PASSIVE_SUBJECT)

    def is_non_subject(self) -> bool:
        """
        Is non-subject operation

        Returns:
            Whether is a non-subject operation type
        """
        return self in (OperationType.NON_SUBJECT, OperationType.NON_SUBJECT_BY_LOCATION)

    def is_exempt(self) -> bool:
        """
        Is exempt operation

        Returns:
            Whether is an exempt operation type
        """
        return self in (
            OperationType.EXEMPT_BY_ARTICLE_20,
            OperationType.EXEMPT_BY_ARTICLE_21,
            OperationType.EXEMPT_BY_ARTICLE_22,
            OperationType.EXEMPT_BY_ARTICLES_23_AND_24,
            OperationType.EXEMPT_BY_ARTICLE_25,
            OperationType.EXEMPT_BY_OTHER,
        )
