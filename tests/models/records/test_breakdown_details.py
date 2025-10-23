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
