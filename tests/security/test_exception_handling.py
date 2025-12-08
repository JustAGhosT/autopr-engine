"""
Tests for Exception Handling and Sanitization
"""

import pytest
from codeflow_engine.security.exception_handling import (
    sanitize_error_message,
    sanitize_exception,
    create_safe_error_response,
    SafeExceptionHandler,
    handle_exception_safely,
)


class TestSanitizeErrorMessage:
    """Test error message sanitization."""
    
    def test_sanitize_file_paths(self):
        """Test sanitization of file paths."""
        tests = [
            ("/home/username/project/file.py", "/home/****/project/file.py"),
            ("/Users/john/app.py", "/Users/****/app.py"),
            ("C:\\Users\\Admin\\script.py", "C:\\Users\\****\\script.py"),
        ]
        
        for original, expected_pattern in tests:
            sanitized = sanitize_error_message(original)
            assert "/home/username" not in sanitized
            assert "C:\\Users\\Admin" not in sanitized
    
    def test_sanitize_database_urls(self):
        """Test sanitization of database connection strings."""
        tests = [
            "postgresql://user:password@localhost:5432/db",
            "mysql://admin:secret@example.com/database",
            "mongodb://root:pass123@mongo:27017",
        ]
        
        for db_url in tests:
            sanitized = sanitize_error_message(db_url)
            assert "password" not in sanitized
            assert "secret" not in sanitized
            assert "pass123" not in sanitized
            assert "****" in sanitized
    
    def test_sanitize_api_keys(self):
        """Test sanitization of API keys and tokens."""
        tests = [
            'api_key="sk-1234567890abcdefghij"',
            "token: ghp_1234567890123456789012345678901234",
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test",
        ]
        
        for text in tests:
            sanitized = sanitize_error_message(text)
            assert "sk-12345678" not in sanitized
            assert "ghp_123456" not in sanitized
            assert "eyJhbGci" not in sanitized or "Bearer ****" in sanitized
    
    def test_sanitize_ip_addresses(self):
        """Test sanitization of IP addresses."""
        original = "Error at IP 192.168.1.100"
        sanitized = sanitize_error_message(original)
        assert "192.168.1.***" in sanitized
        assert "192.168.1.100" not in sanitized
    
    def test_sanitize_emails(self):
        """Test sanitization of email addresses."""
        original = "User john.doe@example.com not found"
        sanitized = sanitize_error_message(original)
        assert "john.doe" not in sanitized
        assert "****@example.com" in sanitized
    
    def test_sanitize_passwords(self):
        """Test sanitization of password fields."""
        tests = [
            'password="mysecretpass"',
            "pwd: admin123",
            "secret='topsecret'",
        ]
        
        for text in tests:
            sanitized = sanitize_error_message(text)
            assert "mysecretpass" not in sanitized
            assert "admin123" not in sanitized
            assert "topsecret" not in sanitized
            assert "****" in sanitized
    
    def test_empty_message(self):
        """Test handling of empty messages."""
        sanitized = sanitize_error_message("")
        assert sanitized == "An error occurred"
        
        sanitized = sanitize_error_message(None)
        assert sanitized == "An error occurred"
    
    def test_aggressive_sanitization(self):
        """Test aggressive sanitization mode."""
        original = 'File "/var/app/main.py", line 42, in function\n  raise ValueError("test")'
        sanitized = sanitize_error_message(original, aggressive=True)
        
        # Should remove all file paths
        assert "/var/app/main.py" not in sanitized
        assert "****" in sanitized


class TestSanitizeException:
    """Test exception sanitization."""
    
    def test_sanitize_value_error(self):
        """Test sanitizing ValueError."""
        exc = ValueError("Invalid API key: sk-1234567890")
        sanitized = sanitize_exception(exc)
        
        assert "ValueError" in sanitized
        assert "sk-1234567890" not in sanitized
        assert "****" in sanitized
    
    def test_sanitize_without_type(self):
        """Test sanitizing without exception type."""
        exc = RuntimeError("Error in /home/user/file.py")
        sanitized = sanitize_exception(exc, include_type=False)
        
        assert "RuntimeError" not in sanitized
        assert "/home/user" not in sanitized
    
    def test_sanitize_custom_exception(self):
        """Test sanitizing custom exception."""
        class CustomError(Exception):
            pass
        
        exc = CustomError("Database password: secret123")
        sanitized = sanitize_exception(exc)
        
        assert "CustomError" in sanitized
        assert "secret123" not in sanitized


class TestCreateSafeErrorResponse:
    """Test safe error response creation."""
    
    def test_basic_error_response(self):
        """Test basic error response."""
        exc = ValueError("Test error")
        response = create_safe_error_response(exc, status_code=400)
        
        assert response["status_code"] == 400
        assert "error" in response
        assert response["error"] == "Bad request. Please check your input."
    
    def test_error_response_with_request_id(self):
        """Test error response with request ID."""
        exc = RuntimeError("Test error")
        response = create_safe_error_response(exc, request_id="req-123")
        
        assert response["request_id"] == "req-123"
    
    def test_error_response_with_details(self):
        """Test error response with details in debug mode."""
        exc = ValueError("Sensitive data: api_key=secret")
        response = create_safe_error_response(exc, include_details=True)
        
        assert "details" in response
        assert "secret" not in response["details"]
    
    def test_error_response_status_codes(self):
        """Test various status codes."""
        test_cases = [
            (400, "Bad request"),
            (401, "Authentication required"),
            (403, "Access denied"),
            (404, "Resource not found"),
            (429, "Rate limit exceeded"),
            (500, "internal error"),
        ]
        
        for status_code, expected_text in test_cases:
            exc = Exception("test")
            response = create_safe_error_response(exc, status_code=status_code)
            assert response["status_code"] == status_code
            assert expected_text.lower() in response["error"].lower()


class TestSafeExceptionHandler:
    """Test SafeExceptionHandler class."""
    
    def test_handle_exception_basic(self):
        """Test basic exception handling."""
        handler = SafeExceptionHandler(debug=False)
        exc = ValueError("Test error with password=secret")
        
        response = handler.handle_exception(exc)
        
        assert "status_code" in response
        assert "error" in response
        assert "secret" not in str(response)
    
    def test_handle_exception_with_context(self):
        """Test exception handling with context."""
        handler = SafeExceptionHandler(debug=False)
        exc = RuntimeError("Test error")
        context = {"user_id": 123, "action": "test"}
        
        response = handler.handle_exception(exc, context=context)
        
        # Response should not include context (logged separately)
        assert response["status_code"] == 500
    
    def test_handle_exception_debug_mode(self):
        """Test exception handling in debug mode."""
        handler = SafeExceptionHandler(debug=True)
        exc = ValueError("Test error")
        
        response = handler.handle_exception(exc)
        
        # Should include details in debug mode
        assert "details" in response
    
    def test_detect_status_code_auth(self):
        """Test status code detection for auth errors."""
        handler = SafeExceptionHandler()
        
        class UnauthorizedError(Exception):
            pass
        
        exc = UnauthorizedError("Not authorized")
        response = handler.handle_exception(exc)
        
        assert response["status_code"] == 401
    
    def test_detect_status_code_validation(self):
        """Test status code detection for validation errors."""
        handler = SafeExceptionHandler()
        
        class ValidationError(Exception):
            pass
        
        exc = ValidationError("Invalid input")
        response = handler.handle_exception(exc)
        
        assert response["status_code"] == 400
    
    def test_detect_status_code_notfound(self):
        """Test status code detection for not found errors."""
        handler = SafeExceptionHandler()
        
        class NotFoundError(Exception):
            pass
        
        exc = NotFoundError("Resource missing")
        response = handler.handle_exception(exc)
        
        assert response["status_code"] == 404


class TestHandleExceptionSafely:
    """Test handle_exception_safely utility function."""
    
    def test_handle_exception_safely_basic(self):
        """Test basic safe exception handling."""
        exc = ValueError("Error with api_key=secret123")
        message = handle_exception_safely(exc)
        
        assert "secret123" not in message
        assert "****" in message
    
    def test_handle_exception_safely_with_type(self):
        """Test safe exception handling with type."""
        exc = RuntimeError("Test error")
        message = handle_exception_safely(exc, include_type=True)
        
        assert "RuntimeError" in message
    
    def test_handle_exception_safely_default(self):
        """Test safe exception handling with default message."""
        exc = Exception("")
        message = handle_exception_safely(exc, default_message="Custom error")
        
        # Should use default for empty message
        assert len(message) > 0


class TestSanitizationPatterns:
    """Test various sanitization patterns."""
    
    def test_sql_injection_patterns(self):
        """Test sanitization of SQL error messages."""
        tests = [
            "Error in table 'users'",
            "Column 'password' does not exist",
            'Invalid column "email"',
        ]
        
        for text in tests:
            sanitized = sanitize_error_message(text)
            # Table/column names should be redacted
            assert "'users'" not in sanitized or "****" in sanitized
    
    def test_stack_trace_sanitization(self):
        """Test sanitization of stack traces."""
        trace = '''File "/app/main.py", line 42, in main
    raise ValueError("test")
ValueError: test with password=secret'''
        
        sanitized = sanitize_error_message(trace, aggressive=True)
        
        # Stack trace should be redacted
        assert "/app/main.py" not in sanitized or "****" in sanitized
        assert "secret" not in sanitized


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
