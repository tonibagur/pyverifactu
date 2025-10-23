"""AEAT response model"""

from dataclasses import dataclass, field as dataclass_field
from datetime import datetime
from typing import List, Optional
from xml.etree import ElementTree as ET

from ...exceptions.aeat_exception import AeatException
from ..records.invoice_identifier import InvoiceIdentifier
from .item_status import ItemStatus
from .record_type import RecordType
from .response_item import ResponseItem
from .response_status import ResponseStatus


@dataclass
class AeatResponse:
    """
    Response from AEAT server

    Represents RespuestaBaseType from AEAT
    """

    NS_ENV = "http://schemas.xmlsoap.org/soap/envelope/"
    NS_TIKR = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaSuministro.xsd"
    NS_TIK = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd"

    wait_seconds: int
    """Segundos de espera entre envíos (TiempoEsperaEnvio)"""

    status: ResponseStatus
    """Estado global del envío (EstadoEnvio)"""

    items: List[ResponseItem] = dataclass_field(default_factory=list)
    """Estado detallado de cada línea del suministro (RespuestaLinea)"""

    csv: Optional[str] = None
    """CSV asociado al envío generado por AEAT (CSV)"""

    submitted_at: Optional[datetime] = None
    """Timestamp asociado a la remisión enviada (DatosPresentacion/TimestampPresentacion)"""

    @classmethod
    def from_xml(cls, xml_string: str) -> "AeatResponse":
        """
        Create new instance from XML response

        Args:
            xml_string: Raw XML response from AEAT

        Returns:
            Parsed response

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
        root_element = root.find(".//tikR:RespuestaRegFactuSistemaFacturacion", ns)
        if root_element is None:
            raise AeatException(
                "Missing <tikR:RespuestaRegFactuSistemaFacturacion /> element from response"
            )

        # Parse CSV
        csv: Optional[str] = None
        csv_element = root_element.find("tikR:CSV", ns)
        if csv_element is not None and csv_element.text:
            csv = csv_element.text

        # Parse submitted at timestamp
        submitted_at: Optional[datetime] = None
        submitted_at_element = root_element.find(
            "tikR:DatosPresentacion/tik:TimestampPresentacion", ns
        )
        if submitted_at_element is not None and submitted_at_element.text:
            try:
                # Parse ISO8601 format
                submitted_at = datetime.fromisoformat(
                    submitted_at_element.text.replace("Z", "+00:00")
                )
            except ValueError as e:
                raise AeatException(
                    f"Invalid submitted at date: {submitted_at_element.text}"
                ) from e

        # Parse wait seconds
        wait_seconds = 0
        wait_seconds_element = root_element.find("tikR:TiempoEsperaEnvio", ns)
        if wait_seconds_element is not None and wait_seconds_element.text:
            wait_seconds = int(wait_seconds_element.text)

        # Parse status
        status = ResponseStatus.INCORRECT
        status_element = root_element.find("tikR:EstadoEnvio", ns)
        if status_element is not None and status_element.text:
            status = ResponseStatus(status_element.text)

        # Parse items
        items: List[ResponseItem] = []
        for item_element in root_element.findall("tikR:RespuestaLinea", ns):
            # Parse issuer ID
            issuer_id_element = item_element.find(
                "tikR:IDFactura/tik:IDEmisorFactura", ns
            )
            issuer_id = (
                issuer_id_element.text if issuer_id_element is not None else ""
            )

            # Parse invoice number
            invoice_number_element = item_element.find(
                "tikR:IDFactura/tik:NumSerieFactura", ns
            )
            invoice_number = (
                invoice_number_element.text
                if invoice_number_element is not None
                else ""
            )

            # Parse issue date
            issue_date_element = item_element.find(
                "tikR:IDFactura/tik:FechaExpedicionFactura", ns
            )
            if issue_date_element is not None and issue_date_element.text:
                try:
                    issue_date = datetime.strptime(
                        issue_date_element.text, "%d-%m-%Y"
                    ).replace(hour=0, minute=0, second=0, microsecond=0)
                except ValueError as e:
                    raise AeatException(
                        f"Invalid invoice issue date: {issue_date_element.text}"
                    ) from e
            else:
                issue_date = datetime.now()

            # Parse record type
            record_type_element = item_element.find(
                "tikR:Operacion/tik:TipoOperacion", ns
            )
            record_type = (
                RecordType(record_type_element.text)
                if record_type_element is not None and record_type_element.text
                else RecordType.REGISTRATION
            )

            # Parse is correction
            is_correction_element = item_element.find(
                "tikR:Operacion/tik:Subsanacion", ns
            )
            is_correction = (
                is_correction_element.text == "S"
                if is_correction_element is not None
                else False
            )

            # Parse status
            item_status_element = item_element.find("tikR:EstadoRegistro", ns)
            item_status = (
                ItemStatus(item_status_element.text)
                if item_status_element is not None and item_status_element.text
                else ItemStatus.INCORRECT
            )

            # Parse error code
            error_code: Optional[str] = None
            error_code_element = item_element.find("tikR:CodigoErrorRegistro", ns)
            if error_code_element is not None and error_code_element.text:
                error_code = error_code_element.text

            # Parse error description
            error_description: Optional[str] = None
            error_description_element = item_element.find(
                "tikR:DescripcionErrorRegistro", ns
            )
            if (
                error_description_element is not None
                and error_description_element.text
            ):
                error_description = error_description_element.text

            item = ResponseItem(
                invoice_id=InvoiceIdentifier(
                    issuer_id=issuer_id,
                    invoice_number=invoice_number,
                    issue_date=issue_date,
                ),
                record_type=record_type,
                status=item_status,
                is_correction=is_correction,
                error_code=error_code,
                error_description=error_description,
            )
            items.append(item)

        return cls(
            wait_seconds=wait_seconds,
            status=status,
            items=items,
            csv=csv,
            submitted_at=submitted_at,
        )
