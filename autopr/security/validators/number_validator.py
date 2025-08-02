from ..validation_models import ValidationResult, ValidationSeverity


class NumberValidator:
    """Number validation functionality."""

    def _validate_number(self, key: str, value: int | float) -> ValidationResult:
        """Validate numeric input."""
        result = ValidationResult(is_valid=True)

        # Range validation
        if isinstance(value, int):
            if value < -(2**31) or value > 2**31 - 1:
                result.errors.append(f"Integer out of safe range for key '{key}': {value}")
                result.severity = ValidationSeverity.MEDIUM
                result.is_valid = False
                return result

        if isinstance(value, float):
            if abs(value) > 1e308:
                result.errors.append(f"Float out of safe range for key '{key}': {value}")
                result.severity = ValidationSeverity.MEDIUM
                result.is_valid = False
                return result

        # Wrap numeric value in a dictionary to satisfy type constraints
        result.sanitized_data = {"value": value}
        return result
