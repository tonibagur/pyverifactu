"""Tests for InvoiceIdentifier model"""

from datetime import datetime, timezone, timedelta

from verifactu.models.records import InvoiceIdentifier


class TestInvoiceIdentifier:
    """Test InvoiceIdentifier comparison logic"""

    def test_compares_instances(self) -> None:
        """Test equality comparison of InvoiceIdentifier objects"""

        # Same instance
        a = InvoiceIdentifier(
            issuer_id="A00000000",  # Must be exactly 9 characters
            invoice_number="InvoiceNumber123",
            issue_date=datetime(2025, 10, 17, 12, 34, 56, tzinfo=timezone(timedelta(hours=2))),
        )
        assert a.equals(a)

        # Same exact values
        a = InvoiceIdentifier(
            issuer_id="A00000000",
            invoice_number="InvoiceNumber123",
            issue_date=datetime(2025, 10, 17, 12, 34, 56, tzinfo=timezone(timedelta(hours=2))),
        )
        b = InvoiceIdentifier(
            issuer_id="A00000000",
            invoice_number="InvoiceNumber123",
            issue_date=datetime(2025, 10, 17, 12, 34, 56, tzinfo=timezone(timedelta(hours=2))),
        )
        assert a.equals(b)
        assert b.equals(a)

        # Different time (but same date)
        a = InvoiceIdentifier(
            issuer_id="A00000000",
            invoice_number="InvoiceNumber123",
            issue_date=datetime(2025, 10, 17, 12, 34, 56, tzinfo=timezone(timedelta(hours=2))),
        )
        b = InvoiceIdentifier(
            issuer_id="A00000000",
            invoice_number="InvoiceNumber123",
            issue_date=datetime(2025, 10, 17, 20, 30, 40, tzinfo=timezone(timedelta(hours=2))),
        )
        assert a.equals(b)
        assert b.equals(a)

        # Different timezone, still same date
        a = InvoiceIdentifier(
            issuer_id="A00000000",
            invoice_number="InvoiceNumber123",
            issue_date=datetime(2025, 10, 17, 0, 0, 0, tzinfo=timezone(timedelta(hours=2))),
        )
        b = InvoiceIdentifier(
            issuer_id="A00000000",
            invoice_number="InvoiceNumber123",
            issue_date=datetime(2025, 10, 17, 2, 0, 0, tzinfo=timezone.utc),
        )
        assert a.equals(b)
        assert b.equals(a)

        # Different dates
        a = InvoiceIdentifier(
            issuer_id="A00000000",
            invoice_number="InvoiceNumber123",
            issue_date=datetime(2025, 10, 11, 0, 0, 0, tzinfo=timezone(timedelta(hours=2))),
        )
        b = InvoiceIdentifier(
            issuer_id="A00000000",
            invoice_number="InvoiceNumber123",
            issue_date=datetime(2025, 10, 17, 0, 0, 0, tzinfo=timezone(timedelta(hours=2))),
        )
        assert not a.equals(b)
        assert not b.equals(a)
