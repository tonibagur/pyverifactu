"""Tests for AeatClient query functionality"""

import pytest
from datetime import date

from verifactu import (
    AeatClient,
    ComputerSystem,
    FiscalIdentifier,
    QueryPeriod,
    QueryFilter,
)


class TestAeatClientQueryXmlGeneration:
    """Tests for query XML generation"""

    @pytest.fixture
    def client(self):
        """Create AeatClient for testing"""
        system = ComputerSystem(
            vendor_name="Test Vendor",
            vendor_nif="B12345678",
            name="Test System",
            id="TS",
            version="1.0.0",
            installation_number="TEST-001",
            only_supports_verifactu=True,
            supports_multiple_taxpayers=False,
            has_multiple_taxpayers=False,
        )
        taxpayer = FiscalIdentifier(name="Test Company", nif="A12345678")
        return AeatClient(system, taxpayer)

    def test_build_query_xml_minimal(self, client):
        """Test building query XML with minimal parameters"""
        period = QueryPeriod(year=2025, month=11)
        filter = QueryFilter(period=period)

        xml = client._build_query_xml_request(filter)

        # Check SOAP envelope
        assert 'Envelope' in xml
        assert 'Body' in xml

        # Check ConsultaFactuSistemaFacturacion element
        assert 'ConsultaFactuSistemaFacturacion' in xml

        # Check header (Cabecera)
        assert 'Cabecera' in xml
        assert 'IDVersion' in xml
        assert '1.0' in xml
        assert 'ObligadoEmision' in xml
        assert 'Test Company' in xml
        assert 'A12345678' in xml

        # Check filter section
        assert 'FiltroConsulta' in xml
        assert 'PeriodoImputacion' in xml
        assert 'Ejercicio' in xml
        assert '2025' in xml
        assert 'Periodo' in xml
        assert '11' in xml

        # Check additional options
        assert 'DatosAdicionalesRespuesta' in xml
        assert 'MostrarNombreRazonEmisor' in xml
        assert 'MostrarSistemaInformatico' in xml

    def test_build_query_xml_with_invoice_number(self, client):
        """Test building query XML with invoice number filter"""
        period = QueryPeriod(year=2025, month=11)
        filter = QueryFilter(period=period, invoice_number="FACT-001")

        xml = client._build_query_xml_request(filter)

        assert 'NumSerieFactura' in xml
        assert 'FACT-001' in xml

    def test_build_query_xml_with_date_range(self, client):
        """Test building query XML with date range filter"""
        period = QueryPeriod(year=2025, month=11)
        filter = QueryFilter(
            period=period,
            date_from=date(2025, 11, 1),
            date_to=date(2025, 11, 15),
        )

        xml = client._build_query_xml_request(filter)

        assert 'FechaExpedicionFactura' in xml
        assert 'Desde' in xml
        assert '01-11-2025' in xml
        assert 'Hasta' in xml
        assert '15-11-2025' in xml

    def test_build_query_xml_with_counterparty(self, client):
        """Test building query XML with counterparty filter"""
        period = QueryPeriod(year=2025, month=11)
        filter = QueryFilter(period=period, counterparty_nif="12345678A")

        xml = client._build_query_xml_request(filter)

        assert 'Contraparte' in xml
        assert '12345678A' in xml

    def test_build_query_xml_with_pagination(self, client):
        """Test building query XML with pagination key"""
        period = QueryPeriod(year=2025, month=11)
        filter = QueryFilter(period=period, pagination_key="abc123xyz")

        xml = client._build_query_xml_request(filter)

        assert 'ClavePaginacion' in xml
        assert 'abc123xyz' in xml

    def test_build_query_xml_show_options(self, client):
        """Test building query XML with show options"""
        period = QueryPeriod(year=2025, month=11)
        filter = QueryFilter(
            period=period,
            show_issuer_name=False,
            show_computer_system=True,
        )

        xml = client._build_query_xml_request(filter)

        # Check that options are included with correct values
        assert 'MostrarNombreRazonEmisor' in xml
        assert 'MostrarSistemaInformatico' in xml
        # The values should be N and S respectively
        assert '>N<' in xml  # MostrarNombreRazonEmisor = N
        assert '>S<' in xml  # MostrarSistemaInformatico = S

    def test_build_query_xml_with_external_reference(self, client):
        """Test building query XML with external reference"""
        period = QueryPeriod(year=2025, month=11)
        filter = QueryFilter(period=period, external_reference="REF-001")

        xml = client._build_query_xml_request(filter)

        assert 'RefExterna' in xml
        assert 'REF-001' in xml

    def test_query_method_exists(self, client):
        """Test that query method exists on client"""
        assert hasattr(client, 'query')
        assert callable(client.query)
