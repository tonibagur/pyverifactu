"""Tests for QueryFilter and QueryPeriod models"""

import pytest
from datetime import date

from verifactu.models.queries.query_period import QueryPeriod
from verifactu.models.queries.query_filter import QueryFilter


class TestQueryPeriod:
    """Tests for QueryPeriod model"""

    def test_valid_period(self):
        """Test creating a valid period"""
        period = QueryPeriod(year=2025, month=11)
        assert period.year == 2025
        assert period.month == 11
        assert period.ejercicio == "2025"
        assert period.periodo == "11"

    def test_month_format_with_leading_zero(self):
        """Test that month is formatted with leading zero"""
        period = QueryPeriod(year=2025, month=1)
        assert period.periodo == "01"

    def test_invalid_year_too_low(self):
        """Test that year below 2000 raises error"""
        with pytest.raises(ValueError, match="Invalid year"):
            QueryPeriod(year=1999, month=1)

    def test_invalid_year_too_high(self):
        """Test that year above 9999 raises error"""
        with pytest.raises(ValueError, match="Invalid year"):
            QueryPeriod(year=10000, month=1)

    def test_invalid_month_too_low(self):
        """Test that month below 1 raises error"""
        with pytest.raises(ValueError, match="Invalid month"):
            QueryPeriod(year=2025, month=0)

    def test_invalid_month_too_high(self):
        """Test that month above 12 raises error"""
        with pytest.raises(ValueError, match="Invalid month"):
            QueryPeriod(year=2025, month=13)


class TestQueryFilter:
    """Tests for QueryFilter model"""

    def test_minimal_filter(self):
        """Test creating a filter with only required fields"""
        period = QueryPeriod(year=2025, month=11)
        filter = QueryFilter(period=period)

        assert filter.period == period
        assert filter.invoice_number is None
        assert filter.counterparty_nif is None
        assert filter.date_from is None
        assert filter.date_to is None
        assert filter.pagination_key is None
        assert filter.show_issuer_name is True
        assert filter.show_computer_system is False

    def test_full_filter(self):
        """Test creating a filter with all fields"""
        period = QueryPeriod(year=2025, month=11)
        filter = QueryFilter(
            period=period,
            invoice_number="FACT-001",
            counterparty_nif="12345678A",
            date_from=date(2025, 11, 1),
            date_to=date(2025, 11, 30),
            external_reference="REF-001",
            pagination_key="abc123",
            show_issuer_name=False,
            show_computer_system=True,
        )

        assert filter.invoice_number == "FACT-001"
        assert filter.counterparty_nif == "12345678A"
        assert filter.date_from == date(2025, 11, 1)
        assert filter.date_to == date(2025, 11, 30)
        assert filter.external_reference == "REF-001"
        assert filter.pagination_key == "abc123"
        assert filter.show_issuer_name is False
        assert filter.show_computer_system is True

    def test_invalid_date_range(self):
        """Test that date_from after date_to raises error"""
        period = QueryPeriod(year=2025, month=11)
        with pytest.raises(ValueError, match="date_from cannot be after date_to"):
            QueryFilter(
                period=period,
                date_from=date(2025, 11, 30),
                date_to=date(2025, 11, 1),
            )
