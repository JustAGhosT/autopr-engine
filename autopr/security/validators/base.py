from typing import Any

import structlog

from autopr.security.validation_models import ValidationResult, ValidationSeverity

from .array_validator import ArrayValidator
from .file_validator import FileValidator
from .number_validator import NumberValidator
from .object_validator import ObjectValidator
from .string_validator import StringValidator

logger = structlog.get_logger(__name__)


class EnterpriseInputValidator(
    StringValidator, ArrayValidator, ObjectValidator, NumberValidator, FileValidator
):
    """Enterprise-grade input validation and sanitization."""

    # Security patterns for common attacks
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\bUNION\s+SELECT\b)",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>",
        r"<object[^>]*>.*?</object>",
        r"<embed[^>]*>.*?</embed>",
    ]

    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$(){}[\]\\]",
        r"\b(rm|del|format|shutdown|reboot|halt)\b",
        r"(>|>>|<|\|)",
    ]

    def __init__(self):
        self.max_string_length = 10000
        self.max_array_length = 1000
        self.allowed_file_extensions = {".txt", ".json", ".yaml", ".yml", ".md"}

    def validate_input(self, data: dict[str, Any], schema: type | None = None) -> ValidationResult:
        """Comprehensive input validation."""
        result = ValidationResult(is_valid=True)
        sanitized_data = {}

        try:
            for key, value in data.items():
                # Validate key name
                if not self._is_safe_key(key):
                    result.errors.append(f"Invalid key name: {key}")
                    result.severity = ValidationSeverity.HIGH
                    result.is_valid = False
                    continue

                # Validate and sanitize value
                validation_result = self._validate_value(key, value)

                if not validation_result.is_valid:
                    result.errors.extend(validation_result.errors)
                    result.warnings.extend(validation_result.warnings)
                    result.is_valid = False

                    # Update severity to highest found
                    if validation_result.severity.value == "critical":
                        result.severity = ValidationSeverity.CRITICAL
                    elif (
                        validation_result.severity.value == "high"
                        and result.severity != ValidationSeverity.CRITICAL
                    ):
                        result.severity = ValidationSeverity.HIGH
                    elif validation_result.severity.value == "medium" and result.severity not in [
                        ValidationSeverity.CRITICAL,
                        ValidationSeverity.HIGH,
                    ]:
                        result.severity = ValidationSeverity.MEDIUM
                else:
                    sanitized_data[key] = validation_result.sanitized_data

            # Apply schema validation if provided
            if schema and result.is_valid:
                try:
                    # Use the schema with the dictionary unpacked
                    validated_data = schema(**sanitized_data)
                    if hasattr(validated_data, "dict"):
                        result.sanitized_data = validated_data.dict()
                    else:
                        result.sanitized_data = sanitized_data
                except Exception as e:
                    result.errors.append(f"Schema validation failed: {e!s}")
                    result.is_valid = False
                    result.severity = ValidationSeverity.HIGH
            else:
                result.sanitized_data = sanitized_data

            # Log validation results
            if not result.is_valid:
                logger.warning(
                    "Input validation failed",
                    errors=result.errors,
                    severity=result.severity.value,
                    data_keys=list(data.keys()),
                )
            else:
                logger.debug("Input validation passed", data_keys=list(data.keys()))

            return result

        except Exception as e:
            logger.error("Input validation error", error=str(e))
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation system error: {e!s}"],
                severity=ValidationSeverity.CRITICAL,
            )

    def _validate_value(self, key: str, value: Any) -> ValidationResult:
        """Validate individual value based on its type."""
        result = ValidationResult(is_valid=True)

        if isinstance(value, str):
            result = self._validate_string(key, value)
        elif isinstance(value, (list, tuple)):
            result = self._validate_array(key, value)
        elif isinstance(value, dict):
            result = self._validate_object(key, value)
        elif isinstance(value, (int, float)):
            result = self._validate_number(key, value)
        else:
            result.sanitized_data = {"value": value}  # Wrap in dict to satisfy type constraints

        return result
