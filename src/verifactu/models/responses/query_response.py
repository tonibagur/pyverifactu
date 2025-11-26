"""Query response model for AEAT invoice consultation"""

from dataclasses import dataclass, field as dataclass_field
from datetime import datetime
from enum import Enum
from typing import List, Optional
from xml.etree import ElementTree as ET

from ...exceptions.aeat_exception import AeatException
from ..records.invoice_identifier import InvoiceIdentifier
from .query_record_status import QueryRecordStatus
from .query_response_item import QueryResponseItem, QueryRecipient, QueryBreakdownItem, QueryPreviousRecord


class QueryResultType(str, Enum):
    """Result type for query response"""

    WITH_DATA = "ConDatos"
    """Query returned invoice records"""

    WITHOUT_DATA = "SinDatos"
    """Query returned no results"""


@dataclass
class QueryResponse:
    """
    Response from AEAT query service

    Represents RespuestaConsultaFactuSistemaFacturacionType from AEAT.
    """

    NS_ENV = "http://schemas.xmlsoap.org/soap/envelope/"
    NS_TIKR = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd"
    NS_TIK = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd"
    # AEAT uses tikLRRC: prefix for RespuestaConsultaLR namespace
    NS_TIKRLRC = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd"

    year: int
    """Tax year (Ejercicio)"""

    month: int
    """Tax month (Periodo)"""

    result_type: QueryResultType
    """Result type - with or without data (ResultadoConsulta)"""

    has_more_pages: bool
    """Indicates if there are more pages (IndicadorPaginacion = 'S')"""

    items: List[QueryResponseItem] = dataclass_field(default_factory=list)
    """List of invoice records (RegistroRespuestaConsultaFactuSistemaFacturacion)"""

    pagination_key: Optional[str] = None
    """Key for fetching next page (ClavePaginacion)"""

    @classmethod
    def from_xml(cls, xml_string: str) -> "QueryResponse":
        """
        Create new instance from XML response

        Args:
            xml_string: Raw XML response from AEAT

        Returns:
            Parsed query response

        Raises:
            AeatException: If server returned an error or failed to parse response
        """
        try:
            root = ET.fromstring(xml_string)
        except ET.ParseError as e:
            raise AeatException(f"Failed to parse XML response: {e}") from e

        # Define namespace map
        ns = {
            "env": cls.NS_ENV,
            "tikR": cls.NS_TIKR,
            "tik": cls.NS_TIK,
        }

        # Handle server errors
        fault_element = root.find(".//env:Fault/faultstring", ns)
        if fault_element is not None and fault_element.text:
            raise AeatException(fault_element.text)

        # Get root XML element
        root_element = root.find(".//tikR:RespuestaConsultaFactuSistemaFacturacion", ns)
        if root_element is None:
            raise AeatException(
                "Missing <tikR:RespuestaConsultaFactuSistemaFacturacion /> element from response"
            )

        # Parse period - AEAT uses tikLRRC namespace for these elements
        year = 0
        year_element = root_element.find("tikR:PeriodoImputacion/tikR:Ejercicio", ns)
        if year_element is not None and year_element.text:
            year = int(year_element.text)

        month = 0
        month_element = root_element.find("tikR:PeriodoImputacion/tikR:Periodo", ns)
        if month_element is not None and month_element.text:
            month = int(month_element.text)

        # Parse result type
        result_type = QueryResultType.WITHOUT_DATA
        result_element = root_element.find("tikR:ResultadoConsulta", ns)
        if result_element is not None and result_element.text:
            result_type = QueryResultType(result_element.text)

        # Parse pagination indicator
        has_more_pages = False
        pagination_indicator = root_element.find("tikR:IndicadorPaginacion", ns)
        if pagination_indicator is not None and pagination_indicator.text:
            has_more_pages = pagination_indicator.text == "S"

        # Parse pagination key
        pagination_key: Optional[str] = None
        pagination_key_element = root_element.find("tikR:ClavePaginacion", ns)
        if pagination_key_element is not None and pagination_key_element.text:
            pagination_key = pagination_key_element.text

        # Parse items
        items: List[QueryResponseItem] = []
        for item_element in root_element.findall(
            "tikR:RegistroRespuestaConsultaFactuSistemaFacturacion", ns
        ):
            item = cls._parse_response_item(item_element, ns)
            items.append(item)

        return cls(
            year=year,
            month=month,
            result_type=result_type,
            has_more_pages=has_more_pages,
            items=items,
            pagination_key=pagination_key,
        )

    @classmethod
    def _parse_response_item(
        cls, item_element: ET.Element, ns: dict
    ) -> QueryResponseItem:
        """Parse a single response item from XML"""
        # Parse invoice ID
        issuer_id_element = item_element.find(
            "tikR:IDFactura/tik:IDEmisorFactura", ns
        )
        issuer_id = issuer_id_element.text if issuer_id_element is not None else ""

        invoice_number_element = item_element.find(
            "tikR:IDFactura/tik:NumSerieFactura", ns
        )
        invoice_number = (
            invoice_number_element.text if invoice_number_element is not None else ""
        )

        issue_date_element = item_element.find(
            "tikR:IDFactura/tik:FechaExpedicionFactura", ns
        )
        if issue_date_element is not None and issue_date_element.text:
            try:
                issue_date = datetime.strptime(
                    issue_date_element.text, "%d-%m-%Y"
                ).replace(hour=0, minute=0, second=0, microsecond=0)
            except ValueError:
                issue_date = datetime.now()
        else:
            issue_date = datetime.now()

        invoice_id = InvoiceIdentifier(
            issuer_id=issuer_id,
            invoice_number=invoice_number,
            issue_date=issue_date,
        )

        # Parse issuer name - elements in tikR (RespuestaConsultaLR) namespace
        issuer_name_element = item_element.find(
            "tikR:DatosRegistroFacturacion/tikR:NombreRazonEmisor", ns
        )
        issuer_name = (
            issuer_name_element.text if issuer_name_element is not None else None
        )

        # Parse invoice type
        invoice_type_element = item_element.find(
            "tikR:DatosRegistroFacturacion/tikR:TipoFactura", ns
        )
        invoice_type = (
            invoice_type_element.text if invoice_type_element is not None else None
        )

        # Parse corrective type
        corrective_type_element = item_element.find(
            "tikR:DatosRegistroFacturacion/tikR:TipoRectificativa", ns
        )
        corrective_type = (
            corrective_type_element.text if corrective_type_element is not None else None
        )

        # Parse description
        description_element = item_element.find(
            "tikR:DatosRegistroFacturacion/tikR:DescripcionOperacion", ns
        )
        description = (
            description_element.text if description_element is not None else None
        )

        # Parse total amount
        total_amount_element = item_element.find(
            "tikR:DatosRegistroFacturacion/tikR:ImporteTotal", ns
        )
        total_amount = (
            total_amount_element.text if total_amount_element is not None else None
        )

        # Parse total tax amount
        total_tax_element = item_element.find(
            "tikR:DatosRegistroFacturacion/tikR:CuotaTotal", ns
        )
        total_tax_amount = (
            total_tax_element.text if total_tax_element is not None else None
        )

        # Parse hash
        hash_element = item_element.find(
            "tikR:DatosRegistroFacturacion/tikR:Huella", ns
        )
        hash_value = hash_element.text if hash_element is not None else None

        # Parse registration date
        reg_date_element = item_element.find(
            "tikR:DatosRegistroFacturacion/tikR:FechaHoraHusoGenRegistro", ns
        )
        registration_date = None
        if reg_date_element is not None and reg_date_element.text:
            try:
                registration_date = datetime.fromisoformat(
                    reg_date_element.text.replace("Z", "+00:00")
                )
            except ValueError:
                pass

        # Parse recipients - Destinatarios in tikR, IDDestinatario in tikR, content in tik
        recipients: List[QueryRecipient] = []
        for recipient_element in item_element.findall(
            "tikR:DatosRegistroFacturacion/tikR:Destinatarios/tikR:IDDestinatario", ns
        ):
            name_el = recipient_element.find("tik:NombreRazon", ns)
            nif_el = recipient_element.find("tik:NIF", ns)
            recipients.append(
                QueryRecipient(
                    name=name_el.text if name_el is not None else None,
                    nif=nif_el.text if nif_el is not None else None,
                )
            )

        # Parse breakdown - Desglose in tikR, DetalleDesglose in tik
        breakdown: List[QueryBreakdownItem] = []
        for detail_element in item_element.findall(
            "tikR:DatosRegistroFacturacion/tikR:Desglose/tik:DetalleDesglose", ns
        ):
            tax_type_el = detail_element.find("tik:Impuesto", ns)
            regime_el = detail_element.find("tik:ClaveRegimen", ns)
            operation_el = detail_element.find("tik:CalificacionOperacion", ns)
            rate_el = detail_element.find("tik:TipoImpositivo", ns)
            base_el = detail_element.find("tik:BaseImponibleOimporteNoSujeto", ns)
            tax_el = detail_element.find("tik:CuotaRepercutida", ns)
            breakdown.append(
                QueryBreakdownItem(
                    tax_type=tax_type_el.text if tax_type_el is not None else None,
                    regime_type=regime_el.text if regime_el is not None else None,
                    operation_type=operation_el.text if operation_el is not None else None,
                    tax_rate=rate_el.text if rate_el is not None else None,
                    base_amount=base_el.text if base_el is not None else None,
                    tax_amount=tax_el.text if tax_el is not None else None,
                )
            )

        # Parse status
        status_element = item_element.find("tikR:EstadoRegistro/tikR:EstadoRegistro", ns)
        status = None
        if status_element is not None and status_element.text:
            try:
                status = QueryRecordStatus(status_element.text)
            except ValueError:
                pass

        # Parse error code
        error_code_element = item_element.find(
            "tikR:EstadoRegistro/tikR:CodigoErrorRegistro", ns
        )
        error_code = (
            error_code_element.text if error_code_element is not None else None
        )

        # Parse error description
        error_desc_element = item_element.find(
            "tikR:EstadoRegistro/tikR:DescripcionErrorRegistro", ns
        )
        error_description = (
            error_desc_element.text if error_desc_element is not None else None
        )

        # Parse last modified
        modified_element = item_element.find(
            "tikR:EstadoRegistro/tikR:TimestampUltimaModificacion", ns
        )
        last_modified = None
        if modified_element is not None and modified_element.text:
            try:
                last_modified = datetime.fromisoformat(
                    modified_element.text.replace("Z", "+00:00")
                )
            except ValueError:
                pass

        # Parse CSV and presentation timestamp
        csv_element = item_element.find(
            "tikR:DatosPresentacion/tik:CSV", ns
        )
        csv = csv_element.text if csv_element is not None else None

        presentation_element = item_element.find(
            "tikR:DatosPresentacion/tik:TimestampPresentacion", ns
        )
        presentation_timestamp = None
        if presentation_element is not None and presentation_element.text:
            try:
                presentation_timestamp = datetime.fromisoformat(
                    presentation_element.text.replace("Z", "+00:00")
                )
            except ValueError:
                pass

        # Parse chaining information (Encadenamiento)
        is_first_record = False
        previous_record = None

        # Check if it's the first record
        first_record_element = item_element.find(
            "tikR:DatosRegistroFacturacion/tikR:Encadenamiento/tikR:PrimerRegistro", ns
        )
        if first_record_element is not None and first_record_element.text == "S":
            is_first_record = True

        # Check for previous record info
        prev_record_element = item_element.find(
            "tikR:DatosRegistroFacturacion/tikR:Encadenamiento/tikR:RegistroAnterior", ns
        )
        if prev_record_element is not None:
            prev_issuer = prev_record_element.find("tik:IDEmisorFactura", ns)
            prev_number = prev_record_element.find("tik:NumSerieFactura", ns)
            prev_date_el = prev_record_element.find("tik:FechaExpedicionFactura", ns)
            prev_hash = prev_record_element.find("tik:Huella", ns)

            prev_date = None
            if prev_date_el is not None and prev_date_el.text:
                try:
                    prev_date = datetime.strptime(prev_date_el.text, "%d-%m-%Y")
                except ValueError:
                    pass

            previous_record = QueryPreviousRecord(
                issuer_nif=prev_issuer.text if prev_issuer is not None else None,
                invoice_number=prev_number.text if prev_number is not None else None,
                issue_date=prev_date,
                hash=prev_hash.text if prev_hash is not None else None,
            )

        return QueryResponseItem(
            invoice_id=invoice_id,
            issuer_name=issuer_name,
            invoice_type=invoice_type,
            corrective_type=corrective_type,
            description=description,
            total_amount=total_amount,
            total_tax_amount=total_tax_amount,
            hash=hash_value,
            registration_date=registration_date,
            recipients=recipients,
            breakdown=breakdown,
            status=status,
            error_code=error_code,
            error_description=error_description,
            last_modified=last_modified,
            csv=csv,
            presentation_timestamp=presentation_timestamp,
            is_first_record=is_first_record,
            previous_record=previous_record,
        )
