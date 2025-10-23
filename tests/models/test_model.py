"""Tests for base Model class"""

import pytest
from pydantic import Field, ValidationError, field_validator

from verifactu.models.model import Model
from verifactu.exceptions import InvalidModelException


class SampleModel(Model):
    """Sample model for testing validation"""

    name: str = Field(..., min_length=4, max_length=4)
    quantity: int = Field(..., gt=0)

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str) -> str:
        """Validate name is not blank"""
        if not v or not v.strip():
            raise ValueError("name cannot be blank")
        return v

    @field_validator("quantity")
    @classmethod
    def validate_quantity_not_blank(cls, v: int) -> int:
        """Validate quantity is positive"""
        if v <= 0:
            raise ValueError("quantity must be positive")
        return v


class TestModel:
    """Test base Model validation functionality"""

    def test_not_throws_on_valid_model(self) -> None:
        """Test that valid models pass validation"""
        model = SampleModel(name="abcd", quantity=2)
        # Should not raise any exception
        model.validate()

    def test_throws_on_invalid_model(self) -> None:
        """Test that invalid data throws ValidationError during construction"""
        with pytest.raises(ValidationError):
            # This will fail validation due to name length and quantity = 0
            SampleModel(name="This is not a valid name", quantity=0)
