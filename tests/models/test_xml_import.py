"""Tests for importing records and models from XML.

The XML fixtures in tests/fixtures are taken from the Verifactu-PHP test suite.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from verifactu import (
    AeatClient,
    BreakdownDetails,
    CancellationRecord,
    ComputerSystem,
    FiscalIdentifier,
    ForeignFiscalIdentifier,
    ForeignIdType,
    ImportException,
    InvalidModelException,
    InvoiceIdentifier,
    InvoiceType,
    OperationType,
    Record,
    RegimeType,
    RegistrationRecord,
    TaxType,
)
from verifactu.models.xml_utils import NS_SUM1

FIXTURES = Path(__file__).parent.parent / "fixtures"


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class TestRecordFromXml:
    """Tests for Record.from_xml."""

    def test_imports_registration_record(self) -> None:
        record = Record.from_xml(read_fixture("registration-record-f1.xml"))

        assert isinstance(record, RegistrationRecord)
        assert record.invoice_id == InvoiceIdentifier(
            "00000000B", "PRUEBA-0002", datetime(2025, 6, 2)
        )
        assert record.issuer_name == "El Nombre del Emisor, S.L."
        assert record.invoice_type == InvoiceType.FACTURA
        assert record.description == "Factura de prueba"
        assert record.is_correction is False
        assert record.correction == "N"
        assert record.total_tax_amount == "26.00"
        assert record.total_amount == "176.00"

        assert record.recipients[0] == FiscalIdentifier("El Destinatario, S.L.", "11111111B")
        foreign = record.recipients[1]
        assert isinstance(foreign, ForeignFiscalIdentifier)
        assert (foreign.name, foreign.country, foreign.type, foreign.value) == (
            "Louise Dubois",
            "FR",
            ForeignIdType.VAT,
            "FR52422961982",
        )

        assert len(record.breakdown) == 2
        assert record.breakdown[1].tax_rate == "10.00"
        assert record.breakdown[1].base_amount == "50.00"
        assert record.breakdown[1].tax_amount == "5.00"

        assert record.previous_invoice_id == InvoiceIdentifier(
            "00000000B", "PRUEBA-001", datetime(2025, 6, 1)
        )
        assert record.previous_hash == "A" * 64
        assert record.hashed_at == datetime(
            2025, 6, 2, 11, 22, 33, tzinfo=timezone(timedelta(hours=2))
        )
        assert record.hash == "8B042C064EE8260DE86766B4C4878DD1347377D00C7D7C97043E126B1215F2A6"
        assert record.hash == record.calculate_hash()
        record.validate()

    def test_imports_simplified_invoice(self) -> None:
        record = Record.from_xml(read_fixture("registration-record-f2.xml"))

        assert isinstance(record, RegistrationRecord)
        assert record.invoice_type == InvoiceType.SIMPLIFICADA
        assert record.recipients == []
        assert record.hash == record.calculate_hash()

    def test_imports_cancellation_record(self) -> None:
        record = Record.from_xml(read_fixture("cancellation-record.xml"))

        assert isinstance(record, CancellationRecord)
        assert record.invoice_id == InvoiceIdentifier(
            "A00000000", "12345679/G34", datetime(2024, 1, 1)
        )
        assert record.without_prior_record is False
        assert record.previous_rejection == "S"
        assert record.hash == "5DCAFD630E24AA03BCE2D3E6F595BAE802555F4604AF830F0340F3338B4935F6"
        assert record.hash == record.calculate_hash()

    def test_accepts_parsed_element(self) -> None:
        element = ET.fromstring(read_fixture("registration-record-f1.xml"))
        assert isinstance(Record.from_xml(element), RegistrationRecord)

    def test_subclass_only_accepts_its_own_node(self) -> None:
        assert isinstance(
            RegistrationRecord.from_xml(read_fixture("registration-record-f1.xml")),
            RegistrationRecord,
        )
        with pytest.raises(ImportException, match="Unexpected node type"):
            RegistrationRecord.from_xml(read_fixture("cancellation-record.xml"))

    def test_round_trip_with_aeat_client(self) -> None:
        system = ComputerSystem.from_xml(read_fixture("computer-system.xml"))
        taxpayer = FiscalIdentifier(name="Perico de los Palotes, S.A.", nif="A00000000")
        record = RegistrationRecord(
            invoice_id=InvoiceIdentifier("A00000000", "FACT-2025-001", datetime(2025, 1, 15)),
            issuer_name="Perico de los Palotes, S.A.",
            invoice_type=InvoiceType.FACTURA,
            description="Round trip",
            recipients=[FiscalIdentifier(name="Customer SL", nif="B11111111")],
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
            hashed_at=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone(timedelta(hours=1))),
        )
        record.hash = record.calculate_hash()

        request = ET.fromstring(AeatClient(system, taxpayer)._build_xml_request([record]))
        element = request.find(f".//{{{NS_SUM1}}}RegistroAlta")
        imported = Record.from_xml(element)

        assert imported.invoice_id == record.invoice_id
        assert imported.recipients == record.recipients
        assert imported.breakdown == record.breakdown
        assert imported.hashed_at == record.hashed_at
        assert imported.hash == record.hash

    def test_rejects_invalid_xml(self) -> None:
        with pytest.raises(ImportException, match="Invalid XML"):
            Record.from_xml("<not-xml")

    def test_rejects_unknown_namespace(self) -> None:
        with pytest.raises(ImportException, match='namespace must be "sum1"'):
            Record.from_xml("<RegistroAlta />")

    def test_rejects_unexpected_node(self) -> None:
        with pytest.raises(ImportException, match="Unexpected node type"):
            Record.from_xml(f'<sum1:Otro xmlns:sum1="{NS_SUM1}" />')

    def test_rejects_missing_required_element(self) -> None:
        xml = read_fixture("registration-record-f1.xml").replace(
            "<sum1:ImporteTotal>176.00</sum1:ImporteTotal>", ""
        )
        with pytest.raises(ImportException, match="Missing <sum1:ImporteTotal />"):
            Record.from_xml(xml)

    def test_rejects_invalid_enum_value(self) -> None:
        xml = read_fixture("registration-record-f1.xml").replace(
            "<sum1:TipoFactura>F1</sum1:TipoFactura>", "<sum1:TipoFactura>XX</sum1:TipoFactura>"
        )
        with pytest.raises(ImportException, match="Invalid value for <sum1:TipoFactura />"):
            Record.from_xml(xml)

    def test_rejects_tampered_record(self) -> None:
        xml = read_fixture("registration-record-f1.xml").replace(
            "<sum1:ImporteTotal>176.00</sum1:ImporteTotal>",
            "<sum1:ImporteTotal>176.01</sum1:ImporteTotal>",
        )
        with pytest.raises(InvalidModelException):
            Record.from_xml(xml)


class TestComputerSystemFromXml:
    """Tests for ComputerSystem.from_xml."""

    def test_imports_computer_system(self) -> None:
        system = ComputerSystem.from_xml(read_fixture("computer-system.xml"))

        assert system.vendor_name == "Perico de los Palotes, S.A."
        assert system.vendor_nif == "A00000000"
        assert system.name == "Test SIF"
        assert system.id == "TS"
        assert system.version == "0.0.1"
        assert system.installation_number == "01234"
        assert system.only_supports_verifactu is True
        assert system.supports_multiple_taxpayers is False
        assert system.has_multiple_taxpayers is False


class TestBreakdownDetailsFromXml:
    """Tests for BreakdownDetails.from_xml."""

    def test_imports_exempt_operation(self) -> None:
        details = BreakdownDetails.from_xml(
            f'<sum1:DetalleDesglose xmlns:sum1="{NS_SUM1}">'
            "<sum1:Impuesto>01</sum1:Impuesto>"
            "<sum1:ClaveRegimen>01</sum1:ClaveRegimen>"
            "<sum1:OperacionExenta>E1</sum1:OperacionExenta>"
            "<sum1:BaseImponibleOimporteNoSujeto>100.00</sum1:BaseImponibleOimporteNoSujeto>"
            "</sum1:DetalleDesglose>"
        )

        assert details.operation_type == OperationType("E1")
        assert details.tax_rate is None
        assert details.tax_amount is None
