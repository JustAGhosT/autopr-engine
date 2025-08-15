from autopr.security.validation_models import ValidationResult, ValidationSeverity


class ArrayValidator:
    """Array validation functionality."""

    # Expected to be provided by composite validator
    max_array_length: int = 1000

    def _validate_value(self, key: str, value):  # type: ignore[override]
        from autopr.security.validation_models import ValidationResult

        return ValidationResult(is_valid=True, sanitized_data={"value": value})

    def _validate_array(self, key: str, value: list | tuple) -> ValidationResult:
        """Validate array input."""
        result = ValidationResult(is_valid=True)

        # Length validation
        if len(value) > self.max_array_length:  # type: ignore[attr-defined]
            result.errors.append(
                f"Array too long for key '{key}': {len(value)} > {self.max_array_length}"
            )
            result.severity = ValidationSeverity.MEDIUM
            result.is_valid = False
            return result

        sanitized_array = []
        for i, item in enumerate(value):
            item_result = self._validate_value(f"{key}[{i}]", item)  # type: ignore[attr-defined]
            if not item_result.is_valid:
                result.errors.extend(item_result.errors)
                result.warnings.extend(item_result.warnings)
                result.is_valid = False

                # Update severity
                if item_result.severity.value == "critical":
                    result.severity = ValidationSeverity.CRITICAL
                elif (
                    item_result.severity.value == "high"
                    and result.severity != ValidationSeverity.CRITICAL
                ):
                    result.severity = ValidationSeverity.HIGH
            elif (
                isinstance(item_result.sanitized_data, dict)
                and "value" in item_result.sanitized_data
                and len(item_result.sanitized_data) == 1
            ):
                sanitized_array.append(item_result.sanitized_data["value"])
            else:
                sanitized_array.append(item_result.sanitized_data)

        # Wrap array in a dictionary to satisfy type constraints
        if result.is_valid:
            result.sanitized_data = {"items": sanitized_array}

        return result
