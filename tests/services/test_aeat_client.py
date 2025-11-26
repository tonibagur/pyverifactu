"""Tests for AeatClient XML generation."""

import pytest
from datetime import datetime

from verifactu.services.aeat_client import AeatClient
from verifactu.models.computer_system import ComputerSystem
from verifactu.models.records.fiscal_identifier import FiscalIdentifier
from verifactu.models.records.registration_record import RegistrationRecord
from verifactu.models.records.invoice_identifier import InvoiceIdentifier
from verifactu.models.records.breakdown_details import BreakdownDetails
from verifactu.models.records.invoice_type import InvoiceType
from verifactu.models.records.tax_type import TaxType
from verifactu.models.records.regime_type import RegimeType
from verifactu.models.records.operation_type import OperationType


class TestAeatClientXmlGeneration:
    """Tests for XML generation in AeatClient."""

    @pytest.fixture
    def computer_system(self) -> ComputerSystem:
        """Create a test computer system."""
        return ComputerSystem(
            vendor_name="Test Vendor SL",
            vendor_nif="B12345678",
            name="TestSystem",
            id="TS",
            version="1.0.0",
            installation_number="INST-001",
            only_supports_verifactu=True,
            supports_multiple_taxpayers=False,
            has_multiple_taxpayers=False,
        )

    @pytest.fixture
    def taxpayer(self) -> FiscalIdentifier:
        """Create a test taxpayer."""
        return FiscalIdentifier(name="Test Company SL", nif="A98765432")

    @pytest.fixture
    def sample_record(self) -> RegistrationRecord:
        """Create a sample registration record."""
        record = RegistrationRecord(
            invoice_id=InvoiceIdentifier(
                issuer_id="A98765432",
                invoice_number="FACT-2025-001",
                issue_date=datetime(2025, 1, 15),
            ),
            issuer_name="Test Company SL",
            invoice_type=InvoiceType.FACTURA,
            description="Test invoice",
            recipients=[
                FiscalIdentifier(name="Customer SL", nif="B11111111")
            ],
            breakdown=[
                BreakdownDetails(
                    tax_type=TaxType.IVA,
                    regime_type=RegimeType.C01,
                    operation_type=OperationType.SUBJECT,
                    tax_rate="21.00",
                    base_amount="100.00",
                    tax_amount="21.00",
                )
            ],
            total_tax_amount="21.00",
            total_amount="121.00",
            hashed_at=datetime(2025, 1, 15, 10, 0, 0),
            hash="",
        )
        record.hash = record.calculate_hash()
        return record

    def test_build_xml_without_incidencia(
        self, computer_system: ComputerSystem, taxpayer: FiscalIdentifier, sample_record: RegistrationRecord
    ):
        """Test that XML is generated without RemisionVoluntaria when incidencia=False."""
        client = AeatClient(computer_system, taxpayer)

        xml = client._build_xml_request([sample_record], incidencia=False)

        # Should not contain RemisionVoluntaria
        assert "RemisionVoluntaria" not in xml
        assert "<sum1:Incidencia>S</sum1:Incidencia>" not in xml

        # Should contain basic structure
        assert "Cabecera" in xml
        assert "ObligadoEmision" in xml
        assert "RegistroFactura" in xml

    def test_build_xml_with_incidencia(
        self, computer_system: ComputerSystem, taxpayer: FiscalIdentifier, sample_record: RegistrationRecord
    ):
        """Test that XML contains RemisionVoluntaria/Incidencia=S when incidencia=True."""
        client = AeatClient(computer_system, taxpayer)

        xml = client._build_xml_request([sample_record], incidencia=True)

        # Should contain RemisionVoluntaria with Incidencia=S
        assert "RemisionVoluntaria" in xml
        assert "<sum1:Incidencia>S</sum1:Incidencia>" in xml

        # Should contain basic structure
        assert "Cabecera" in xml
        assert "ObligadoEmision" in xml
        assert "RegistroFactura" in xml

    def test_build_xml_incidencia_after_obligado_emision(
        self, computer_system: ComputerSystem, taxpayer: FiscalIdentifier, sample_record: RegistrationRecord
    ):
        """Test that RemisionVoluntaria appears after ObligadoEmision in the XML."""
        client = AeatClient(computer_system, taxpayer)

        xml = client._build_xml_request([sample_record], incidencia=True)

        # RemisionVoluntaria should appear after ObligadoEmision
        obligado_pos = xml.find("ObligadoEmision")
        remision_pos = xml.find("RemisionVoluntaria")

        assert obligado_pos > 0, "ObligadoEmision should be in XML"
        assert remision_pos > 0, "RemisionVoluntaria should be in XML"
        assert remision_pos > obligado_pos, "RemisionVoluntaria should come after ObligadoEmision"

    def test_build_xml_with_representative_and_incidencia(
        self, computer_system: ComputerSystem, taxpayer: FiscalIdentifier, sample_record: RegistrationRecord
    ):
        """Test XML with both representative and incidencia flag."""
        client = AeatClient(computer_system, taxpayer)
        representative = FiscalIdentifier(name="Representative SL", nif="C22222222")
        client.set_representative(representative)

        xml = client._build_xml_request([sample_record], incidencia=True)

        # Should contain all elements
        assert "Representante" in xml
        assert "RemisionVoluntaria" in xml
        assert "<sum1:Incidencia>S</sum1:Incidencia>" in xml

        # Order should be: ObligadoEmision, Representante, RemisionVoluntaria
        obligado_pos = xml.find("ObligadoEmision")
        representante_pos = xml.find("Representante")
        remision_pos = xml.find("RemisionVoluntaria")

        assert obligado_pos < representante_pos < remision_pos

    def test_send_method_accepts_incidencia_parameter(
        self, computer_system: ComputerSystem, taxpayer: FiscalIdentifier
    ):
        """Test that send() method accepts incidencia parameter."""
        client = AeatClient(computer_system, taxpayer)

        # This should not raise any errors - just verify the method signature
        # We can't actually send without a certificate, but we can verify the parameter exists
        import inspect
        sig = inspect.signature(client.send)
        params = list(sig.parameters.keys())

        assert "incidencia" in params
        assert sig.parameters["incidencia"].default is False


class TestAeatClientIncidenciaIntegration:
    """Integration tests for incidencia flag behavior."""

    @pytest.fixture
    def client_setup(self):
        """Set up client with system and taxpayer."""
        system = ComputerSystem(
            vendor_name="Test Vendor",
            vendor_nif="B12345678",
            name="TestSys",
            id="TS",
            version="1.0",
            installation_number="INST-001",
            only_supports_verifactu=True,
            supports_multiple_taxpayers=False,
            has_multiple_taxpayers=False,
        )
        taxpayer = FiscalIdentifier(name="Company", nif="A98765432")
        return AeatClient(system, taxpayer)

    def test_incidencia_default_is_false(self, client_setup: AeatClient):
        """Test that incidencia defaults to False."""
        record = RegistrationRecord(
            invoice_id=InvoiceIdentifier(
                issuer_id="A98765432",
                invoice_number="F-001",
                issue_date=datetime(2025, 1, 1),
            ),
            issuer_name="Company",
            invoice_type=InvoiceType.SIMPLIFICADA,
            description="Test",
            recipients=[],
            breakdown=[
                BreakdownDetails(
                    tax_type=TaxType.IVA,
                    regime_type=RegimeType.C01,
                    operation_type=OperationType.SUBJECT,
                    tax_rate="21.00",
                    base_amount="100.00",
                    tax_amount="21.00",
                )
            ],
            total_tax_amount="21.00",
            total_amount="121.00",
            hashed_at=datetime.now(),
            hash="",
        )
        record.hash = record.calculate_hash()

        # Call without incidencia parameter - should default to False
        xml = client_setup._build_xml_request([record])

        assert "RemisionVoluntaria" not in xml
