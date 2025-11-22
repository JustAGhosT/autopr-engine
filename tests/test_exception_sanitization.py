"""
Tests for Exception Sanitization and Information Leakage Prevention

Tests BUG-9 fix: Ensures sensitive information is not exposed in error messages.
"""

import pytest
from autopr.exceptions import (
    AutoPRException,
    ConfigurationError,
    WorkflowError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    sanitize_error_message,
    handle_exception_safely,
    log_exception_securely,
)


class TestSanitizeErrorMessage:
    """Tests for error message sanitization."""
    
    def test_sanitize_database_connection_string(self):
        """Test that database connection strings are redacted."""
        messages = [
            "Connection failed: postgresql://user:password@localhost:5432/db",
            "Error: mysql://admin:secret123@192.168.1.1/production",
            "Cannot connect to mongodb://user:pass@mongo.example.com/db",
            "SQLite error: sqlite:///app/data/sensitive.db",
        ]
        
        for msg in messages:
            sanitized = sanitize_error_message(msg)
            # Should not contain passwords or connection details
            assert "password" not in sanitized.lower() or "[REDACTED]" in sanitized
            assert "secret" not in sanitized.lower() or "[REDACTED]" in sanitized
            assert "@localhost" not in sanitized or "[REDACTED]" in sanitized
            assert "@192.168" not in sanitized or "[REDACTED]" in sanitized
    
    def test_sanitize_api_keys(self):
        """Test that API keys and tokens are redacted."""
        messages = [
            "API call failed with key: sk-abc123xyz456",
            "Authentication error, token: ghp_1234567890abcdef",
            "Bearer token: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "api_key = abc123def456",
            "secret_token='very_secret_value'",
        ]
        
        for msg in messages:
            sanitized = sanitize_error_message(msg)
            # Should not contain actual keys
            assert "sk-abc123xyz456" not in sanitized
            assert "ghp_1234567890abcdef" not in sanitized
            assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in sanitized
            assert "abc123def456" not in sanitized
            assert "very_secret_value" not in sanitized
            # Should contain redaction marker
            assert "[REDACTED]" in sanitized
    
    def test_sanitize_file_paths(self):
        """Test that file paths are redacted."""
        messages = [
            "File not found: /home/user/app/sensitive_config.py",
            "Error in module: /var/www/autopr/secrets.py",
            "Windows path error: C:\\Users\\Admin\\Documents\\config.py",
        ]
        
        for msg in messages:
            sanitized = sanitize_error_message(msg)
            # Should not contain full file paths
            assert "/home/user" not in sanitized or "[FILE_PATH]" in sanitized
            assert "/var/www" not in sanitized or "[FILE_PATH]" in sanitized
            assert "C:\\Users" not in sanitized or "[FILE_PATH]" in sanitized
    
    def test_sanitize_email_addresses(self):
        """Test that email addresses are redacted."""
        messages = [
            "User not found: admin@company.com",
            "Email error: support@autopr-engine.com",
            "Failed to send to: john.doe@example.org",
        ]
        
        for msg in messages:
            sanitized = sanitize_error_message(msg)
            # Should not contain email addresses
            assert "@company.com" not in sanitized
            assert "@autopr-engine.com" not in sanitized
            assert "@example.org" not in sanitized
            # Should contain redaction marker
            assert "[EMAIL_REDACTED]" in sanitized
    
    def test_sanitize_ip_addresses(self):
        """Test that IP addresses are redacted."""
        messages = [
            "Connection failed to: 192.168.1.100",
            "Timeout connecting to 10.0.0.5",
            "Server error at 172.16.254.1",
        ]
        
        for msg in messages:
            sanitized = sanitize_error_message(msg)
            # Should not contain IP addresses
            assert "192.168.1.100" not in sanitized
            assert "10.0.0.5" not in sanitized
            assert "172.16.254.1" not in sanitized
            # Should contain redaction marker
            assert "[IP_REDACTED]" in sanitized
    
    def test_sanitize_sql_queries(self):
        """Test that SQL queries are redacted."""
        messages = [
            "Query failed: SELECT * FROM users WHERE password='secret'",
            "Error: INSERT INTO credentials VALUES ('admin', 'password123')",
            "Failed: UPDATE users SET api_key='abc123' WHERE id=1",
        ]
        
        for msg in messages:
            sanitized = sanitize_error_message(msg)
            # Should not contain actual query values
            assert "password='secret'" not in sanitized
            assert "'password123'" not in sanitized
            assert "api_key='abc123'" not in sanitized
            # Should contain redaction marker
            assert "[QUERY_REDACTED]" in sanitized
    
    def test_sanitize_technical_details(self):
        """Test that technical details and stack traces are removed."""
        messages = [
            "Traceback (most recent call last):",
            "File 'module.py', line 42, in function",
            "AttributeError: 'NoneType' object has no attribute 'value'",
            "Object at 0x7f8b4c0a3d60",
        ]
        
        for msg in messages:
            sanitized = sanitize_error_message(msg)
            # Should use generic message for technical details
            assert "check the logs" in sanitized.lower() or "contact support" in sanitized.lower()
    
    def test_safe_messages_unchanged(self):
        """Test that safe, user-friendly messages are preserved."""
        messages = [
            "Workflow execution failed",
            "Invalid input provided",
            "Resource not found",
            "Operation timeout",
        ]
        
        for msg in messages:
            sanitized = sanitize_error_message(msg)
            # Should be preserved (or similar)
            assert len(sanitized) > 0
            assert "[REDACTED]" not in sanitized


class TestAutoPRExceptionSanitization:
    """Tests for AutoPRException sanitization methods."""
    
    def test_get_user_message_sanitizes(self):
        """Test that get_user_message() returns sanitized message."""
        exc = AutoPRException(
            "Internal error: postgresql://user:pass@localhost/db",
            error_code="TEST_ERROR"
        )
        
        user_msg = exc.get_user_message()
        
        # Should not contain sensitive data
        assert "pass@localhost" not in user_msg
        assert "[REDACTED]" in user_msg or "contact support" in user_msg.lower()
    
    def test_get_internal_message_preserves(self):
        """Test that get_internal_message() preserves full message."""
        original = "Internal error: postgresql://user:pass@localhost/db"
        exc = AutoPRException(original, error_code="TEST_ERROR")
        
        internal_msg = exc.get_internal_message()
        
        # Should preserve original message
        assert internal_msg == original
    
    def test_custom_user_message(self):
        """Test that custom user messages are used when provided."""
        exc = AutoPRException(
            "Internal error with sensitive data",
            error_code="TEST_ERROR",
            user_message="A friendly error message for users"
        )
        
        user_msg = exc.get_user_message()
        
        # Should use custom message
        assert user_msg == "A friendly error message for users"


class TestSpecificExceptions:
    """Tests for specific exception classes."""
    
    def test_configuration_error_sanitizes_keys(self):
        """Test that ConfigurationError sanitizes config keys."""
        exc = ConfigurationError(
            "Invalid password configuration",
            config_key="database_password"
        )
        
        user_msg = exc.get_user_message()
        
        # Should redact sensitive key names
        assert "password" not in user_msg or "[REDACTED]" in user_msg
    
    def test_workflow_error_preserves_name(self):
        """Test that WorkflowError preserves workflow name."""
        exc = WorkflowError(
            "Internal error with sensitive data",
            workflow_name="test-workflow"
        )
        
        user_msg = exc.get_user_message()
        
        # Should include workflow name (safe)
        assert "test-workflow" in user_msg
        # Should not leak sensitive internal data
        assert "sensitive data" not in user_msg or len(user_msg) < 100
    
    def test_authentication_error_generic(self):
        """Test that AuthenticationError uses generic message."""
        exc = AuthenticationError(
            "Failed to authenticate with token: sk-secret123"
        )
        
        user_msg = exc.get_user_message()
        
        # Should not contain token
        assert "sk-secret123" not in user_msg
        # Should be generic
        assert "authentication" in user_msg.lower()
        assert "credentials" in user_msg.lower()
    
    def test_rate_limit_error_includes_retry(self):
        """Test that RateLimitError includes retry_after."""
        exc = RateLimitError(
            "Rate limit exceeded for API key sk-abc123",
            retry_after=60
        )
        
        user_msg = exc.get_user_message()
        
        # Should not contain API key
        assert "sk-abc123" not in user_msg
        # Should include retry time
        assert "60" in user_msg
    
    def test_validation_error_includes_field(self):
        """Test that ValidationError includes field name."""
        exc = ValidationError(
            "Invalid email format: user@domain.com",
            field_name="email"
        )
        
        user_msg = exc.get_user_message()
        
        # Should include field name
        assert "email" in user_msg.lower()
        # Should not include actual email
        assert "@domain.com" not in user_msg or "[EMAIL_REDACTED]" in user_msg


class TestHandleExceptionSafely:
    """Tests for handle_exception_safely function."""
    
    def test_handle_autopr_exception(self):
        """Test handling of AutoPRException."""
        exc = WorkflowError(
            "Internal workflow error with sensitive data",
            workflow_name="test-workflow"
        )
        
        response = handle_exception_safely(exc, context={'user_id': 123})
        
        # Check response structure
        assert response['success'] is False
        assert 'error' in response
        assert response['error_code'] == 'WORKFLOW_ERROR'
        
        # Check sanitization
        assert "sensitive data" not in response['error']
        
        # Check context inclusion
        assert 'context' in response
        assert response['context']['workflow_name'] == 'test-workflow'
        # user_id should not be in response (only in logs)
        assert 'user_id' not in response.get('context', {})
    
    def test_handle_generic_exception(self):
        """Test handling of generic Python exceptions."""
        exc = ValueError("Invalid database connection: postgresql://user:pass@localhost/db")
        
        response = handle_exception_safely(exc)
        
        # Check response structure
        assert response['success'] is False
        assert 'error' in response
        assert response['error_code'] == 'INTERNAL_ERROR'
        
        # Check sanitization
        assert "pass@localhost" not in response['error']
    
    def test_logging_integration(self, caplog):
        """Test that exceptions are logged internally."""
        import logging
        caplog.set_level(logging.ERROR)
        
        exc = WorkflowError("Internal error")
        
        handle_exception_safely(exc, context={'operation': 'test'})
        
        # Check that error was logged
        assert len(caplog.records) > 0
        # Check that context was included in log
        log_message = caplog.records[0].message
        assert "WorkflowError" in log_message


class TestLogExceptionSecurely:
    """Tests for log_exception_securely function."""
    
    def test_logs_full_exception_details(self, caplog):
        """Test that full exception details are logged internally."""
        import logging
        caplog.set_level(logging.ERROR)
        
        exc = ValueError("Sensitive error: postgresql://user:pass@localhost/db")
        
        log_exception_securely(exc, context={'key': 'value'})
        
        # Should log full details (not sanitized in logs)
        assert len(caplog.records) > 0
        log_message = caplog.records[0].message
        
        # Should include exception type and message
        assert "ValueError" in log_message
        assert "Sensitive error" in log_message
        
        # Should include context
        assert "key=value" in log_message
    
    def test_different_log_levels(self, caplog):
        """Test logging at different levels."""
        import logging
        
        for level in ['debug', 'info', 'warning', 'error', 'critical']:
            caplog.clear()
            caplog.set_level(getattr(logging, level.upper()))
            
            exc = RuntimeError(f"Test error for {level}")
            log_exception_securely(exc, level=level)
            
            if level in ['error', 'critical']:
                assert len(caplog.records) > 0


class TestSecurityIntegration:
    """Integration tests for security features."""
    
    def test_no_sensitive_data_in_user_responses(self):
        """Comprehensive test that sensitive data never reaches users."""
        sensitive_data = [
            "postgresql://admin:SuperSecret123@prod.database.com:5432/app_db",
            "API_KEY=sk-proj-1234567890abcdef",
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.sensitive.data",
            "/home/admin/.ssh/id_rsa",
            "admin@internal-company.com",
            "192.168.1.100:5432",
        ]
        
        for data in sensitive_data:
            # Create exception with sensitive data
            exc = WorkflowError(f"Error occurred: {data}")
            
            # Get user message
            user_msg = exc.get_user_message()
            
            # Verify sensitive data is not in user message
            assert data not in user_msg, f"Sensitive data leaked: {data}"
            
            # Handle exception
            response = handle_exception_safely(exc)
            
            # Verify sensitive data is not in response
            assert data not in str(response), f"Sensitive data leaked in response: {data}"
    
    def test_internal_logs_contain_full_info(self, caplog):
        """Test that internal logs contain full information for debugging."""
        import logging
        caplog.set_level(logging.ERROR)
        
        sensitive_msg = "Connection failed: postgresql://user:pass@localhost/db"
        exc = ValueError(sensitive_msg)
        
        # Log exception
        log_exception_securely(exc)
        
        # Internal logs should have full details
        assert len(caplog.records) > 0
        log_message = caplog.records[0].message
        
        # Should include sensitive data (for internal debugging)
        assert "postgresql:" in log_message
        # Note: password might still be there for internal debugging
        # This is intentional - logs are internal only


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
