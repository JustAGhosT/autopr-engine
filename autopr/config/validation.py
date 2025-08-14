"""
Configuration Validation Utilities

This module provides comprehensive validation for AutoPR configuration,
including environment-specific checks, security validations, and
dependency verification.
"""

import os
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse

from .settings import AutoPRSettings, Environment, LLMProvider


class ConfigurationValidator:
    """Validates AutoPR configuration for completeness and security."""

    def __init__(self, settings: AutoPRSettings):
        self.settings = settings
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate_all(self) -> tuple[list[str], list[str]]:
        """
        Run all validation checks.

        Returns:
            Tuple of (errors, warnings)
        """
        self.errors.clear()
        self.warnings.clear()

        # Run all validation methods
        self._validate_github_config()
        self._validate_llm_config()
        self._validate_database_config()
        self._validate_redis_config()
        self._validate_security_config()
        self._validate_monitoring_config()
        self._validate_workflow_config()
        self._validate_environment_specific()

        return self.errors.copy(), self.warnings.copy()

    def _validate_github_config(self) -> None:
        """Validate GitHub configuration."""
        github = self.settings.github

        # Authentication validation
        if not github.token and not github.app_id:
            self.errors.append(
                "GitHub authentication required: provide either GITHUB_TOKEN or GITHUB_APP_ID"
            )

        if github.app_id and not github.private_key:
            self.errors.append("GITHUB_PRIVATE_KEY is required when using GITHUB_APP_ID")

        # URL validation
        if github.base_url:
            parsed = urlparse(str(github.base_url))
            if not parsed.scheme or not parsed.netloc:
                self.errors.append(f"Invalid GitHub base URL: {github.base_url}")

        # Timeout validation
        if github.timeout <= 0:
            self.errors.append("GitHub timeout must be positive")
        elif github.timeout < 5:
            self.warnings.append("GitHub timeout is very low, may cause request failures")

        # Retries validation
        if github.max_retries < 0:
            self.errors.append("GitHub max_retries cannot be negative")
        elif github.max_retries > 10:
            self.warnings.append("GitHub max_retries is very high, may cause long delays")

    def _validate_llm_config(self) -> None:
        """Validate LLM configuration."""
        llm = self.settings.llm

        # Check if at least one provider is configured
        provider_keys = [
            llm.openai_api_key,
            llm.anthropic_api_key,
            llm.mistral_api_key,
            llm.groq_api_key,
            llm.perplexity_api_key,
            llm.together_api_key,
        ]

        if not any(key for key in provider_keys):
            self.errors.append("At least one LLM provider API key is required")

        # Validate default provider has API key
        default_provider = llm.default_provider
        provider_key_map = {
            LLMProvider.OPENAI: llm.openai_api_key,
            LLMProvider.ANTHROPIC: llm.anthropic_api_key,
            LLMProvider.MISTRAL: llm.mistral_api_key,
            LLMProvider.GROQ: llm.groq_api_key,
            LLMProvider.PERPLEXITY: llm.perplexity_api_key,
            LLMProvider.TOGETHER: llm.together_api_key,
        }

        if not provider_key_map.get(default_provider):
            self.warnings.append(
                f"Default LLM provider '{default_provider}' has no API key configured"
            )

        # Validate fallback order
        for provider in llm.fallback_order:
            if not provider_key_map.get(provider):
                self.warnings.append(f"Fallback provider '{provider}' has no API key configured")

        # Parameter validation
        if llm.max_tokens <= 0:
            self.errors.append("LLM max_tokens must be positive")
        elif llm.max_tokens > 32000:
            self.warnings.append("LLM max_tokens is very high, may be expensive")

        if not 0 <= llm.temperature <= 2:
            self.errors.append("LLM temperature must be between 0 and 2")

        if llm.timeout <= 0:
            self.errors.append("LLM timeout must be positive")
        elif llm.timeout < 10:
            self.warnings.append("LLM timeout is very low, may cause request failures")

    def _validate_database_config(self) -> None:
        """Validate database configuration."""
        db = self.settings.database

        if db.url:
            # Validate database URL format
            if not db.url.startswith(("postgresql://", "mysql://", "sqlite://")):
                self.warnings.append(
                    "Database URL should use a supported scheme (postgresql, mysql, sqlite)"
                )

        # Pool settings validation
        if db.pool_size <= 0:
            self.errors.append("Database pool_size must be positive")
        elif db.pool_size > 100:
            self.warnings.append("Database pool_size is very high")

        if db.max_overflow < 0:
            self.errors.append("Database max_overflow cannot be negative")

        if db.pool_timeout <= 0:
            self.errors.append("Database pool_timeout must be positive")

    def _validate_redis_config(self) -> None:
        """Validate Redis configuration."""
        redis = self.settings.redis

        if redis.url:
            # Validate Redis URL format
            if not redis.url.startswith(("redis://", "rediss://")):
                self.warnings.append("Redis URL should use redis:// or rediss:// scheme")

        # Port validation
        if not 1 <= redis.port <= 65535:
            self.errors.append("Redis port must be between 1 and 65535")

        # Database number validation
        if not 0 <= redis.db <= 15:
            self.errors.append("Redis database number must be between 0 and 15")

        # Connection settings
        if redis.max_connections <= 0:
            self.errors.append("Redis max_connections must be positive")
        elif redis.max_connections > 1000:
            self.warnings.append("Redis max_connections is very high")

    def _validate_security_config(self) -> None:
        """Validate security configuration."""
        security = self.settings.security

        # Secret key validation
        if self.settings.environment == Environment.PRODUCTION:
            if not security.secret_key:
                self.errors.append("SECRET_KEY is required in production environment")
            elif len(str(security.secret_key)) < 32:
                self.errors.append("SECRET_KEY should be at least 32 characters long")

        # JWT validation
        if security.jwt_secret and len(str(security.jwt_secret)) < 32:
            self.warnings.append("JWT_SECRET should be at least 32 characters long")

        if security.jwt_expiry <= 0:
            self.errors.append("JWT expiry must be positive")
        elif security.jwt_expiry > 86400:  # 24 hours
            self.warnings.append("JWT expiry is very long, consider shorter duration for security")

        # Rate limiting
        if security.rate_limit_per_minute <= 0:
            self.errors.append("Rate limit must be positive")

        # CORS validation
        if security.enable_cors and not security.allowed_origins:
            if self.settings.environment == Environment.PRODUCTION:
                self.errors.append("CORS allowed_origins must be specified in production")
            else:
                self.warnings.append("CORS is enabled but no allowed_origins specified")

    def _validate_monitoring_config(self) -> None:
        """Validate monitoring configuration."""
        monitoring = self.settings.monitoring

        # Port validation
        if not 1024 <= monitoring.metrics_port <= 65535:
            self.warnings.append("Metrics port should be between 1024 and 65535")

        # Tracing validation
        if monitoring.enable_tracing and not monitoring.jaeger_endpoint:
            self.warnings.append("Tracing is enabled but no Jaeger endpoint configured")

        # Sentry validation
        if monitoring.sentry_dsn and not str(monitoring.sentry_dsn).startswith("https://"):
            self.warnings.append("Sentry DSN should start with https://")

    def _validate_workflow_config(self) -> None:
        """Validate workflow configuration."""
        workflow = self.settings.workflow

        if workflow.max_concurrent <= 0:
            self.errors.append("Workflow max_concurrent must be positive")
        elif workflow.max_concurrent > 100:
            self.warnings.append(
                "Workflow max_concurrent is very high, may consume too many resources"
            )

        if workflow.timeout <= 0:
            self.errors.append("Workflow timeout must be positive")
        elif workflow.timeout < 30:
            self.warnings.append("Workflow timeout is very low, may cause premature failures")

        if workflow.retry_attempts < 0:
            self.errors.append("Workflow retry_attempts cannot be negative")
        elif workflow.retry_attempts > 10:
            self.warnings.append("Workflow retry_attempts is very high")

        if workflow.retry_delay <= 0:
            self.errors.append("Workflow retry_delay must be positive")

    def _validate_environment_specific(self) -> None:
        """Validate environment-specific requirements."""
        env = self.settings.environment

        if env == Environment.PRODUCTION:
            # Production-specific validations
            if self.settings.debug:
                self.errors.append("Debug mode should be disabled in production")

            if self.settings.monitoring.log_level == "DEBUG":
                self.warnings.append("Debug logging should be avoided in production")

            if not self.settings.monitoring.enable_metrics:
                self.warnings.append("Metrics should be enabled in production")

            if not self.settings.security.enable_csrf_protection:
                self.warnings.append("CSRF protection should be enabled in production")

        elif env == Environment.DEVELOPMENT:
            # Development-specific recommendations
            if not self.settings.debug:
                self.warnings.append("Debug mode is typically enabled in development")

            if self.settings.monitoring.log_level != "DEBUG":
                self.warnings.append("Debug logging is recommended in development")

        elif env == Environment.TESTING:
            # Testing-specific validations
            if self.settings.workflow.max_concurrent > 1:
                self.warnings.append("Sequential execution is recommended for testing")

            if self.settings.workflow.retry_attempts > 0:
                self.warnings.append(
                    "Retries should be disabled in testing for predictable results"
                )


def validate_configuration(settings: AutoPRSettings) -> dict[str, Any]:
    """
    Validate configuration and return results.

    Args:
        settings: AutoPRSettings instance to validate

    Returns:
        Dictionary with validation results
    """
    validator = ConfigurationValidator(settings)
    errors, warnings = validator.validate_all()

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }


def check_environment_variables() -> dict[str, Any]:
    """
    Check for common environment variable issues.

    Returns:
        Dictionary with environment variable check results
    """
    issues = []
    recommendations = []

    # Check for common environment variables
    important_vars = [
        "GITHUB_TOKEN",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "DATABASE_URL",
        "REDIS_URL",
        "SECRET_KEY",
    ]

    missing_vars = [var for var in important_vars if not os.getenv(var)]

    if missing_vars:
        recommendations.append(
            f"Consider setting these environment variables: {', '.join(missing_vars)}"
        )

    # Check for .env file
    env_files = [".env", ".env.local", ".env.development", ".env.production"]
    found_env_files = [f for f in env_files if Path(f).exists()]

    if not found_env_files:
        recommendations.append("Consider creating a .env file for environment variables")

    # Check for sensitive data in environment
    sensitive_patterns = [r".*[Pp]assword.*", r".*[Ss]ecret.*", r".*[Kk]ey.*", r".*[Tt]oken.*"]

    for var_name, var_value in os.environ.items():
        if any(re.match(pattern, var_name) for pattern in sensitive_patterns):
            if var_value and len(var_value) < 16:
                issues.append(
                    f"Environment variable {var_name} appears to be too short for a secure value"
                )

    return {
        "issues": issues,
        "recommendations": recommendations,
        "missing_important_vars": missing_vars,
        "found_env_files": found_env_files,
    }


def generate_config_report(settings: AutoPRSettings) -> str:
    """
    Generate a comprehensive configuration report.

    Args:
        settings: AutoPRSettings instance

    Returns:
        Formatted configuration report
    """
    validation_result = validate_configuration(settings)
    env_check = check_environment_variables()

    report = []
    report.append("=" * 60)
    report.append("AutoPR Configuration Report")
    report.append("=" * 60)
    report.append("")

    # Basic information
    report.append(f"Environment: {settings.environment.value}")
    report.append(f"Debug Mode: {settings.debug}")
    report.append(f"Version: {settings.version}")
    report.append("")

    # Validation results
    if validation_result["valid"]:
        report.append("✅ Configuration is valid")
    else:
        report.append("❌ Configuration has errors")

    report.extend(
        (
            f"Errors: {validation_result['error_count']}",
            f"Warnings: {validation_result['warning_count']}",
            "",
        )
    )

    # Errors
    if validation_result["errors"]:
        report.append("🚨 Errors:")
        report.extend(f"  - {error}" for error in validation_result["errors"])
        report.append("")

    # Warnings
    if validation_result["warnings"]:
        report.append("⚠️  Warnings:")
        report.extend(f"  - {warning}" for warning in validation_result["warnings"])
        report.append("")

    # Environment variable recommendations
    if env_check["recommendations"]:
        report.append("💡 Recommendations:")
        report.extend(f"  - {rec}" for rec in env_check["recommendations"])
        report.append("")

    # Configuration summary
    report.extend(
        (
            "📋 Configuration Summary:",
            f"  GitHub: {'✅' if settings.github.token or settings.github.app_id else '❌'}",
        )
    )

    llm_providers = []
    if settings.llm.openai_api_key:
        llm_providers.append("OpenAI")
    if settings.llm.anthropic_api_key:
        llm_providers.append("Anthropic")
    if settings.llm.mistral_api_key:
        llm_providers.append("Mistral")
    if settings.llm.groq_api_key:
        llm_providers.append("Groq")

    report.extend(
        (
            f"  LLM Providers: {', '.join(llm_providers) if llm_providers else 'None'}",
            f"  Database: {'✅' if settings.database.url else '❌'}",
            f"  Redis: {'✅' if settings.redis.url else '❌'}",
            f"  Monitoring: {'✅' if settings.monitoring.enable_metrics else '❌'}",
            "",
            "=" * 60,
        )
    )

    return "\n".join(report)
