"""Tests for the XML generated for cancellation records.

The expected XML (tests/fixtures/cancellation-record.xml) is taken from the
Verifactu-PHP test suite.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from verifactu.models.computer_system import ComputerSystem
from verifactu.models.records.cancellation_record import CancellationRecord
from verifactu.models.records.fiscal_identifier import FiscalIdentifier
from verifactu.models.records.invoice_identifier import InvoiceIdentifier
from verifactu.services.aeat_client import AeatClient

FIXTURE = Path(__file__).parent.parent / "fixtures" / "cancellation-record.xml"


def flatten(element: ET.Element) -> list:
    """List (tag, text) pairs of an element tree in document order"""
    return [(e.tag, (e.text or "").strip()) for e in element.iter()]


class TestAeatClientCancellation:
    """Tests for cancellation record export."""

    @pytest.fixture
    def client(self) -> AeatClient:
        system = ComputerSystem(
            vendor_name="Perico de los Palotes, S.A.",
            vendor_nif="A00000000",
            name="Test SIF",
            id="TS",
            version="0.0.1",
            installation_number="01234",
            only_supports_verifactu=True,
            supports_multiple_taxpayers=False,
            has_multiple_taxpayers=False,
        )
        return AeatClient(
            system, FiscalIdentifier(name="Perico de los Palotes, S.A.", nif="A00000000")
        )

    @pytest.fixture
    def record(self) -> CancellationRecord:
        invoice_id = InvoiceIdentifier("A00000000", "12345679/G34", datetime(2024, 1, 1))
        record = CancellationRecord(
            invoice_id=invoice_id,
            previous_invoice_id=invoice_id,
            previous_hash="F7B94CFD8924EDFF273501B01EE5153E4CE8F259766F88CF6ACB8935802A2B97",
            previous_rejection="S",
            hashed_at=datetime(2024, 1, 1, 19, 20, 40, tzinfo=timezone(timedelta(hours=1))),
        )
        record.hash = record.calculate_hash()
        return record

    def test_builds_request_for_cancellation(
        self, client: AeatClient, record: CancellationRecord
    ) -> None:
        xml = client._build_xml_request([record])
        assert "RegistroAnulacion" in xml

    def test_exported_record_matches_reference_xml(
        self, client: AeatClient, record: CancellationRecord
    ) -> None:
        expected = ET.parse(FIXTURE).getroot()
        assert record.hash == expected.find(f"{{{AeatClient.NS_SUM1}}}Huella").text

        request = ET.fromstring(client._build_xml_request([record]))
        exported = request.find(f".//{{{AeatClient.NS_SUM1}}}RegistroAnulacion")

        assert exported is not None
        assert flatten(exported) == flatten(expected)

    def test_build_record_xml_for_cancellation(
        self, client: AeatClient, record: CancellationRecord
    ) -> None:
        xml = client.build_record_xml(record)
        assert "IDEmisorFacturaAnulada" in xml
        assert "NombreRazonEmisor" not in xml
        assert "TipoFactura" not in xml

    def test_exports_without_prior_record_flag(
        self, client: AeatClient, record: CancellationRecord
    ) -> None:
        record.without_prior_record = True
        request = ET.fromstring(client._build_xml_request([record]))
        exported = request.find(f".//{{{AeatClient.NS_SUM1}}}RegistroAnulacion")
        tags = [child.tag.split("}")[1] for child in exported]
        assert tags[:5] == [
            "IDVersion",
            "IDFactura",
            "SinRegistroPrevio",
            "RechazoPrevio",
            "Encadenamiento",
        ]
