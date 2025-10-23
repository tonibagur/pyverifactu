"""Tests for CancellationRecord model"""

from datetime import datetime, timezone, timedelta
import pytest
from pydantic import ValidationError

from verifactu.models.records import (
    CancellationRecord,
    InvoiceIdentifier,
)
from verifactu.exceptions import InvalidModelException


class TestCancellationRecord:
    """Test CancellationRecord model validation and hash calculation"""

    def test_requires_previous_invoice(self) -> None:
        """Test that previous invoice is always required for cancellation records"""

        # Missing both previous invoice ID and hash should fail
        with pytest.raises(ValidationError) as exc_info:
            CancellationRecord(
                invoice_id=InvoiceIdentifier(
                    issuer_id="89890001K",
                    invoice_number="12345679/G34",
                    issue_date=datetime(2024, 1, 1),
                ),
                previous_invoice_id=None,  # Not allowed
                previous_hash=None,  # Not allowed
                hashed_at=datetime(2024, 1, 1, 19, 20, 40, tzinfo=timezone(timedelta(hours=1))),
            )
        error_msg = str(exc_info.value)
        # Pydantic stops at first error, so check for at least one of the messages
        assert "Previous invoice ID is required" in error_msg or "Previous hash is required" in error_msg

        # Missing only previous hash should fail
        with pytest.raises(ValidationError) as exc_info:
            CancellationRecord(
                invoice_id=InvoiceIdentifier(
                    issuer_id="89890001K",
                    invoice_number="12345679/G34",
                    issue_date=datetime(2024, 1, 1),
                ),
                previous_invoice_id=InvoiceIdentifier(
                    issuer_id="89890001K",
                    invoice_number="12345679/G34",
                    issue_date=datetime(2024, 1, 1),
                ),
                previous_hash=None,  # Not allowed
                hashed_at=datetime(2024, 1, 1, 19, 20, 40, tzinfo=timezone(timedelta(hours=1))),
            )
        assert "Previous hash is required" in str(exc_info.value)

    def test_calculates_hash_for_other_records(self) -> None:
        """Test hash calculation for cancellation records"""
        record = CancellationRecord(
            invoice_id=InvoiceIdentifier(
                issuer_id="89890001K",
                invoice_number="12345679/G34",
                issue_date=datetime(2024, 1, 1),
            ),
            previous_invoice_id=InvoiceIdentifier(
                issuer_id="89890001K",
                invoice_number="12345679/G34",
                issue_date=datetime(2024, 1, 1),
            ),
            previous_hash="F7B94CFD8924EDFF273501B01EE5153E4CE8F259766F88CF6ACB8935802A2B97",
            hashed_at=datetime(2024, 1, 1, 19, 20, 40, tzinfo=timezone(timedelta(hours=1))),
            hash="",  # Will be calculated
        )

        record.hash = record.calculate_hash()
        assert record.hash == "177547C0D57AC74748561D054A9CEC14B4C4EA23D1BEFD6F2E69E3A388F90C68"
        record.validate()

    def test_correction_fields_do_not_affect_hash(self) -> None:
        """Test that correction fields don't affect hash calculation"""
        # Record without correction fields
        record1 = CancellationRecord(
            invoice_id=InvoiceIdentifier(
                issuer_id="89890001K",
                invoice_number="TEST-HASH",
                issue_date=datetime(2024, 1, 1),
            ),
            previous_invoice_id=InvoiceIdentifier(
                issuer_id="89890001K",
                invoice_number="PREV-001",
                issue_date=datetime(2024, 1, 1),
            ),
            previous_hash="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            hashed_at=datetime(2024, 1, 1, 10, 20, 30, tzinfo=timezone(timedelta(hours=1))),
            hash="",
        )
        hash1 = record1.calculate_hash()

        # Record with correction fields
        record2 = CancellationRecord(
            invoice_id=InvoiceIdentifier(
                issuer_id="89890001K",
                invoice_number="TEST-HASH",
                issue_date=datetime(2024, 1, 1),
            ),
            previous_invoice_id=InvoiceIdentifier(
                issuer_id="89890001K",
                invoice_number="PREV-001",
                issue_date=datetime(2024, 1, 1),
            ),
            previous_hash="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            hashed_at=datetime(2024, 1, 1, 10, 20, 30, tzinfo=timezone(timedelta(hours=1))),
            previous_rejection="N",
            correction="N",
            external_reference="CANCEL-REF-001",
            hash="",
        )
        hash2 = record2.calculate_hash()

        # Hashes should be identical
        assert hash1 == hash2, "Correction fields should not affect hash calculation"
