"""Tests for BreakdownDetails model"""

import pytest
from pydantic import ValidationError

from verifactu.models.records import (
    BreakdownDetails,
    TaxType,
    RegimeType,
    OperationType,
)
from verifactu.exceptions import InvalidModelException


class TestBreakdownDetails:
    """Test BreakdownDetails validation and calculations"""

    def test_validates_tax_amount(self) -> None:
        """Test tax amount calculation validation"""

        # Create valid breakdown
        details = BreakdownDetails(
            tax_type=TaxType.IVA,
            regime_type=RegimeType.C01,
            operation_type=OperationType.SUBJECT,
            base_amount="11.22",
            tax_rate="21.00",
            tax_amount="2.36",
        )

        # Should pass validation
        details.validate()

        # Wrong tax amount should raise exception
        with pytest.raises(ValidationError) as exc_info:
            BreakdownDetails(
                tax_type=TaxType.IVA,
                regime_type=RegimeType.C01,
                operation_type=OperationType.SUBJECT,
                base_amount="11.22",
                tax_rate="21.00",
                tax_amount="99.99",
            )
        assert "Expected tax amount of 2.36, got 99.99" in str(exc_info.value)

        # Acceptable tax amount differences (±0.01)
        details_low = BreakdownDetails(
            tax_type=TaxType.IVA,
            regime_type=RegimeType.C01,
            operation_type=OperationType.SUBJECT,
            base_amount="11.22",
            tax_rate="21.00",
            tax_amount="2.35",
        )
        details_low.validate()

        details_high = BreakdownDetails(
            tax_type=TaxType.IVA,
            regime_type=RegimeType.C01,
            operation_type=OperationType.SUBJECT,
            base_amount="11.22",
            tax_rate="21.00",
            tax_amount="2.37",
        )
        details_high.validate()

    def test_tax_amount_tolerance_with_rounding_boundary(self) -> None:
        """Test that tax amounts within ±0.02 are accepted even at float rounding boundaries.

        When base_amount * tax_rate / 100 falls exactly on a .XX5 boundary
        (e.g., 12.50 * 21% = 2.625), the discrete tolerance approach can miss
        valid tax_amount values because float formatting skips over them.

        For example, 2.625 formatted with tolerances [0, ±0.01, ±0.02] generates
        the set {"2.60", "2.62", "2.64"} — missing "2.61" and "2.63" which are
        both within 0.02 of 2.625.
        """
        # base_amount=12.50, tax_rate=21.00 => exact tax = 2.625
        # tax_amount="2.61" has diff of 0.015 from 2.625, well within 0.02
        BreakdownDetails(
            tax_type=TaxType.IVA,
            regime_type=RegimeType.C01,
            operation_type=OperationType.SUBJECT,
            base_amount="12.50",
            tax_rate="21.00",
            tax_amount="2.61",
        )

        # tax_amount="2.64" has diff of 0.015 from 2.625, well within 0.02
        BreakdownDetails(
            tax_type=TaxType.IVA,
            regime_type=RegimeType.C01,
            operation_type=OperationType.SUBJECT,
            base_amount="12.50",
            tax_rate="21.00",
            tax_amount="2.64",
        )

        # Another common case: base_amount=1.50, tax_rate=21.00 => exact tax = 0.315
        # tax_amount="0.31" has diff of 0.005, well within 0.02
        BreakdownDetails(
            tax_type=TaxType.IVA,
            regime_type=RegimeType.C01,
            operation_type=OperationType.SUBJECT,
            base_amount="1.50",
            tax_rate="21.00",
            tax_amount="0.31",
        )

    def test_validates_operation_type(self) -> None:
        """Test operation type validation requirements"""

        # Subject operation without tax rate and amount should fail
        with pytest.raises(ValidationError) as exc_info:
            BreakdownDetails(
                tax_type=TaxType.IVA,
                regime_type=RegimeType.C01,
                operation_type=OperationType.SUBJECT,
                base_amount="100.00",
            )
        error_msg = str(exc_info.value)
        # Pydantic stops at first error, so check for at least one of the messages
        assert "Tax rate must be defined for subject operation types" in error_msg

        # Exempt operation without tax rate and amount should pass
        details = BreakdownDetails(
            tax_type=TaxType.IVA,
            regime_type=RegimeType.C01,
            operation_type=OperationType.EXEMPT_BY_OTHER,
            base_amount="100.00",
        )
        details.validate()
