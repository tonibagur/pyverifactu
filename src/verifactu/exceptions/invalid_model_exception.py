"""Exception thrown when a model class does not pass validation"""

from typing import Any, List


class InvalidModelException(RuntimeError):
    """Exception thrown when a model class does not pass validation"""

    def __init__(self, errors: List[Any]) -> None:
        """
        Class constructor

        Args:
            errors: Validation errors (Pydantic ValidationError or list of errors)
        """
        self.errors = errors
        super().__init__(f"Invalid instance of model class:\n{self._get_human_representation()}")

    def _get_human_representation(self) -> str:
        """
        Get human representation of validation errors

        Returns:
            Human-readable validation errors
        """
        result = []
        if hasattr(self.errors, "errors"):
            # Pydantic ValidationError
            for error in self.errors.errors():
                loc = " -> ".join(str(l) for l in error["loc"])
                msg = error["msg"]
                result.append(f"- {loc}: {msg}")
        else:
            # List of errors
            for error in self.errors:
                result.append(f"- {error}")
        return "\n".join(result)
