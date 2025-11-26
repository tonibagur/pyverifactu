"""Tests for QueryResponse XML parsing"""

import pytest
from verifactu.models.responses.query_response import QueryResponse, QueryResultType


class TestQueryResponseParsing:
    """Tests for parsing AEAT query response XML"""

    def test_parse_response_with_first_record(self):
        """Test parsing response where invoice is first in chain"""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
        <env:Body>
        <tikLRRC:RespuestaConsultaFactuSistemaFacturacion
            xmlns:tik="https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd"
            xmlns:tikLRRC="https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd">
            <tikLRRC:PeriodoImputacion>
                <tikLRRC:Ejercicio>2025</tikLRRC:Ejercicio>
                <tikLRRC:Periodo>11</tikLRRC:Periodo>
            </tikLRRC:PeriodoImputacion>
            <tikLRRC:IndicadorPaginacion>N</tikLRRC:IndicadorPaginacion>
            <tikLRRC:ResultadoConsulta>ConDatos</tikLRRC:ResultadoConsulta>
            <tikLRRC:RegistroRespuestaConsultaFactuSistemaFacturacion>
                <tikLRRC:IDFactura>
                    <tik:IDEmisorFactura>B12345678</tik:IDEmisorFactura>
                    <tik:NumSerieFactura>FACT-001</tik:NumSerieFactura>
                    <tik:FechaExpedicionFactura>25-11-2025</tik:FechaExpedicionFactura>
                </tikLRRC:IDFactura>
                <tikLRRC:DatosRegistroFacturacion>
                    <tikLRRC:NombreRazonEmisor>Test Company</tikLRRC:NombreRazonEmisor>
                    <tikLRRC:TipoFactura>F1</tikLRRC:TipoFactura>
                    <tikLRRC:DescripcionOperacion>Test invoice</tikLRRC:DescripcionOperacion>
                    <tikLRRC:ImporteTotal>121.00</tikLRRC:ImporteTotal>
                    <tikLRRC:CuotaTotal>21.00</tikLRRC:CuotaTotal>
                    <tikLRRC:Huella>ABC123DEF456</tikLRRC:Huella>
                    <tikLRRC:Encadenamiento>
                        <tikLRRC:PrimerRegistro>S</tikLRRC:PrimerRegistro>
                    </tikLRRC:Encadenamiento>
                </tikLRRC:DatosRegistroFacturacion>
                <tikLRRC:EstadoRegistro>
                    <tikLRRC:EstadoRegistro>Correcto</tikLRRC:EstadoRegistro>
                </tikLRRC:EstadoRegistro>
            </tikLRRC:RegistroRespuestaConsultaFactuSistemaFacturacion>
        </tikLRRC:RespuestaConsultaFactuSistemaFacturacion>
        </env:Body>
        </env:Envelope>'''

        response = QueryResponse.from_xml(xml)

        assert response.year == 2025
        assert response.month == 11
        assert response.result_type == QueryResultType.WITH_DATA
        assert response.has_more_pages is False
        assert len(response.items) == 1

        item = response.items[0]
        assert item.invoice_id.issuer_id == "B12345678"
        assert item.invoice_id.invoice_number == "FACT-001"
        assert item.issuer_name == "Test Company"
        assert item.invoice_type == "F1"
        assert item.hash == "ABC123DEF456"
        assert item.is_first_record is True
        assert item.previous_record is None

    def test_parse_response_with_previous_record(self):
        """Test parsing response where invoice has previous record in chain"""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
        <env:Body>
        <tikLRRC:RespuestaConsultaFactuSistemaFacturacion
            xmlns:tik="https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd"
            xmlns:tikLRRC="https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd">
            <tikLRRC:PeriodoImputacion>
                <tikLRRC:Ejercicio>2025</tikLRRC:Ejercicio>
                <tikLRRC:Periodo>11</tikLRRC:Periodo>
            </tikLRRC:PeriodoImputacion>
            <tikLRRC:IndicadorPaginacion>N</tikLRRC:IndicadorPaginacion>
            <tikLRRC:ResultadoConsulta>ConDatos</tikLRRC:ResultadoConsulta>
            <tikLRRC:RegistroRespuestaConsultaFactuSistemaFacturacion>
                <tikLRRC:IDFactura>
                    <tik:IDEmisorFactura>B12345678</tik:IDEmisorFactura>
                    <tik:NumSerieFactura>FACT-002</tik:NumSerieFactura>
                    <tik:FechaExpedicionFactura>26-11-2025</tik:FechaExpedicionFactura>
                </tikLRRC:IDFactura>
                <tikLRRC:DatosRegistroFacturacion>
                    <tikLRRC:NombreRazonEmisor>Test Company</tikLRRC:NombreRazonEmisor>
                    <tikLRRC:TipoFactura>F1</tikLRRC:TipoFactura>
                    <tikLRRC:Huella>DEF789GHI012</tikLRRC:Huella>
                    <tikLRRC:Encadenamiento>
                        <tikLRRC:RegistroAnterior>
                            <tik:IDEmisorFactura>B12345678</tik:IDEmisorFactura>
                            <tik:NumSerieFactura>FACT-001</tik:NumSerieFactura>
                            <tik:FechaExpedicionFactura>25-11-2025</tik:FechaExpedicionFactura>
                            <tik:Huella>ABC123DEF456</tik:Huella>
                        </tikLRRC:RegistroAnterior>
                    </tikLRRC:Encadenamiento>
                </tikLRRC:DatosRegistroFacturacion>
                <tikLRRC:EstadoRegistro>
                    <tikLRRC:EstadoRegistro>Correcto</tikLRRC:EstadoRegistro>
                </tikLRRC:EstadoRegistro>
            </tikLRRC:RegistroRespuestaConsultaFactuSistemaFacturacion>
        </tikLRRC:RespuestaConsultaFactuSistemaFacturacion>
        </env:Body>
        </env:Envelope>'''

        response = QueryResponse.from_xml(xml)

        assert len(response.items) == 1
        item = response.items[0]

        assert item.invoice_id.invoice_number == "FACT-002"
        assert item.hash == "DEF789GHI012"
        assert item.is_first_record is False
        assert item.previous_record is not None
        assert item.previous_record.issuer_nif == "B12345678"
        assert item.previous_record.invoice_number == "FACT-001"
        assert item.previous_record.hash == "ABC123DEF456"
        assert item.previous_record.issue_date.day == 25
        assert item.previous_record.issue_date.month == 11
        assert item.previous_record.issue_date.year == 2025

    def test_parse_response_without_data(self):
        """Test parsing response with no data"""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
        <env:Body>
        <tikLRRC:RespuestaConsultaFactuSistemaFacturacion
            xmlns:tik="https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd"
            xmlns:tikLRRC="https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd">
            <tikLRRC:PeriodoImputacion>
                <tikLRRC:Ejercicio>2025</tikLRRC:Ejercicio>
                <tikLRRC:Periodo>10</tikLRRC:Periodo>
            </tikLRRC:PeriodoImputacion>
            <tikLRRC:IndicadorPaginacion>N</tikLRRC:IndicadorPaginacion>
            <tikLRRC:ResultadoConsulta>SinDatos</tikLRRC:ResultadoConsulta>
        </tikLRRC:RespuestaConsultaFactuSistemaFacturacion>
        </env:Body>
        </env:Envelope>'''

        response = QueryResponse.from_xml(xml)

        assert response.year == 2025
        assert response.month == 10
        assert response.result_type == QueryResultType.WITHOUT_DATA
        assert response.has_more_pages is False
        assert len(response.items) == 0

    def test_parse_response_with_pagination(self):
        """Test parsing response with pagination"""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
        <env:Body>
        <tikLRRC:RespuestaConsultaFactuSistemaFacturacion
            xmlns:tik="https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd"
            xmlns:tikLRRC="https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd">
            <tikLRRC:PeriodoImputacion>
                <tikLRRC:Ejercicio>2025</tikLRRC:Ejercicio>
                <tikLRRC:Periodo>11</tikLRRC:Periodo>
            </tikLRRC:PeriodoImputacion>
            <tikLRRC:IndicadorPaginacion>S</tikLRRC:IndicadorPaginacion>
            <tikLRRC:ResultadoConsulta>ConDatos</tikLRRC:ResultadoConsulta>
            <tikLRRC:ClavePaginacion>NEXT_PAGE_KEY_123</tikLRRC:ClavePaginacion>
        </tikLRRC:RespuestaConsultaFactuSistemaFacturacion>
        </env:Body>
        </env:Envelope>'''

        response = QueryResponse.from_xml(xml)

        assert response.has_more_pages is True
        assert response.pagination_key == "NEXT_PAGE_KEY_123"

    def test_parse_response_with_recipients_and_breakdown(self):
        """Test parsing response with recipients and tax breakdown"""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
        <env:Body>
        <tikLRRC:RespuestaConsultaFactuSistemaFacturacion
            xmlns:tik="https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd"
            xmlns:tikLRRC="https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd">
            <tikLRRC:PeriodoImputacion>
                <tikLRRC:Ejercicio>2025</tikLRRC:Ejercicio>
                <tikLRRC:Periodo>11</tikLRRC:Periodo>
            </tikLRRC:PeriodoImputacion>
            <tikLRRC:IndicadorPaginacion>N</tikLRRC:IndicadorPaginacion>
            <tikLRRC:ResultadoConsulta>ConDatos</tikLRRC:ResultadoConsulta>
            <tikLRRC:RegistroRespuestaConsultaFactuSistemaFacturacion>
                <tikLRRC:IDFactura>
                    <tik:IDEmisorFactura>B12345678</tik:IDEmisorFactura>
                    <tik:NumSerieFactura>FACT-001</tik:NumSerieFactura>
                    <tik:FechaExpedicionFactura>25-11-2025</tik:FechaExpedicionFactura>
                </tikLRRC:IDFactura>
                <tikLRRC:DatosRegistroFacturacion>
                    <tikLRRC:NombreRazonEmisor>Seller Company</tikLRRC:NombreRazonEmisor>
                    <tikLRRC:TipoFactura>F1</tikLRRC:TipoFactura>
                    <tikLRRC:ImporteTotal>1478.61</tikLRRC:ImporteTotal>
                    <tikLRRC:CuotaTotal>256.62</tikLRRC:CuotaTotal>
                    <tikLRRC:Destinatarios>
                        <tikLRRC:IDDestinatario>
                            <tik:NombreRazon>Buyer Name</tik:NombreRazon>
                            <tik:NIF>12345678A</tik:NIF>
                        </tikLRRC:IDDestinatario>
                    </tikLRRC:Destinatarios>
                    <tikLRRC:Desglose>
                        <tik:DetalleDesglose>
                            <tik:Impuesto>01</tik:Impuesto>
                            <tik:ClaveRegimen>01</tik:ClaveRegimen>
                            <tik:CalificacionOperacion>S1</tik:CalificacionOperacion>
                            <tik:TipoImpositivo>21</tik:TipoImpositivo>
                            <tik:BaseImponibleOimporteNoSujeto>1221.99</tik:BaseImponibleOimporteNoSujeto>
                            <tik:CuotaRepercutida>256.62</tik:CuotaRepercutida>
                        </tik:DetalleDesglose>
                    </tikLRRC:Desglose>
                    <tikLRRC:Encadenamiento>
                        <tikLRRC:PrimerRegistro>S</tikLRRC:PrimerRegistro>
                    </tikLRRC:Encadenamiento>
                </tikLRRC:DatosRegistroFacturacion>
                <tikLRRC:EstadoRegistro>
                    <tikLRRC:EstadoRegistro>Correcto</tikLRRC:EstadoRegistro>
                </tikLRRC:EstadoRegistro>
            </tikLRRC:RegistroRespuestaConsultaFactuSistemaFacturacion>
        </tikLRRC:RespuestaConsultaFactuSistemaFacturacion>
        </env:Body>
        </env:Envelope>'''

        response = QueryResponse.from_xml(xml)
        item = response.items[0]

        # Check recipients
        assert len(item.recipients) == 1
        assert item.recipients[0].name == "Buyer Name"
        assert item.recipients[0].nif == "12345678A"

        # Check breakdown
        assert len(item.breakdown) == 1
        assert item.breakdown[0].tax_type == "01"
        assert item.breakdown[0].regime_type == "01"
        assert item.breakdown[0].operation_type == "S1"
        assert item.breakdown[0].tax_rate == "21"
        assert item.breakdown[0].base_amount == "1221.99"
        assert item.breakdown[0].tax_amount == "256.62"

        # Check totals
        assert item.total_amount == "1478.61"
        assert item.total_tax_amount == "256.62"
