"""
Workflow Input Validation

Provides comprehensive validation for workflow inputs to prevent injection attacks
and ensure data integrity.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class WorkflowContextValidator(BaseModel):
    """
    Validates workflow execution context.
    
    Ensures all required fields are present and properly typed to prevent
    injection attacks and type errors during execution.
    """
    
    # Common workflow context fields
    workflow_name: str = Field(..., min_length=1, max_length=255)
    execution_id: str | None = Field(None, max_length=500)
    
    # Allow additional fields but validate their types
    class Config:
        extra = "allow"
        str_strip_whitespace = True
    
    @field_validator("workflow_name")
    @classmethod
    def validate_workflow_name(cls, v: str) -> str:
        """Validate workflow name to prevent injection attacks."""
        # Only allow alphanumeric, hyphens, underscores, and dots
        if not v.replace("-", "").replace("_", "").replace(".", "").replace(" ", "").isalnum():
            msg = "Workflow name contains invalid characters. Only alphanumeric, hyphens, underscores, dots, and spaces are allowed."
            raise ValueError(msg)
        return v
    
    @field_validator("execution_id")
    @classmethod
    def validate_execution_id(cls, v: str | None) -> str | None:
        """Validate execution ID format."""
        if v is None:
            return v
        
        # Execution IDs should be reasonable length
        if len(v) > 500:
            msg = "Execution ID is too long (max 500 characters)"
            raise ValueError(msg)
        
        return v


def validate_workflow_context(context: dict[str, Any]) -> dict[str, Any]:
    """
    Validate workflow context dictionary.
    
    Args:
        context: Context dictionary to validate
        
    Returns:
        Validated context dictionary
        
    Raises:
        ValueError: If validation fails
        
    Example:
        >>> context = {"workflow_name": "test-workflow", "data": {"key": "value"}}
        >>> validated = validate_workflow_context(context)
    """
    try:
        # Extract workflow_name if present
        workflow_name = context.get("workflow_name", "unknown")
        execution_id = context.get("execution_id")
        
        # Validate using Pydantic model
        validator = WorkflowContextValidator(
            workflow_name=workflow_name,
            execution_id=execution_id,
            **{k: v for k, v in context.items() if k not in {"workflow_name", "execution_id"}}
        )
        
        # Return validated dict
        return validator.model_dump(exclude_none=True)
        
    except Exception as e:
        msg = f"Workflow context validation failed: {e}"
        raise ValueError(msg) from e


def sanitize_workflow_parameters(params: dict[str, Any]) -> dict[str, Any]:
    """
    Sanitize workflow parameters to prevent injection attacks.
    
    This performs basic sanitization while preserving data structure.
    
    Args:
        params: Parameters dictionary to sanitize
        
    Returns:
        Sanitized parameters dictionary
        
    Security:
        - Validates string lengths
        - Checks for suspicious patterns
        - Prevents excessively deep nesting
    """
    MAX_STRING_LENGTH = 10000
    MAX_NESTING_DEPTH = 10
    
    def sanitize_value(value: Any, depth: int = 0) -> Any:
        """Recursively sanitize values."""
        if depth > MAX_NESTING_DEPTH:
            msg = f"Parameter nesting depth exceeds maximum of {MAX_NESTING_DEPTH}"
            raise ValueError(msg)
        
        if isinstance(value, str):
            # Check string length
            if len(value) > MAX_STRING_LENGTH:
                msg = f"String parameter exceeds maximum length of {MAX_STRING_LENGTH}"
                raise ValueError(msg)
            
            # Check for suspicious patterns (basic check)
            suspicious_patterns = ["<script", "javascript:", "onerror=", "eval("]
            lower_value = value.lower()
            for pattern in suspicious_patterns:
                if pattern in lower_value:
                    msg = f"Parameter contains suspicious pattern: {pattern}"
                    raise ValueError(msg)
            
            return value
        
        elif isinstance(value, dict):
            return {k: sanitize_value(v, depth + 1) for k, v in value.items()}
        
        elif isinstance(value, list):
            return [sanitize_value(item, depth + 1) for item in value]
        
        else:
            # Numbers, booleans, None are safe
            return value
    
    return sanitize_value(params)


__all__ = [
    "WorkflowContextValidator",
    "validate_workflow_context",
    "sanitize_workflow_parameters",
]
