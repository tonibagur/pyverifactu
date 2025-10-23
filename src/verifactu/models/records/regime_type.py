"""Regime type enumeration (Claves de Régimen Especial o Trascendencia Adicional)"""

from enum import Enum


class RegimeType(str, Enum):
    """Regime type enumeration"""

    # Operación de régimen general
    C01 = "01"

    # Exportación
    C02 = "02"

    # Operaciones a las que se aplique el régimen especial de bienes usados, objetos de arte,
    # antigüedades y objetos de colección
    C03 = "03"

    # Régimen especial del oro de inversión
    C04 = "04"

    # Régimen especial de las agencias de viajes
    C05 = "05"

    # Régimen especial grupo de entidades en IVA (Nivel Avanzado)
    C06 = "06"

    # Régimen especial del criterio de caja
    C07 = "07"

    # Operaciones sujetas al IPSI / IGIC (Impuesto sobre la Producción, los Servicios y la
    # Importación / Impuesto General Indirecto Canario)
    C08 = "08"

    # Facturación de las prestaciones de servicios de agencias de viaje que actúan como mediadoras
    # en nombre y por cuenta ajena (D.A 4ª RD1619/2012)
    C09 = "09"

    # Cobros por cuenta de terceros de honorarios profesionales o de derechos derivados de la
    # propiedad industrial, de autor u otros por cuenta de sus socios, asociados o colegiados
    # efectuados por sociedades, asociaciones, colegios profesionales u otras entidades que
    # realicen estas funciones de cobro
    C10 = "10"

    # Operaciones de arrendamiento de local de negocio
    C11 = "11"

    # Factura con IVA pendiente de devengo en certificaciones de obra cuyo destinatario sea una
    # Administración Pública
    C14 = "14"

    # Factura con IVA pendiente de devengo en operaciones de tracto sucesivo
    C15 = "15"

    # Operación acogida a alguno de los regímenes previstos en el Capítulo XI del Título IX
    # (OSS e IOSS)
    C17 = "17"

    # Recargo de equivalencia
    C18 = "18"

    # Operaciones de actividades incluidas en el Régimen Especial de Agricultura, Ganadería y
    # Pesca (REAGYP)
    C19 = "19"

    # Régimen simplificado
    C20 = "20"
