"""Tests for RegistrationRecord model"""

from datetime import datetime, timezone, timedelta
import pytest
from pydantic import ValidationError

from verifactu.models.records import (
    RegistrationRecord,
    InvoiceIdentifier,
    FiscalIdentifier,
    ForeignFiscalIdentifier,
    BreakdownDetails,
    InvoiceType,
    TaxType,
    RegimeType,
    OperationType,
    CorrectiveType,
    ForeignIdType,
)
from verifactu.exceptions import InvalidModelException


class TestRegistrationRecord:
    """Test RegistrationRecord model validation and hash calculation"""

    def test_calculates_hash_for_first_record(self) -> None:
        """Test hash calculation for first invoice (no previous chain)"""
        record = RegistrationRecord(
            invoice_id=InvoiceIdentifier(
                issuer_id="A00000000",
                invoice_number="PRUEBA-0001",
                issue_date=datetime(2025, 6, 1),
            ),
            issuer_name="Perico de los Palotes, S.A.",
            invoice_type=InvoiceType.SIMPLIFICADA,
            description="Factura simplificada de prueba",
            breakdown=[
                BreakdownDetails(
                    tax_type=TaxType.IVA,
                    regime_type=RegimeType.C01,
                    operation_type=OperationType.SUBJECT,
                    base_amount="10.00",
                    tax_rate="21.00",
                    tax_amount="2.10",
                )
            ],
            total_tax_amount="2.10",
            total_amount="12.10",
            previous_invoice_id=None,
            previous_hash=None,
            hashed_at=datetime(2025, 6, 1, 10, 20, 30, tzinfo=timezone(timedelta(hours=2))),
            hash="",  # Will be calculated
        )

        record.hash = record.calculate_hash()
        assert record.hash == "F223F0A84F7D0C701C13C97CF10A1628FF9E46A003DDAEF3A804FBD799D82070"
        record.validate()

    def test_calculates_hash_for_other_records(self) -> None:
        """Test hash calculation for subsequent invoices (with chain)"""
        record = RegistrationRecord(
            invoice_id=InvoiceIdentifier(
                issuer_id="A00000000",
                invoice_number="PRUEBA-0002",
                issue_date=datetime(2025, 6, 2),
            ),
            issuer_name="Perico de los Palotes, S.A.",
            invoice_type=InvoiceType.SIMPLIFICADA,
            description="Factura simplificada de prueba",
            breakdown=[
                BreakdownDetails(
                    tax_type=TaxType.IVA,
                    regime_type=RegimeType.C01,
                    operation_type=OperationType.SUBJECT,
                    base_amount="100.00",
                    tax_rate="21.00",
                    tax_amount="21.00",
                )
            ],
            total_tax_amount="21.00",
            total_amount="121.00",
            previous_invoice_id=InvoiceIdentifier(
                issuer_id="A00000000",
                invoice_number="PRUEBA-001",
                issue_date=datetime(2025, 6, 1),
            ),
            previous_hash="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            hashed_at=datetime(2025, 6, 2, 20, 30, 40, tzinfo=timezone(timedelta(hours=2))),
            hash="",  # Will be calculated
        )

        record.hash = record.calculate_hash()
        assert record.hash == "4566062C5A5D7DA4E0E876C0994071CD807962629F8D3C1F33B91EDAA65B2BA1"
        record.validate()

    def test_validates_total_amounts(self) -> None:
        """Test total amount calculations with rounding tolerance"""
        record = RegistrationRecord(
            invoice_id=InvoiceIdentifier(
                issuer_id="A00000000",
                invoice_number="TEST",
                issue_date=datetime(2025, 6, 1),
            ),
            issuer_name="Perico de los Palotes, S.A.",
            invoice_type=InvoiceType.SIMPLIFICADA,
            description="Factura simplificada de prueba",
            breakdown=[
                BreakdownDetails(
                    tax_type=TaxType.IVA,
                    regime_type=RegimeType.C01,
                    operation_type=OperationType.SUBJECT,
                    base_amount="12.34",
                    tax_rate="21.00",
                    tax_amount="2.59",
                ),
                BreakdownDetails(
                    tax_type=TaxType.IVA,
                    regime_type=RegimeType.C01,
                    operation_type=OperationType.SUBJECT,
                    base_amount="543.21",
                    tax_rate="10.00",
                    tax_amount="54.31",  # off by 0.01
                ),
            ],
            total_tax_amount="56.90",
            total_amount="612.45",
            previous_invoice_id=None,
            previous_hash=None,
            hashed_at=datetime(2025, 6, 1, 20, 30, 40, tzinfo=timezone(timedelta(hours=2))),
            hash="",  # Will be calculated
        )

        # Should pass validation
        record.hash = record.calculate_hash()
        record.validate()

        # Invalid total tax amount
        with pytest.raises(ValidationError) as exc_info:
            invalid_record = RegistrationRecord(
                invoice_id=InvoiceIdentifier(
                    issuer_id="A00000000",
                    invoice_number="TEST",
                    issue_date=datetime(2025, 6, 1),
                ),
                issuer_name="Perico de los Palotes, S.A.",
                invoice_type=InvoiceType.SIMPLIFICADA,
                description="Factura simplificada de prueba",
                breakdown=record.breakdown,
                total_tax_amount="56.91",  # Wrong value
                total_amount="612.45",
                previous_invoice_id=None,
                previous_hash=None,
                hashed_at=datetime(2025, 6, 1, 20, 30, 40, tzinfo=timezone(timedelta(hours=2))),
                hash="",  # Dummy hash to pass format validation
            )
        assert "Expected total tax amount of 56.90, got 56.91" in str(exc_info.value)

        # Total amount with minor difference (should pass)
        record_minor_diff = RegistrationRecord(
            invoice_id=InvoiceIdentifier(
                issuer_id="A00000000",
                invoice_number="TEST",
                issue_date=datetime(2025, 6, 1),
            ),
            issuer_name="Perico de los Palotes, S.A.",
            invoice_type=InvoiceType.SIMPLIFICADA,
            description="Factura simplificada de prueba",
            breakdown=record.breakdown,
            total_tax_amount="56.90",
            total_amount="612.44",  # Off by 0.01 - should pass
            previous_invoice_id=None,
            previous_hash=None,
            hashed_at=datetime(2025, 6, 1, 20, 30, 40, tzinfo=timezone(timedelta(hours=2))),
            hash="",
        )
        record_minor_diff.hash = record_minor_diff.calculate_hash()
        record_minor_diff.validate()

        # Total amount with major difference (should fail)
        with pytest.raises(ValidationError) as exc_info:
            invalid_record2 = RegistrationRecord(
                invoice_id=InvoiceIdentifier(
                    issuer_id="A00000000",
                    invoice_number="TEST",
                    issue_date=datetime(2025, 6, 1),
                ),
                issuer_name="Perico de los Palotes, S.A.",
                invoice_type=InvoiceType.SIMPLIFICADA,
                description="Factura simplificada de prueba",
                breakdown=record.breakdown,
                total_tax_amount="56.90",
                total_amount="1.23",  # Way off
                previous_invoice_id=None,
                previous_hash=None,
                hashed_at=datetime(2025, 6, 1, 20, 30, 40, tzinfo=timezone(timedelta(hours=2))),
                hash="",
            )
        assert "Expected total amount of 612.45, got 1.23" in str(exc_info.value)

    def test_validates_recipients(self) -> None:
        """Test recipient requirement validation based on invoice type"""
        # Full invoice without recipients should fail
        with pytest.raises(ValidationError) as exc_info:
            RegistrationRecord(
                invoice_id=InvoiceIdentifier(
                    issuer_id="A00000000",
                    invoice_number="TEST",
                    issue_date=datetime(2025, 6, 1),
                ),
                issuer_name="Perico de los Palotes, S.A.",
                invoice_type=InvoiceType.FACTURA,  # Full invoice requires recipients
                description="Factura simplificada de prueba",
                breakdown=[
                    BreakdownDetails(
                        tax_type=TaxType.IVA,
                        regime_type=RegimeType.C01,
                        operation_type=OperationType.SUBJECT,
                        base_amount="10.00",
                        tax_rate="21.00",
                        tax_amount="2.10",
                    )
                ],
                total_tax_amount="2.10",
                total_amount="12.10",
                recipients=[],  # Missing recipients
                previous_invoice_id=None,
                previous_hash=None,
                hashed_at=datetime(2025, 6, 1, 20, 30, 40, tzinfo=timezone(timedelta(hours=2))),
                hash="",
            )
        assert "This type of invoice requires at least one recipient" in str(exc_info.value)

        # Should pass with Spanish identifier
        record = RegistrationRecord(
            invoice_id=InvoiceIdentifier(
                issuer_id="A00000000",
                invoice_number="TEST",
                issue_date=datetime(2025, 6, 1),
            ),
            issuer_name="Perico de los Palotes, S.A.",
            invoice_type=InvoiceType.FACTURA,
            description="Factura simplificada de prueba",
            breakdown=[
                BreakdownDetails(
                    tax_type=TaxType.IVA,
                    regime_type=RegimeType.C01,
                    operation_type=OperationType.SUBJECT,
                    base_amount="10.00",
                    tax_rate="21.00",
                    tax_amount="2.10",
                )
            ],
            total_tax_amount="2.10",
            total_amount="12.10",
            recipients=[FiscalIdentifier(name="Antonio García Pérez", nif="00000000A")],
            previous_invoice_id=None,
            previous_hash=None,
            hashed_at=datetime(2025, 6, 1, 20, 30, 40, tzinfo=timezone(timedelta(hours=2))),
            hash="",
        )
        record.hash = record.calculate_hash()
        record.validate()

        # Should pass with foreign identifier
        record_foreign = RegistrationRecord(
            invoice_id=InvoiceIdentifier(
                issuer_id="A00000000",
                invoice_number="TEST2",
                issue_date=datetime(2025, 6, 1),
            ),
            issuer_name="Perico de los Palotes, S.A.",
            invoice_type=InvoiceType.FACTURA,
            description="Factura simplificada de prueba",
            breakdown=[
                BreakdownDetails(
                    tax_type=TaxType.IVA,
                    regime_type=RegimeType.C01,
                    operation_type=OperationType.SUBJECT,
                    base_amount="10.00",
                    tax_rate="21.00",
                    tax_amount="2.10",
                )
            ],
            total_tax_amount="2.10",
            total_amount="12.10",
            recipients=[
                FiscalIdentifier(name="Antonio García Pérez", nif="00000000A"),
                ForeignFiscalIdentifier(
                    name="Another Company",
                    country="PT",
                    type=ForeignIdType.VAT,
                    value="PT999999999",
                ),
            ],
            previous_invoice_id=None,
            previous_hash=None,
            hashed_at=datetime(2025, 6, 1, 20, 30, 40, tzinfo=timezone(timedelta(hours=2))),
            hash="",
        )
        record_foreign.hash = record_foreign.calculate_hash()
        record_foreign.validate()

    def test_validates_corrective_details(self) -> None:
        """Test corrective invoice type validation"""
        # Corrective invoice without corrective type should fail
        with pytest.raises(ValidationError) as exc_info:
            RegistrationRecord(
                invoice_id=InvoiceIdentifier(
                    issuer_id="A00000000",
                    invoice_number="RECT-0001",
                    issue_date=datetime(2025, 6, 1),
                ),
                issuer_name="Perico de los Palotes, S.A.",
                invoice_type=InvoiceType.R1,  # Corrective invoice
                description="Factura rectificativa de prueba",
                recipients=[FiscalIdentifier(name="Antonio García Pérez", nif="00000000A")],
                breakdown=[
                    BreakdownDetails(
                        tax_type=TaxType.IVA,
                        regime_type=RegimeType.C01,
                        operation_type=OperationType.SUBJECT,
                        base_amount="10.00",
                        tax_rate="21.00",
                        tax_amount="2.10",
                    )
                ],
                total_tax_amount="2.10",
                total_amount="12.10",
                corrective_type=None,  # Missing corrective type
                previous_invoice_id=None,
                previous_hash=None,
                hashed_at=datetime(2025, 6, 1, 20, 30, 40, tzinfo=timezone(timedelta(hours=2))),
                hash="",
            )
        assert "Missing type for corrective invoice" in str(exc_info.value)

        # Corrective invoice by substitution without amounts should fail
        with pytest.raises(ValidationError) as exc_info:
            RegistrationRecord(
                invoice_id=InvoiceIdentifier(
                    issuer_id="A00000000",
                    invoice_number="RECT-0001",
                    issue_date=datetime(2025, 6, 1),
                ),
                issuer_name="Perico de los Palotes, S.A.",
                invoice_type=InvoiceType.R1,
                description="Factura rectificativa de prueba",
                recipients=[FiscalIdentifier(name="Antonio García Pérez", nif="00000000A")],
                breakdown=[
                    BreakdownDetails(
                        tax_type=TaxType.IVA,
                        regime_type=RegimeType.C01,
                        operation_type=OperationType.SUBJECT,
                        base_amount="10.00",
                        tax_rate="21.00",
                        tax_amount="2.10",
                    )
                ],
                total_tax_amount="2.10",
                total_amount="12.10",
                corrective_type=CorrectiveType.SUBSTITUTION,
                corrected_base_amount=None,  # Missing
                corrected_tax_amount=None,  # Missing
                previous_invoice_id=None,
                previous_hash=None,
                hashed_at=datetime(2025, 6, 1, 20, 30, 40, tzinfo=timezone(timedelta(hours=2))),
                hash="",
            )
        assert "Missing corrected base amount for corrective invoice by substitution" in str(
            exc_info.value
        )

        # Corrective invoice with proper details should pass
        record = RegistrationRecord(
            invoice_id=InvoiceIdentifier(
                issuer_id="A00000000",
                invoice_number="RECT-0001",
                issue_date=datetime(2025, 6, 1),
            ),
            issuer_name="Perico de los Palotes, S.A.",
            invoice_type=InvoiceType.R1,
            description="Factura rectificativa de prueba",
            recipients=[FiscalIdentifier(name="Antonio García Pérez", nif="00000000A")],
            breakdown=[
                BreakdownDetails(
                    tax_type=TaxType.IVA,
                    regime_type=RegimeType.C01,
                    operation_type=OperationType.SUBJECT,
                    base_amount="10.00",
                    tax_rate="21.00",
                    tax_amount="2.10",
                )
            ],
            total_tax_amount="2.10",
            total_amount="12.10",
            corrective_type=CorrectiveType.SUBSTITUTION,
            corrected_base_amount="8.00",
            corrected_tax_amount="1.68",
            previous_invoice_id=None,
            previous_hash=None,
            hashed_at=datetime(2025, 6, 1, 20, 30, 40, tzinfo=timezone(timedelta(hours=2))),
            hash="",
        )
        record.hash = record.calculate_hash()
        record.validate()
