"""AEAT client for communicating with Verifactu web service"""

from xml.etree import ElementTree as ET
from typing import Optional, Sequence, Union
import os
import tempfile
import requests
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption

from ..exceptions.aeat_exception import AeatException
from ..models.computer_system import ComputerSystem
from ..models.records.fiscal_identifier import FiscalIdentifier
from ..models.records.record import Record
from ..models.records.registration_record import RegistrationRecord
from ..models.records.cancellation_record import CancellationRecord
from ..models.responses.aeat_response import AeatResponse
from ..models.responses.query_response import QueryResponse
from ..models.queries.query_filter import QueryFilter


class AeatClient:
    """
    Client to communicate with the AEAT web service endpoint for VERI*FACTU

    This class handles:
    - Building SOAP XML requests
    - Sending records to AEAT
    - Parsing AEAT responses
    - Certificate authentication
    """

    NS_SOAPENV = "http://schemas.xmlsoap.org/soap/envelope/"
    NS_SUM = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroLR.xsd"
    NS_SUM1 = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd"
    NS_CONS = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/ConsultaLR.xsd"

    def __init__(
        self,
        system: ComputerSystem,
        taxpayer: FiscalIdentifier,
        http_client: Optional[requests.Session] = None,
    ):
        """
        Initialize AEAT client

        Args:
            system: Computer system details
            taxpayer: Taxpayer details (party that issues the invoices)
            http_client: Custom HTTP client session, leave None to create a new one
        """
        self.system = system
        self.taxpayer = taxpayer
        self.client = http_client or requests.Session()
        self.certificate_path: Optional[str] = None
        self.certificate_password: Optional[str] = None
        self._temp_cert_file: Optional[str] = None  # For converted PFX certificates
        self.representative: Optional[FiscalIdentifier] = None
        self.is_production = True

    def set_certificate(
        self, certificate_path: str, certificate_password: Optional[str] = None
    ) -> "AeatClient":
        """
        Set certificate for authentication

        The certificate path can be:
        - A PEM file (unencrypted or encrypted with password)
        - A PKCS#12 (.p12, .pfx) bundle (requires password)

        For PKCS#12 files, the certificate will be automatically converted to PEM format.

        Args:
            certificate_path: Path to certificate file
            certificate_password: Certificate password or None for unencrypted PEM

        Returns:
            This instance for chaining

        Raises:
            AeatException: If certificate cannot be read or converted
        """
        self.certificate_path = certificate_path
        self.certificate_password = certificate_password

        # Check if it's a PKCS#12 file and convert to PEM
        if certificate_path.lower().endswith(('.pfx', '.p12')):
            self._convert_pfx_to_pem(certificate_path, certificate_password)

        return self

    def _convert_pfx_to_pem(self, pfx_path: str, password: Optional[str]) -> None:
        """
        Convert PKCS#12 certificate to PEM format

        Args:
            pfx_path: Path to PFX/P12 file
            password: Certificate password (required for PFX)

        Raises:
            AeatException: If conversion fails
        """
        try:
            # Read PFX file
            with open(pfx_path, 'rb') as f:
                pfx_data = f.read()

            # Convert password to bytes if provided
            password_bytes = password.encode('utf-8') if password else None

            # Load PKCS#12
            try:
                private_key, certificate, _ = pkcs12.load_key_and_certificates(
                    pfx_data,
                    password_bytes
                )
            except Exception as e:
                raise AeatException(
                    f"Failed to read PKCS#12 certificate. Check password and file format. Error: {e}"
                ) from e

            if private_key is None or certificate is None:
                raise AeatException("PKCS#12 file does not contain a valid certificate and private key")

            # Serialize certificate to PEM
            cert_pem = certificate.public_bytes(Encoding.PEM)

            # Serialize private key to PEM (unencrypted for use with requests)
            key_pem = private_key.private_bytes(
                encoding=Encoding.PEM,
                format=PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=NoEncryption()
            )

            # Combine certificate and key in a temporary file
            temp_fd, temp_path = tempfile.mkstemp(suffix='.pem', text=False)
            try:
                with os.fdopen(temp_fd, 'wb') as f:
                    f.write(cert_pem)
                    f.write(key_pem)

                # Store temporary file path
                self._temp_cert_file = temp_path
                # Update certificate path to use the converted PEM
                self.certificate_path = temp_path
                # PEM files don't need password for requests
                self.certificate_password = None

                print(f"✓ Certificate converted from PKCS#12 to PEM format")
                print(f"📄 Using temporary PEM file for connection")

            except Exception as e:
                # Clean up temp file on error
                try:
                    os.unlink(temp_path)
                except:
                    pass
                raise AeatException(f"Failed to write PEM file: {e}") from e

        except AeatException:
            raise
        except Exception as e:
            raise AeatException(f"Failed to convert certificate: {e}") from e

    def __del__(self):
        """Cleanup temporary certificate file if created"""
        if self._temp_cert_file and os.path.exists(self._temp_cert_file):
            try:
                os.unlink(self._temp_cert_file)
            except:
                pass

    def set_representative(
        self, representative: Optional[FiscalIdentifier]
    ) -> "AeatClient":
        """
        Set representative

        NOTE: Requires the represented fiscal entity to fill the "GENERALLEY58" form at AEAT.

        Args:
            representative: Representative details (party that sends the invoices)

        Returns:
            This instance for chaining
        """
        self.representative = representative
        return self

    def set_production(self, production: bool) -> "AeatClient":
        """
        Set production environment

        Args:
            production: True for production, False for testing

        Returns:
            This instance for chaining
        """
        self.is_production = production
        return self

    def send(
        self, records: Sequence[Union[RegistrationRecord, CancellationRecord]],
        debug: bool = False,
        incidencia: bool = False
    ) -> AeatResponse:
        """
        Send invoicing records to AEAT

        Args:
            records: Invoicing records to send
            debug: If True, print request and response XML for debugging
            incidencia: If True, marks submission as "incidencia" (records generated
                        during an incident, e.g., issue_date is before today).
                        This adds RemisionVoluntaria/Incidencia="S" to the header.

        Returns:
            Response from AEAT service

        Raises:
            AeatException: If AEAT server returned an error
            requests.RequestException: If request sending failed
        """
        # Build XML request
        xml_body = self._build_xml_request(records, incidencia=incidencia)

        if debug:
            print("\n=== DEBUG: Request XML ===")
            print(xml_body)
            print("=" * 50 + "\n")

        # Prepare request
        url = f"{self._get_base_uri()}/wlpl/TIKE-CONT/ws/SistemaFacturacion/VerifactuSOAP"
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "User-Agent": f"Mozilla/5.0 (compatible; {self.system.name}/{self.system.version})",
        }

        # Configure certificate
        cert = None
        if self.certificate_path:
            if self.certificate_password:
                # For PKCS#12 with password, we need to pass as tuple
                cert = (self.certificate_path, self.certificate_password)
            else:
                # For PEM or unencrypted certificate
                cert = self.certificate_path

        # Send request
        try:
            response = self.client.post(
                url,
                data=xml_body.encode("utf-8"),
                headers=headers,
                cert=cert,
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise AeatException(f"Failed to send request to AEAT: {e}") from e

        if debug:
            print("\n=== DEBUG: Response XML ===")
            print(response.text)
            print("=" * 50 + "\n")

        # Parse and return response
        try:
            return AeatResponse.from_xml(response.text)
        except AeatException as e:
            # Add response text to error for debugging
            if debug:
                print(f"\n=== DEBUG: Error parsing response ===")
                print(f"Error: {e}")
                print("=" * 50 + "\n")
            raise

    def _get_base_uri(self) -> str:
        """Get base URI of web service"""
        if self.is_production:
            return "https://www1.agenciatributaria.gob.es"
        else:
            return "https://prewww1.aeat.es"

    def _build_xml_request(
        self, records: Sequence[Union[RegistrationRecord, CancellationRecord]],
        incidencia: bool = False
    ) -> str:
        """
        Build SOAP XML request

        Args:
            records: Records to include in request
            incidencia: If True, adds RemisionVoluntaria/Incidencia="S" to header

        Returns:
            XML string ready to send
        """
        # Register namespaces globally for proper serialization
        ET.register_namespace('soapenv', self.NS_SOAPENV)
        ET.register_namespace('sum', self.NS_SUM)
        ET.register_namespace('sum1', self.NS_SUM1)

        # Build envelope - namespaces will be added automatically by ElementTree
        envelope = ET.Element(f"{{{self.NS_SOAPENV}}}Envelope")

        # Add header
        ET.SubElement(envelope, f"{{{self.NS_SOAPENV}}}Header")

        # Add body
        body = ET.SubElement(envelope, f"{{{self.NS_SOAPENV}}}Body")
        base_element = ET.SubElement(
            body, f"{{{self.NS_SUM}}}RegFactuSistemaFacturacion"
        )

        # Add header section
        cabecera = ET.SubElement(base_element, f"{{{self.NS_SUM}}}Cabecera")
        obligado_emision = ET.SubElement(
            cabecera, f"{{{self.NS_SUM1}}}ObligadoEmision"
        )
        ET.SubElement(
            obligado_emision, f"{{{self.NS_SUM1}}}NombreRazon"
        ).text = self.taxpayer.name
        ET.SubElement(
            obligado_emision, f"{{{self.NS_SUM1}}}NIF"
        ).text = self.taxpayer.nif

        # Add representative if present
        if self.representative:
            representante = ET.SubElement(
                cabecera, f"{{{self.NS_SUM1}}}Representante"
            )
            ET.SubElement(
                representante, f"{{{self.NS_SUM1}}}NombreRazon"
            ).text = self.representative.name
            ET.SubElement(
                representante, f"{{{self.NS_SUM1}}}NIF"
            ).text = self.representative.nif

        # Add RemisionVoluntaria if incidencia flag is set
        # According to XSD: RemisionVoluntaria contains FechaFinVeriFactu (optional) and Incidencia
        # Incidencia="S" indicates records were generated during an incident (e.g., backdated invoices)
        if incidencia:
            remision_voluntaria = ET.SubElement(
                cabecera, f"{{{self.NS_SUM1}}}RemisionVoluntaria"
            )
            ET.SubElement(
                remision_voluntaria, f"{{{self.NS_SUM1}}}Incidencia"
            ).text = "S"

        # Add records
        for record in records:
            self._export_record(base_element, record)

        # Convert to string
        return ET.tostring(envelope, encoding="unicode", method="xml")

    def _export_record(
        self,
        base_element: ET.Element,
        record: Union[RegistrationRecord, CancellationRecord],
    ) -> None:
        """
        Export a record to XML

        Args:
            base_element: Base XML element to append to
            record: Record to export
        """
        # Create registro_factura element
        registro_factura = ET.SubElement(
            base_element, f"{{{self.NS_SUM}}}RegistroFactura"
        )

        # Determine record type
        if isinstance(record, RegistrationRecord):
            record_element_name = "RegistroAlta"
        else:
            record_element_name = "RegistroAnulacion"

        record_element = ET.SubElement(
            registro_factura, f"{{{self.NS_SUM1}}}{record_element_name}"
        )

        # Add version
        ET.SubElement(
            record_element, f"{{{self.NS_SUM1}}}IDVersion"
        ).text = "1.0"

        # Export record-specific properties
        if isinstance(record, RegistrationRecord):
            self._export_registration_record(record_element, record)
        else:
            self._export_cancellation_record(record_element, record)

        # Add chaining (Encadenamiento)
        self._add_chaining(record_element, record)

        # Add computer system
        self._add_computer_system(record_element)

        # Add hash metadata (format with timezone like PHP does: 'c' format)
        # Format: 2025-10-23T11:27:07+01:00 (NO microseconds!)
        # Use local timezone like PHP does with format('c')
        import datetime
        import time

        dt = record.hashed_at

        # If no timezone info, add local timezone (like PHP does)
        if dt.tzinfo is None:
            # Get local timezone offset
            if time.daylight and time.localtime().tm_isdst:
                # Daylight saving time is in effect
                offset_seconds = -time.altzone
            else:
                # Standard time
                offset_seconds = -time.timezone

            local_tz = datetime.timezone(datetime.timedelta(seconds=offset_seconds))
            dt = dt.replace(tzinfo=local_tz)

        # Format without microseconds: YYYY-MM-DDTHH:MM:SS+HH:MM
        dt_str = dt.strftime('%Y-%m-%dT%H:%M:%S')

        # Add timezone offset in format +HH:MM
        offset = dt.utcoffset()
        if offset is not None:
            total_seconds = int(offset.total_seconds())
            hours, remainder = divmod(abs(total_seconds), 3600)
            minutes = remainder // 60
            sign = '+' if total_seconds >= 0 else '-'
            dt_str += f'{sign}{hours:02d}:{minutes:02d}'
        else:
            dt_str += '+00:00'

        ET.SubElement(
            record_element, f"{{{self.NS_SUM1}}}FechaHoraHusoGenRegistro"
        ).text = dt_str
        ET.SubElement(
            record_element, f"{{{self.NS_SUM1}}}TipoHuella"
        ).text = "01"  # SHA-256
        ET.SubElement(record_element, f"{{{self.NS_SUM1}}}Huella").text = (
            record.hash
        )

        # Add optional fields
        if record.previous_rejection:
            ET.SubElement(
                record_element, f"{{{self.NS_SUM1}}}RechazoPrevio"
            ).text = record.previous_rejection

        if record.correction:
            ET.SubElement(
                record_element, f"{{{self.NS_SUM1}}}Subsanacion"
            ).text = record.correction

        if record.external_reference:
            ET.SubElement(
                record_element, f"{{{self.NS_SUM1}}}RefExterna"
            ).text = record.external_reference

    def _export_registration_record(
        self, record_element: ET.Element, record: RegistrationRecord
    ) -> None:
        """Export registration record specific fields"""
        # Add invoice ID
        self._add_invoice_id(record_element, record.invoice_id)

        # Add issuer name
        ET.SubElement(
            record_element, f"{{{self.NS_SUM1}}}NombreRazonEmisor"
        ).text = record.issuer_name

        # Add invoice type
        ET.SubElement(
            record_element, f"{{{self.NS_SUM1}}}TipoFactura"
        ).text = record.invoice_type.value

        # Add corrective type if present
        if record.corrective_type:
            ET.SubElement(
                record_element, f"{{{self.NS_SUM1}}}TipoRectificativa"
            ).text = record.corrective_type.value

        # Add description if present
        if record.description:
            ET.SubElement(
                record_element, f"{{{self.NS_SUM1}}}DescripcionOperacion"
            ).text = record.description

        # Add recipients (Destinatarios)
        if record.recipients:
            destinatarios = ET.SubElement(
                record_element, f"{{{self.NS_SUM1}}}Destinatarios"
            )
            for recipient in record.recipients:
                id_destinatario = ET.SubElement(
                    destinatarios, f"{{{self.NS_SUM1}}}IDDestinatario"
                )
                ET.SubElement(
                    id_destinatario, f"{{{self.NS_SUM1}}}NombreRazon"
                ).text = recipient.name
                ET.SubElement(
                    id_destinatario, f"{{{self.NS_SUM1}}}NIF"
                ).text = recipient.nif

        # Add breakdown (Desglose)
        desglose = ET.SubElement(
            record_element, f"{{{self.NS_SUM1}}}Desglose"
        )
        for detail in record.breakdown:
            detalle = ET.SubElement(
                desglose, f"{{{self.NS_SUM1}}}DetalleDesglose"
            )
            ET.SubElement(
                detalle, f"{{{self.NS_SUM1}}}Impuesto"
            ).text = detail.tax_type.value
            ET.SubElement(
                detalle, f"{{{self.NS_SUM1}}}ClaveRegimen"
            ).text = detail.regime_type.value
            ET.SubElement(
                detalle, f"{{{self.NS_SUM1}}}CalificacionOperacion"
            ).text = detail.operation_type.value
            ET.SubElement(
                detalle, f"{{{self.NS_SUM1}}}TipoImpositivo"
            ).text = detail.tax_rate
            ET.SubElement(
                detalle, f"{{{self.NS_SUM1}}}BaseImponibleOimporteNoSujeto"
            ).text = detail.base_amount
            ET.SubElement(
                detalle, f"{{{self.NS_SUM1}}}CuotaRepercutida"
            ).text = detail.tax_amount

        # Add totals
        ET.SubElement(
            record_element, f"{{{self.NS_SUM1}}}CuotaTotal"
        ).text = record.total_tax_amount
        ET.SubElement(
            record_element, f"{{{self.NS_SUM1}}}ImporteTotal"
        ).text = record.total_amount

    def _export_cancellation_record(
        self, record_element: ET.Element, record: CancellationRecord
    ) -> None:
        """Export cancellation record specific fields"""
        # Add invoice ID
        self._add_invoice_id(record_element, record.invoice_id)

        # Add issuer name
        ET.SubElement(
            record_element, f"{{{self.NS_SUM1}}}NombreRazonEmisor"
        ).text = record.issuer_name

        # Add cancellation type
        ET.SubElement(
            record_element, f"{{{self.NS_SUM1}}}TipoFactura"
        ).text = record.cancellation_type.value

    def _add_invoice_id(
        self, parent: ET.Element, invoice_id
    ) -> None:
        """Add invoice ID to XML element"""
        id_factura = ET.SubElement(parent, f"{{{self.NS_SUM1}}}IDFactura")
        ET.SubElement(
            id_factura, f"{{{self.NS_SUM1}}}IDEmisorFactura"
        ).text = invoice_id.issuer_id
        ET.SubElement(
            id_factura, f"{{{self.NS_SUM1}}}NumSerieFactura"
        ).text = invoice_id.invoice_number
        ET.SubElement(
            id_factura, f"{{{self.NS_SUM1}}}FechaExpedicionFactura"
        ).text = invoice_id.issue_date.strftime("%d-%m-%Y")

    def _add_chaining(self, record_element: ET.Element, record: Record) -> None:
        """Add chaining information to record"""
        encadenamiento = ET.SubElement(
            record_element, f"{{{self.NS_SUM1}}}Encadenamiento"
        )

        if record.previous_invoice_id is None:
            ET.SubElement(
                encadenamiento, f"{{{self.NS_SUM1}}}PrimerRegistro"
            ).text = "S"
        else:
            registro_anterior = ET.SubElement(
                encadenamiento, f"{{{self.NS_SUM1}}}RegistroAnterior"
            )
            ET.SubElement(
                registro_anterior, f"{{{self.NS_SUM1}}}IDEmisorFactura"
            ).text = record.previous_invoice_id.issuer_id
            ET.SubElement(
                registro_anterior, f"{{{self.NS_SUM1}}}NumSerieFactura"
            ).text = record.previous_invoice_id.invoice_number
            ET.SubElement(
                registro_anterior, f"{{{self.NS_SUM1}}}FechaExpedicionFactura"
            ).text = record.previous_invoice_id.issue_date.strftime("%d-%m-%Y")
            ET.SubElement(
                registro_anterior, f"{{{self.NS_SUM1}}}Huella"
            ).text = record.previous_hash

    def _add_computer_system(self, record_element: ET.Element) -> None:
        """Add computer system information to record"""
        sistema = ET.SubElement(
            record_element, f"{{{self.NS_SUM1}}}SistemaInformatico"
        )
        ET.SubElement(
            sistema, f"{{{self.NS_SUM1}}}NombreRazon"
        ).text = self.system.vendor_name
        ET.SubElement(sistema, f"{{{self.NS_SUM1}}}NIF").text = self.system.vendor_nif
        ET.SubElement(
            sistema, f"{{{self.NS_SUM1}}}NombreSistemaInformatico"
        ).text = self.system.name
        ET.SubElement(
            sistema, f"{{{self.NS_SUM1}}}IdSistemaInformatico"
        ).text = self.system.id
        ET.SubElement(
            sistema, f"{{{self.NS_SUM1}}}Version"
        ).text = self.system.version
        ET.SubElement(
            sistema, f"{{{self.NS_SUM1}}}NumeroInstalacion"
        ).text = self.system.installation_number
        ET.SubElement(
            sistema, f"{{{self.NS_SUM1}}}TipoUsoPosibleSoloVerifactu"
        ).text = ("S" if self.system.only_supports_verifactu else "N")
        ET.SubElement(
            sistema, f"{{{self.NS_SUM1}}}TipoUsoPosibleMultiOT"
        ).text = ("S" if self.system.supports_multiple_taxpayers else "N")
        ET.SubElement(
            sistema, f"{{{self.NS_SUM1}}}IndicadorMultiplesOT"
        ).text = ("S" if self.system.has_multiple_taxpayers else "N")

    def query(
        self, query_filter: QueryFilter, debug: bool = False
    ) -> QueryResponse:
        """
        Query invoices submitted to AEAT

        Args:
            query_filter: Filter parameters for the query
            debug: If True, print request and response XML for debugging

        Returns:
            QueryResponse with the list of invoices

        Raises:
            AeatException: If AEAT server returned an error
            requests.RequestException: If request sending failed
        """
        # Build XML request
        xml_body = self._build_query_xml_request(query_filter)

        if debug:
            print("\n=== DEBUG: Query Request XML ===")
            print(xml_body)
            print("=" * 50 + "\n")

        # Prepare request - use same endpoint as send, different SOAP action
        url = f"{self._get_base_uri()}/wlpl/TIKE-CONT/ws/SistemaFacturacion/VerifactuSOAP"
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "User-Agent": f"Mozilla/5.0 (compatible; {self.system.name}/{self.system.version})",
        }

        # Configure certificate
        cert = None
        if self.certificate_path:
            if self.certificate_password:
                cert = (self.certificate_path, self.certificate_password)
            else:
                cert = self.certificate_path

        # Send request
        try:
            response = self.client.post(
                url,
                data=xml_body.encode("utf-8"),
                headers=headers,
                cert=cert,
                timeout=60,  # Queries can take longer
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise AeatException(f"Failed to send query request to AEAT: {e}") from e

        if debug:
            print("\n=== DEBUG: Query Response XML ===")
            print(response.text)
            print("=" * 50 + "\n")

        # Parse and return response
        try:
            return QueryResponse.from_xml(response.text)
        except AeatException as e:
            if debug:
                print(f"\n=== DEBUG: Error parsing query response ===")
                print(f"Error: {e}")
                print("=" * 50 + "\n")
            raise

    def build_record_xml(
        self, record: Union[RegistrationRecord, CancellationRecord]
    ) -> str:
        """
        Build XML representation of a single invoice record in AEAT format.

        This method generates the XML for a single record (RegistroFactura containing
        RegistroAlta or RegistroAnulacion) without the SOAP envelope.
        Useful for viewing/exporting invoice data in AEAT format.

        Args:
            record: The registration or cancellation record to serialize

        Returns:
            XML string representation of the record
        """
        # Reuse existing _build_xml_request with a single record
        full_xml = self._build_xml_request([record])

        # Extract just the RegistroFactura element from the full SOAP XML
        # Parse and find the RegistroFactura element
        root = ET.fromstring(full_xml)

        # Find RegistroFactura in the XML tree (it's nested inside Body/RegFactuSistemaFacturacion)
        registro_factura = root.find(f".//{{{self.NS_SUM}}}RegistroFactura")

        if registro_factura is None:
            raise ValueError("Could not find RegistroFactura in generated XML")

        return ET.tostring(registro_factura, encoding="unicode", method="xml")

    def _build_query_xml_request(self, query_filter: QueryFilter) -> str:
        """
        Build SOAP XML request for invoice query

        Args:
            query_filter: Filter parameters for the query

        Returns:
            XML string ready to send
        """
        # Register namespaces globally for proper serialization
        ET.register_namespace('soapenv', self.NS_SOAPENV)
        ET.register_namespace('con', self.NS_CONS)
        ET.register_namespace('sum1', self.NS_SUM1)

        # Build envelope
        envelope = ET.Element(f"{{{self.NS_SOAPENV}}}Envelope")

        # Add header
        ET.SubElement(envelope, f"{{{self.NS_SOAPENV}}}Header")

        # Add body
        body = ET.SubElement(envelope, f"{{{self.NS_SOAPENV}}}Body")
        base_element = ET.SubElement(
            body, f"{{{self.NS_CONS}}}ConsultaFactuSistemaFacturacion"
        )

        # Add header section (Cabecera) - element in ConsultaLR namespace, content in SuministroInformacion
        cabecera = ET.SubElement(base_element, f"{{{self.NS_CONS}}}Cabecera")

        # Add version
        ET.SubElement(cabecera, f"{{{self.NS_SUM1}}}IDVersion").text = "1.0"

        # Add obligado emision (issuer)
        obligado_emision = ET.SubElement(
            cabecera, f"{{{self.NS_SUM1}}}ObligadoEmision"
        )
        ET.SubElement(
            obligado_emision, f"{{{self.NS_SUM1}}}NombreRazon"
        ).text = self.taxpayer.name
        ET.SubElement(
            obligado_emision, f"{{{self.NS_SUM1}}}NIF"
        ).text = self.taxpayer.nif

        # Add representative if present
        if self.representative:
            ET.SubElement(
                cabecera, f"{{{self.NS_SUM1}}}IndicadorRepresentante"
            ).text = "S"

        # Add filter section (FiltroConsulta) - elements in ConsultaLR namespace
        filtro = ET.SubElement(base_element, f"{{{self.NS_CONS}}}FiltroConsulta")

        # Add period (required) - element in ConsultaLR namespace, subelements in SuministroInformacion
        periodo = ET.SubElement(filtro, f"{{{self.NS_CONS}}}PeriodoImputacion")
        ET.SubElement(
            periodo, f"{{{self.NS_SUM1}}}Ejercicio"
        ).text = query_filter.period.ejercicio
        ET.SubElement(
            periodo, f"{{{self.NS_SUM1}}}Periodo"
        ).text = query_filter.period.periodo

        # Add invoice number filter (optional)
        if query_filter.invoice_number:
            ET.SubElement(
                filtro, f"{{{self.NS_CONS}}}NumSerieFactura"
            ).text = query_filter.invoice_number

        # Add counterparty filter (optional)
        if query_filter.counterparty_nif:
            contraparte = ET.SubElement(filtro, f"{{{self.NS_CONS}}}Contraparte")
            ET.SubElement(
                contraparte, f"{{{self.NS_SUM1}}}NIF"
            ).text = query_filter.counterparty_nif

        # Add date filter (optional)
        if query_filter.date_from or query_filter.date_to:
            fecha_expedicion = ET.SubElement(
                filtro, f"{{{self.NS_CONS}}}FechaExpedicionFactura"
            )
            if query_filter.date_from:
                ET.SubElement(
                    fecha_expedicion, f"{{{self.NS_SUM1}}}Desde"
                ).text = query_filter.date_from.strftime("%d-%m-%Y")
            if query_filter.date_to:
                ET.SubElement(
                    fecha_expedicion, f"{{{self.NS_SUM1}}}Hasta"
                ).text = query_filter.date_to.strftime("%d-%m-%Y")

        # Add external reference filter (optional)
        if query_filter.external_reference:
            ET.SubElement(
                filtro, f"{{{self.NS_CONS}}}RefExterna"
            ).text = query_filter.external_reference

        # Add pagination key (optional)
        if query_filter.pagination_key:
            ET.SubElement(
                filtro, f"{{{self.NS_CONS}}}ClavePaginacion"
            ).text = query_filter.pagination_key

        # Add additional response options (DatosAdicionalesRespuesta)
        datos_adicionales = ET.SubElement(
            base_element, f"{{{self.NS_CONS}}}DatosAdicionalesRespuesta"
        )
        ET.SubElement(
            datos_adicionales, f"{{{self.NS_CONS}}}MostrarNombreRazonEmisor"
        ).text = "S" if query_filter.show_issuer_name else "N"
        ET.SubElement(
            datos_adicionales, f"{{{self.NS_CONS}}}MostrarSistemaInformatico"
        ).text = "S" if query_filter.show_computer_system else "N"

        # Convert to string
        return ET.tostring(envelope, encoding="unicode", method="xml")
