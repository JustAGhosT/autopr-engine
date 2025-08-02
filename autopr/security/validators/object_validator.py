from ..validation_models import ValidationResult, ValidationSeverity


class ObjectValidator:
    """Object validation functionality."""

    def _validate_object(self, key: str, value: dict) -> ValidationResult:
        """Validate object input."""
        result = ValidationResult(is_valid=True)
        sanitized_object = {}

        for obj_key, obj_value in value.items():
            if not self._is_safe_key(obj_key):
                result.errors.append(f"Invalid nested key name: {key}.{obj_key}")
                result.severity = ValidationSeverity.HIGH
                result.is_valid = False
                continue

            obj_result = self._validate_value(f"{key}.{obj_key}", obj_value)
            if not obj_result.is_valid:
                result.errors.extend(obj_result.errors)
                result.warnings.extend(obj_result.warnings)
                result.is_valid = False

                # Update severity
                if obj_result.severity.value == "critical":
                    result.severity = ValidationSeverity.CRITICAL
                elif (
                    obj_result.severity.value == "high"
                    and result.severity != ValidationSeverity.CRITICAL
                ):
                    result.severity = ValidationSeverity.HIGH
            elif (
                isinstance(obj_result.sanitized_data, dict)
                and "value" in obj_result.sanitized_data
                and len(obj_result.sanitized_data) == 1
            ):
                sanitized_object[obj_key] = obj_result.sanitized_data["value"]
            else:
                sanitized_object[obj_key] = obj_result.sanitized_data

        if result.is_valid:
            result.sanitized_data = sanitized_object

        return result
