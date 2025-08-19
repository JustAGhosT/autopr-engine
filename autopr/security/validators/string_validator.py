import html
import re

from autopr.security.validation_models import ValidationResult, ValidationSeverity

# Constants
MAX_KEY_LENGTH = 100


class StringValidator:
    """String validation functionality."""

    def __init__(self, max_string_length: int = 1000):
        self.max_string_length = max_string_length
        self.SQL_INJECTION_PATTERNS = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|SCRIPT)\b)",
            r"(\b(OR|AND)\b\s+\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\b\s+['\"]\w+['\"]\s*=\s*['\"]\w+['\"])",
            r"(--|\b(COMMENT|REM)\b)",
            r"(\b(WAITFOR|DELAY)\b)",
            r"(\b(BENCHMARK|SLEEP)\b)",
        ]
        self.XSS_PATTERNS = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<form[^>]*>",
            r"<input[^>]*>",
            r"<textarea[^>]*>",
            r"<select[^>]*>",
        ]
        self.COMMAND_INJECTION_PATTERNS = [
            r"[;&|`$(){}[\]]",
            r"\b(cat|ls|pwd|whoami|id|uname|ps|top|kill|rm|cp|mv|chmod|chown)\b",
            r"\b(netcat|nc|telnet|ssh|scp|wget|curl|ftp|sftp)\b",
            r"\b(bash|sh|zsh|fish|powershell|cmd|command)\b",
        ]

    def _validate_string(self, key: str, value: str) -> ValidationResult:
        """Validate string input for security threats."""
        result = ValidationResult(is_valid=True)

        # Check length validation
        if len(value) > self.max_string_length:
            result.errors.append(
                f"String too long for key '{key}': {len(value)} > {self.max_string_length}"
            )
            result.severity = ValidationSeverity.MEDIUM
            result.is_valid = False
            return result

        # Check for security threats
        threat_check = self._check_security_threats(key, value)
        if not threat_check.is_valid:
            return threat_check

        # Sanitize HTML entities
        sanitized_value = html.escape(value)

        # Check format validation
        format_check = self._check_format_validation(key, sanitized_value)
        if not format_check.is_valid:
            return format_check

        # Wrap string value in a dictionary to satisfy type constraints
        result.sanitized_data = {"value": sanitized_value}
        return result

    def _check_security_threats(self, key: str, value: str) -> ValidationResult:
        """Check for security threats in the string."""
        result = ValidationResult(is_valid=True)

        # SQL Injection detection
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                result.errors.append(f"Potential SQL injection detected in '{key}'")
                result.severity = ValidationSeverity.CRITICAL
                result.is_valid = False
                return result

        # XSS detection
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                result.errors.append(f"Potential XSS attack detected in '{key}'")
                result.severity = ValidationSeverity.CRITICAL
                result.is_valid = False
                return result

        # Command injection detection
        for pattern in self.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value):
                result.errors.append(f"Potential command injection detected in '{key}'")
                result.severity = ValidationSeverity.CRITICAL
                result.is_valid = False
                return result

        return result

    def _check_format_validation(self, key: str, sanitized_value: str) -> ValidationResult:
        """Check format validation for specific contexts."""
        result = ValidationResult(is_valid=True)

        # Additional sanitization for specific contexts
        if "email" in key.lower() and not self._is_valid_email(sanitized_value):
            result.errors.append(f"Invalid email format in '{key}'")
            result.severity = ValidationSeverity.MEDIUM
            result.is_valid = False
            return result

        if "url" in key.lower() and not self._is_valid_url(sanitized_value):
            result.errors.append(f"Invalid URL format in '{key}'")
            result.severity = ValidationSeverity.MEDIUM
            result.is_valid = False
            return result

        return result

    def _is_safe_key(self, key: str) -> bool:
        """Check if key name is safe."""
        # Allow alphanumeric, underscore, hyphen, and dot
        safe_pattern = r"^[a-zA-Z0-9_\-\.]+$"
        return bool(re.match(safe_pattern, key)) and len(key) <= MAX_KEY_LENGTH

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(email_pattern, email))

    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format."""
        url_pattern = r"^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$"
        return bool(re.match(url_pattern, url))
