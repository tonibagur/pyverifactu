"""Tests for QrGenerator."""

from datetime import datetime

from verifactu.models.records.invoice_identifier import InvoiceIdentifier
from verifactu.models.records.registration_record import RegistrationRecord
from verifactu.services.qr_generator import QrGenerator


class TestQrGenerator:
    """Tests for QR code URL generation."""

    def test_generates_links_from_raw_parameters(self) -> None:
        service = QrGenerator()
        assert (
            service.from_raw("A86018322", "FACT001", datetime(2025, 10, 1), "100.23")
            == "https://www2.agenciatributaria.gob.es/wlpl/TIKE-CONT/ValidarQR?nif=A86018322&numserie=FACT001&fecha=01-10-2025&importe=100.23"
        )

        service.set_online_mode(False)
        assert (
            service.from_raw("A86018322", "FACT002", datetime(2025, 10, 1), "100.23")
            == "https://www2.agenciatributaria.gob.es/wlpl/TIKE-CONT/ValidarQRNoVerifactu?nif=A86018322&numserie=FACT002&fecha=01-10-2025&importe=100.23"
        )

        service.set_production(False)
        assert (
            service.from_raw("A86018322", "FACT003", datetime(2025, 10, 1), "100.23")
            == "https://prewww2.aeat.es/wlpl/TIKE-CONT/ValidarQRNoVerifactu?nif=A86018322&numserie=FACT003&fecha=01-10-2025&importe=100.23"
        )

    def test_generates_links_from_invoice_identifier(self) -> None:
        service = QrGenerator()
        invoice_id = InvoiceIdentifier("A86018322", "FACT001", datetime(2025, 10, 1))
        assert (
            service.from_invoice_id(invoice_id, "100.23")
            == "https://www2.agenciatributaria.gob.es/wlpl/TIKE-CONT/ValidarQR?nif=A86018322&numserie=FACT001&fecha=01-10-2025&importe=100.23"
        )

    def test_generates_links_from_registration_record(self) -> None:
        service = QrGenerator()
        record = RegistrationRecord.model_construct(
            invoice_id=InvoiceIdentifier("A86018322", "FACT001", datetime(2025, 10, 1)),
            total_amount="100.23",
        )
        assert (
            service.from_registration_record(record)
            == "https://www2.agenciatributaria.gob.es/wlpl/TIKE-CONT/ValidarQR?nif=A86018322&numserie=FACT001&fecha=01-10-2025&importe=100.23"
        )

    def test_encodes_special_characters(self) -> None:
        service = QrGenerator()
        assert (
            service.from_raw("A86018322", "A/2025 01&B", datetime(2025, 10, 1), "100.23")
            == "https://www2.agenciatributaria.gob.es/wlpl/TIKE-CONT/ValidarQR?nif=A86018322&numserie=A%2F2025+01%26B&fecha=01-10-2025&importe=100.23"
        )

    def test_setters_return_instance_for_chaining(self) -> None:
        service = QrGenerator()
        assert service.set_production(False).set_online_mode(False) is service
