"""Service to generate QR code URLs"""

from datetime import datetime
from urllib.parse import urlencode

from ..models.records.invoice_identifier import InvoiceIdentifier
from ..models.records.registration_record import RegistrationRecord


class QrGenerator:
    """
    Service to generate QR code URLs

    By default uses the production environment operating in online mode (VERI*FACTU mode).
    """

    def __init__(self) -> None:
        """Class constructor"""
        self.is_production = True
        self.is_online_mode = True

    def set_production(self, production: bool) -> "QrGenerator":
        """
        Set production environment

        Args:
            production: True for production, False for testing

        Returns:
            This instance for chaining
        """
        self.is_production = production
        return self

    def set_online_mode(self, online_mode: bool) -> "QrGenerator":
        """
        Set online mode

        Args:
            online_mode: True for online mode (VERI*FACTU), False for offline mode (No VERI*FACTU)

        Returns:
            This instance for chaining
        """
        self.is_online_mode = online_mode
        return self

    def from_registration_record(self, record: RegistrationRecord) -> str:
        """
        Generate URL from registration record

        Args:
            record: Registration record

        Returns:
            QR code URL
        """
        return self.from_invoice_id(record.invoice_id, record.total_amount)

    def from_invoice_id(self, invoice_id: InvoiceIdentifier, amount: str) -> str:
        """
        Generate URL from invoice ID and amount

        Args:
            invoice_id: Invoice ID
            amount: Invoice amount

        Returns:
            QR code URL
        """
        return self.from_raw(
            invoice_id.issuer_id, invoice_id.invoice_number, invoice_id.issue_date, amount
        )

    def from_raw(
        self, issuer_id: str, invoice_number: str, issue_date: datetime, amount: str
    ) -> str:
        """
        Generate URL from raw parameters

        Args:
            issuer_id: Invoice issuer ID
            invoice_number: Invoice number
            issue_date: Invoice issue date
            amount: Invoice total amount

        Returns:
            QR code URL
        """
        url = (
            "https://www2.agenciatributaria.gob.es"
            if self.is_production
            else "https://prewww2.aeat.es"
        )
        url += "/wlpl/TIKE-CONT/"
        url += "ValidarQR" if self.is_online_mode else "ValidarQRNoVerifactu"
        url += "?" + urlencode(
            {
                "nif": issuer_id,
                "numserie": invoice_number,
                "fecha": issue_date.strftime("%d-%m-%Y"),
                "importe": amount,
            }
        )
        return url
