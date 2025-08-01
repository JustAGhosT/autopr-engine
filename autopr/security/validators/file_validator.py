import html
import os

from ..validation_models import ValidationResult, ValidationSeverity


class FileValidator:
    """File validation functionality."""

    def validate_file_upload(
        self, filename: str, content: bytes, max_size: int = 10 * 1024 * 1024
    ) -> ValidationResult:
        """Validate file upload."""
        result = ValidationResult(is_valid=True)

        # File size validation
        if len(content) > max_size:
            result.errors.append(f"File too large: {len(content)} > {max_size}")
            result.severity = ValidationSeverity.MEDIUM
            result.is_valid = False
            return result

        # File extension validation
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in self.allowed_file_extensions:
            result.errors.append(f"File extension not allowed: {file_ext}")
            result.severity = ValidationSeverity.HIGH
            result.is_valid = False
            return result

        # Content validation for text files
        if file_ext in {".txt", ".json", ".yaml", ".yml", ".md"}:
            try:
                content_str = content.decode("utf-8")
                content_result = self._validate_string("file_content", content_str)
                if not content_result.is_valid:
                    result.errors.extend(content_result.errors)
                    result.severity = content_result.severity
                    result.is_valid = False
                    return result
            except UnicodeDecodeError:
                result.errors.append("File contains invalid UTF-8 encoding")
                result.severity = ValidationSeverity.HIGH
                result.is_valid = False
                return result

        result.sanitized_data = {
            "filename": html.escape(filename),
            "content": content,
            "size": len(content),
            "extension": file_ext,
        }

        return result
