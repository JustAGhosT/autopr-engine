"""
Global Exception Handling and Sanitization

Provides centralized exception handling with information leakage prevention.
Implements OWASP guidelines for error handling and logging.
"""

import re
import traceback
from typing import Optional, Dict, Any

import structlog

logger = structlog.get_logger(__name__)


# Sensitive patterns to remove from error messages
SENSITIVE_PATTERNS = [
    # File paths
    (r"/home/[^/\s]+", "/home/****"),
    (r"/Users/[^/\s]+", "/Users/****"),
    (r"C:\\Users\\[^\\]+", r"C:\\Users\\****"),
    (r"/var/[^/\s]+", "/var/****"),
    (r"/tmp/[^/\s]+", "/tmp/****"),
    
    # Database connection strings
    (r"postgresql://[^@\s]+@", "postgresql://****:****@"),
    (r"mysql://[^@\s]+@", "mysql://****:****@"),
    (r"mongodb://[^@\s]+@", "mongodb://****:****@"),
    
    # API keys and tokens
    (r"(api[_-]?key|token|secret)['\"]?\s*[:=]\s*['\"]?[\w-]{10,}", r"\1=****"),
    (r"Bearer\s+[\w\-.]+", "Bearer ****"),
    (r"ghp_[\w]{36}", "ghp_****"),  # GitHub tokens
    (r"sk-[\w]{10,}", "sk-****"),     # OpenAI keys (any length 10+)
    
    # IP addresses (partial masking)
    (r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.)\d{1,3}\b", r"\1***"),
    
    # Email addresses (partial masking)
    (r"\b([\w.]+)@([\w.]+)\b", r"****@\2"),
    
    # Stack trace file paths
    (r'File "([^"]+)"', r'File "****"'),
    
    # Database table/column names in SQL errors
    (r"table\s+['\"]?(\w+)['\"]?", "table '****'"),
    (r"column\s+['\"]?(\w+)['\"]?", "column '****'"),
]


# Common sensitive keywords to redact
SENSITIVE_KEYWORDS = [
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_key",
    "private_key",
    "auth",
    "authorization",
    "session",
    "cookie",
]


def sanitize_error_message(message: str, aggressive: bool = False) -> str:
    """
    Sanitize error message by removing sensitive information.
    
    Args:
        message: Original error message
        aggressive: If True, apply more aggressive sanitization
        
    Returns:
        Sanitized error message
    """
    if not message:
        return "An error occurred"
    
    sanitized = message
    
    # Apply regex patterns
    for pattern, replacement in SENSITIVE_PATTERNS:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
    
    # Remove sensitive keyword values
    for keyword in SENSITIVE_KEYWORDS:
        # Match: keyword="value" or keyword='value' or keyword: value
        pattern = rf"{keyword}\s*[:=]\s*['\"]?([^'\"\s,}}]+)['\"]?"
        sanitized = re.sub(pattern, f"{keyword}=****", sanitized, flags=re.IGNORECASE)
    
    if aggressive:
        # Remove all file paths
        sanitized = re.sub(r'[/\\][\w\./\\-]+', '****', sanitized)
        
        # Remove stack traces
        sanitized = re.sub(r'File ".*", line \d+', 'File "****", line ***', sanitized)
        sanitized = re.sub(r'Traceback.*?(?=\n\n|\Z)', '[Stack trace redacted]', sanitized, flags=re.DOTALL)
    
    return sanitized


def sanitize_exception(exc: Exception, include_type: bool = True) -> str:
    """
    Sanitize exception for safe display to users.
    
    Args:
        exc: Exception to sanitize
        include_type: Include exception type name
        
    Returns:
        Sanitized exception message
    """
    exc_type = type(exc).__name__
    exc_message = str(exc)
    
    sanitized_message = sanitize_error_message(exc_message)
    
    if include_type:
        return f"{exc_type}: {sanitized_message}"
    return sanitized_message


def create_safe_error_response(
    exc: Exception,
    status_code: int = 500,
    include_details: bool = False,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a safe error response for API endpoints.
    
    Args:
        exc: Exception that occurred
        status_code: HTTP status code
        include_details: Include sanitized details (for development)
        request_id: Request ID for tracking
        
    Returns:
        Dictionary suitable for JSON response
    """
    # Generic error messages by status code
    generic_messages = {
        400: "Bad request. Please check your input.",
        401: "Authentication required.",
        403: "Access denied.",
        404: "Resource not found.",
        429: "Rate limit exceeded. Please try again later.",
        500: "An internal error occurred. Please try again.",
        503: "Service temporarily unavailable. Please try again later.",
    }
    
    response = {
        "error": generic_messages.get(status_code, "An error occurred"),
        "status_code": status_code,
    }
    
    if request_id:
        response["request_id"] = request_id
    
    if include_details:
        # Only in development/debug mode
        response["details"] = sanitize_exception(exc, include_type=True)
    
    return response


class SafeExceptionHandler:
    """
    Centralized exception handler with logging and sanitization.
    
    Usage:
        handler = SafeExceptionHandler()
        try:
            # code
        except Exception as e:
            return handler.handle_exception(e)
    """
    
    def __init__(self, debug: bool = False):
        """
        Initialize exception handler.
        
        Args:
            debug: Enable debug mode (includes stack traces)
        """
        self.debug = debug
    
    def handle_exception(
        self,
        exc: Exception,
        context: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Handle exception with logging and safe response generation.
        
        Args:
            exc: Exception that occurred
            context: Additional context for logging
            status_code: HTTP status code (auto-detected if None)
            
        Returns:
            Safe error response dictionary
        """
        # Auto-detect status code from exception type
        if status_code is None:
            status_code = self._detect_status_code(exc)
        
        # Log the full exception (not sanitized)
        log_context = context or {}
        logger.exception(
            "Exception occurred",
            exc_type=type(exc).__name__,
            exc_message=str(exc),
            status_code=status_code,
            **log_context
        )
        
        # Create safe response
        response = create_safe_error_response(
            exc,
            status_code=status_code,
            include_details=self.debug,
            request_id=log_context.get("request_id")
        )
        
        return response
    
    def _detect_status_code(self, exc: Exception) -> int:
        """Detect appropriate HTTP status code from exception type."""
        exc_type = type(exc).__name__.lower()
        
        if "auth" in exc_type or "unauthorized" in exc_type:
            return 401
        elif "permission" in exc_type or "forbidden" in exc_type:
            return 403
        elif "notfound" in exc_type or "missing" in exc_type:
            return 404
        elif "validation" in exc_type or "invalid" in exc_type:
            return 400
        elif "timeout" in exc_type:
            return 504
        elif "ratelimit" in exc_type:
            return 429
        else:
            return 500


# Flask exception handler
def setup_flask_exception_handlers(app, debug: bool = False):
    """
    Setup global exception handlers for Flask app.
    
    Usage:
        app = Flask(__name__)
        setup_flask_exception_handlers(app, debug=app.debug)
    """
    from flask import jsonify
    
    handler = SafeExceptionHandler(debug=debug)
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Handle all uncaught exceptions."""
        response_data = handler.handle_exception(e)
        response = jsonify(response_data)
        response.status_code = response_data["status_code"]
        return response
    
    @app.errorhandler(404)
    def handle_404(e):
        """Handle 404 errors."""
        return jsonify({
            "error": "Resource not found",
            "status_code": 404
        }), 404
    
    @app.errorhandler(429)
    def handle_rate_limit(e):
        """Handle rate limit errors."""
        return jsonify({
            "error": "Rate limit exceeded. Please try again later.",
            "status_code": 429
        }), 429


# FastAPI exception handler
def setup_fastapi_exception_handlers(app, debug: bool = False):
    """
    Setup global exception handlers for FastAPI app.
    
    Usage:
        app = FastAPI()
        setup_fastapi_exception_handlers(app, debug=False)
    """
    from fastapi import Request
    from fastapi.responses import JSONResponse
    
    handler = SafeExceptionHandler(debug=debug)
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle all uncaught exceptions."""
        response_data = handler.handle_exception(
            exc,
            context={"path": request.url.path, "method": request.method}
        )
        return JSONResponse(
            status_code=response_data["status_code"],
            content=response_data
        )
    
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        """Handle 404 errors."""
        return JSONResponse(
            status_code=404,
            content={
                "error": "Resource not found",
                "status_code": 404
            }
        )


# Utility function for manual exception handling
def handle_exception_safely(
    exc: Exception,
    default_message: str = "An error occurred",
    include_type: bool = False
) -> str:
    """
    Handle exception and return safe error message.
    
    Args:
        exc: Exception to handle
        default_message: Default message if sanitization produces empty result
        include_type: Include exception type in message
        
    Returns:
        Safe error message
    """
    try:
        message = sanitize_exception(exc, include_type=include_type)
        return message if message else default_message
    except Exception:
        # Failsafe: if sanitization itself fails
        logger.exception("Error during exception sanitization")
        return default_message


# Testing utilities
def test_sanitization():
    """Test sanitization with various sensitive data patterns."""
    test_cases = [
        "Error in /home/username/project/file.py",
        "Connection to postgresql://user:pass@localhost:5432/db failed",
        "API key is api_key=sk-1234567890abcdef",
        "Token: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        "User john.doe@example.com not found",
        "Error at 192.168.1.100",
        'File "/var/app/main.py", line 42',
        "Invalid password for user admin",
    ]
    
    print("Sanitization Test Results:")
    print("=" * 80)
    for test in test_cases:
        sanitized = sanitize_error_message(test)
        print(f"Original:  {test}")
        print(f"Sanitized: {sanitized}")
        print("-" * 80)


if __name__ == "__main__":
    # Run tests when module is executed directly
    test_sanitization()
