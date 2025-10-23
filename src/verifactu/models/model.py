"""Base model class with validation"""

from __future__ import annotations

from abc import ABC
from pydantic import BaseModel, ConfigDict, ValidationError
from verifactu.exceptions import InvalidModelException


class Model(BaseModel, ABC):
    """
    Abstract base class for all models

    Provides validation functionality using Pydantic.
    All model classes should extend this class.
    """

    model_config = ConfigDict(
        # Allow arbitrary types for datetime objects
        arbitrary_types_allowed=True,
        # Validate on assignment
        validate_assignment=True,
        # Use enum values
        use_enum_values=False,
        # Strict mode for better type checking
        strict=False,
    )

    def validate(self) -> None:
        """
        Validate this instance

        Raises:
            InvalidModelException: If failed to pass validation
        """
        try:
            # Re-validate the model
            self.model_validate(self.model_dump())
        except ValidationError as e:
            raise InvalidModelException(e) from e
