"""
Enhanced Configuration Management for AutoPR Engine

This module provides a comprehensive configuration system with:
- Environment-specific configurations
- Validation and type checking
- Secure secret handling
- Configuration inheritance
- Hot reloading capabilities
"""

from enum import StrEnum
import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
import yaml  # type: ignore[import-untyped]


# Flag to track Pydantic version
_PYDANTIC_V2 = True
try:
    # Pydantic 2.0+ (preferred)
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    # Pydantic 1.x fallback
    from pydantic.env_settings import BaseSettings  # type: ignore[no-redef]
    SettingsConfigDict = None  # type: ignore[misc,assignment]
    _PYDANTIC_V2 = False


class Environment(StrEnum):
    """Environment types."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(StrEnum):
    """Logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LLMProvider(StrEnum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MISTRAL = "mistral"
    GROQ = "groq"
    PERPLEXITY = "perplexity"
    TOGETHER = "together"


class GitHubConfig(BaseModel):
    """GitHub integration configuration."""

    token: SecretStr | None = Field(default=None)
    app_id: int | None = Field(default=None)
    private_key: SecretStr | None = Field(default=None)
    timeout: int = 30
    base_url: str = "https://api.github.com"

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        if v <= 0:
            msg = "timeout must be positive"
            raise ValueError(msg)
        return v

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: SecretStr | None) -> SecretStr | None:
        if v is None:
            return v
        try:
            token_value = v.get_secret_value()
        except Exception:
            token_value = str(v)
        if not token_value or not token_value.startswith(("ghp_", "github_pat_")):
            msg = "Invalid GitHub token format"
            raise ValueError(msg)
        return v


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    default_provider: LLMProvider = Field(default=LLMProvider.OPENAI)
    fallback_order: list[LLMProvider] = Field(
        default_factory=lambda: [
            LLMProvider.OPENAI,
            LLMProvider.ANTHROPIC,
            LLMProvider.MISTRAL,
        ]
    )

    # Provider-specific configurations
    openai_api_key: SecretStr | None = Field(default=None)
    openai_base_url: str | None = Field(default=None)
    openai_default_model: str = Field(default="gpt-4")

    anthropic_api_key: SecretStr | None = Field(default=None)
    anthropic_base_url: str | None = Field(default=None)
    anthropic_default_model: str = Field(default="claude-3-sonnet-20240229")

    mistral_api_key: SecretStr | None = Field(default=None)
    mistral_base_url: str | None = Field(default=None)
    mistral_default_model: str = Field(default="mistral-large-latest")

    groq_api_key: SecretStr | None = Field(default=None)
    groq_base_url: str | None = Field(default=None)
    groq_default_model: str = Field(default="mixtral-8x7b-32768")

    perplexity_api_key: SecretStr | None = Field(default=None)
    perplexity_base_url: str | None = Field(default=None)
    perplexity_default_model: str = Field(default="llama-3.1-sonar-large-128k-online")

    together_api_key: SecretStr | None = Field(default=None)
    together_base_url: str | None = Field(default=None)
    together_default_model: str = Field(default="meta-llama/Llama-2-70b-chat-hf")

    # General LLM settings
    max_tokens: int = Field(default=4000)
    temperature: float = Field(default=0.7)
    timeout: int = Field(default=60)
    max_retries: int = Field(default=3)

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if not 0 <= v <= 2:
            msg = "temperature must be between 0 and 2"
            raise ValueError(msg)
        return v


class DatabaseConfig(BaseModel):
    """Database configuration."""

    url: str | None = Field(default=None)
    pool_size: int = Field(default=10)
    max_overflow: int = Field(default=20)
    pool_timeout: int = Field(default=30)
    pool_recycle: int = Field(default=3600)
    echo: bool = Field(default=False)


class RedisConfig(BaseModel):
    """Redis configuration."""

    url: str | None = Field(default=None)
    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    db: int = Field(default=0)
    password: SecretStr | None = Field(default=None)
    ssl: bool = Field(default=False)
    timeout: int = Field(default=5)
    max_connections: int = Field(default=50)


class WorkflowConfig(BaseModel):
    """Workflow execution configuration."""

    max_concurrent: int = Field(default=10)
    timeout: int = Field(default=300)
    retry_attempts: int = Field(default=3)
    retry_delay: int = Field(default=5)
    enable_parallel_execution: bool = Field(default=True)


class MonitoringConfig(BaseModel):
    """Monitoring and observability configuration."""

    enable_metrics: bool = Field(default=True)
    metrics_port: int = Field(default=8000)
    enable_tracing: bool = Field(default=False)
    jaeger_endpoint: str | None = Field(default=None)
    sentry_dsn: SecretStr | None = Field(default=None)
    log_level: LogLevel = Field(default=LogLevel.INFO)
    structured_logging: bool = Field(default=True)


class SecurityConfig(BaseModel):
    """Security configuration."""

    secret_key: SecretStr | None = Field(default=None)
    jwt_secret: SecretStr | None = Field(default=None)
    jwt_expiry: int = Field(default=3600)  # seconds
    rate_limit_per_minute: int = Field(default=60)
    enable_cors: bool = Field(default=True)
    allowed_origins: list[str] = Field(default_factory=list)
    enable_csrf_protection: bool = Field(default=True)


class VolumeDefaults(BaseModel):
    """Default volume levels for different run contexts."""

    pr: int = Field(default=500)
    dev: int = Field(default=500)
    checkin: int = Field(default=500)


class ErrorHandlerConfig(BaseModel):
    """Error handling configuration for AI linting fixer and other components."""

    # Error handling settings
    enabled: bool = Field(default=True)
    log_errors: bool = Field(default=True)
    display_errors: bool = Field(default=True)
    export_errors: bool = Field(default=False)

    # Error categorization
    auto_categorize: bool = Field(default=True)
    severity_threshold: str = Field(default="LOW")

    # Recovery settings
    enable_recovery: bool = Field(default=True)
    max_retry_attempts: int = Field(default=3)
    retry_delay_seconds: float = Field(default=1.0)
    exponential_backoff: bool = Field(default=True)

    # Display settings
    use_colors: bool = Field(default=True)
    use_emojis: bool = Field(default=True)
    verbose_mode: bool = Field(default=False)

    # Export settings
    export_format: str = Field(default="json")
    export_directory: str = Field(default="./logs")
    auto_export: bool = Field(default=False)

    # Callback settings
    enable_callbacks: bool = Field(default=True)
    external_notifications: bool = Field(default=False)

    # Integration settings
    integrate_with_logging: bool = Field(default=True)
    integrate_with_metrics: bool = Field(default=True)
    integrate_with_workflows: bool = Field(default=True)


class ReportBuilderConfig(BaseModel):
    """Configuration for report builder summary and platform defaults."""

    # Volume thresholds for summary messages
    thorough_min_volume: int = Field(default=800)
    standard_min_volume: int = Field(default=400)

    # Summary messages by level
    summary_message_thorough: str = Field(default="Thorough analysis completed")
    summary_message_standard: str = Field(default="Standard analysis completed")
    summary_message_quick: str = Field(default="Quick analysis completed")

    # Label to use when platform is not detected
    unknown_platform_label: str = Field(default="unknown")

    # Simple repo-scanning rules to guess platform when unknown
    python_file_extensions: list[str] = Field(default_factory=lambda: [".py"])
    javascript_markers: list[str] = Field(
        default_factory=lambda: ["package.json"]
    )
    python_platform_name: str = Field(default="Python")
    javascript_platform_name: str = Field(default="JavaScript")


class AILintingConfig(BaseModel):
    """AI Linting Fixer specific configuration."""

    # Core settings
    enabled: bool = Field(default=True)
    default_provider: str = Field(default="openai")
    default_model: str = Field(default="gpt-4")

    # Processing settings
    max_workers: int = Field(default=4)
    max_fixes_per_run: int = Field(default=10)
    timeout_seconds: int = Field(default=300)

    # Fix types
    default_fix_types: list[str] = Field(
        default_factory=lambda: ["E501", "F401", "F841", "E722", "B001"]
    )

    # Quality settings
    confidence_threshold: float = Field(default=0.7)
    syntax_validation: bool = Field(default=True)
    create_backups: bool = Field(default=True)

    # Error handling integration
    error_handler: ErrorHandlerConfig = Field(default_factory=ErrorHandlerConfig)

    # Performance settings
    enable_metrics: bool = Field(default=True)
    enable_database_logging: bool = Field(default=True)
    enable_orchestration: bool = Field(default=False)


class AutoPRSettings(BaseSettings):
    """
    Main settings class for AutoPR Engine.

    This class combines all configuration sections and provides
    environment-specific loading, validation, and management.
    """

    # Environment and basic settings
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=False)
    version: str = Field(default="1.0.0")

    # Configuration sections
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    ai_linting: AILintingConfig = Field(default_factory=AILintingConfig)
    volume_defaults: VolumeDefaults = Field(default_factory=VolumeDefaults)
    report_builder: ReportBuilderConfig = Field(default_factory=ReportBuilderConfig)

    # Custom settings for extensions
    custom: dict[str, Any] = Field(default_factory=dict)

    # Pydantic V2 configuration using SettingsConfigDict
    if _PYDANTIC_V2 and SettingsConfigDict:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            validate_assignment=True,
            extra="allow",  # Allow additional fields for custom settings
            env_prefix="",  # No prefix for top-level settings
        )
    else:
        # Pydantic V1 fallback using class Config
        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False
            validate_assignment = True
            extra = "allow"

    def __init__(self, **kwargs):
        """Initialize settings with environment-specific overrides."""
        super().__init__(**kwargs)
        self._load_environment_specific_config()
        self._load_custom_config()

    def _load_environment_specific_config(self) -> None:
        """Load environment-specific configuration overrides."""
        config_dir = Path(__file__).parent / "environments"
        env_config_file = config_dir / f"{self.environment.value}.yaml"

        if env_config_file.exists():
            env_config = self._load_yaml_config(env_config_file)
            if env_config:
                self._apply_config_overrides(env_config)

    def _get_config_file_paths(self) -> list[Path]:
        """
        Get list of potential configuration file paths in priority order.
        
        Returns:
            List of Path objects to check for configuration files
        """
        return [
            Path.cwd() / "autopr.yaml",
            Path.cwd() / "autopr.yml",
            Path.cwd() / ".autopr.yaml",
            Path.cwd() / ".autopr.yml",
            Path.home() / ".autopr.yaml",
            Path.home() / ".autopr.yml",
        ]

    def _load_yaml_config(self, config_path: Path) -> dict[str, Any] | None:
        """
        Load YAML configuration from a file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Parsed configuration dictionary or None if loading fails
        """
        try:
            with open(config_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logging.warning(f"Failed to load config from {config_path}: {e}")
            return None

    def _load_custom_config(self) -> None:
        """Load custom configuration from various sources."""
        config_paths = self._get_config_file_paths()

        for config_path in config_paths:
            if config_path.exists():
                custom_config = self._load_yaml_config(config_path)
                if custom_config:
                    self._apply_config_overrides(custom_config)
                    break

    def _apply_config_overrides(self, overrides: dict[str, Any]) -> None:
        """Apply configuration overrides."""
        for key, value in overrides.items():
            if hasattr(self, key):
                if isinstance(getattr(self, key), BaseModel):
                    # Handle nested configuration objects
                    current_config = getattr(self, key)
                    if isinstance(value, dict):
                        for nested_key, nested_value in value.items():
                            if hasattr(current_config, nested_key):
                                setattr(current_config, nested_key, nested_value)
                else:
                    setattr(self, key, value)
            else:
                # Store in custom settings
                self.custom[key] = value

    def validate_configuration(self) -> list[str]:
        """
        Validate the complete configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # GitHub validation
        if not self.github.token and not self.github.app_id:
            errors.append(
                "GitHub authentication required: provide either GITHUB_TOKEN or GITHUB_APP_ID"
            )

        # LLM validation
        llm_keys = [
            self.llm.openai_api_key,
            self.llm.anthropic_api_key,
            self.llm.mistral_api_key,
            self.llm.groq_api_key,
            self.llm.perplexity_api_key,
            self.llm.together_api_key,
        ]
        if not any(key for key in llm_keys):
            errors.append("At least one LLM provider API key is required")

        # Production-specific validations
        if self.environment == Environment.PRODUCTION:
            if not self.security.secret_key:
                errors.append("SECRET_KEY is required in production")
            if self.debug:
                errors.append("DEBUG should be False in production")
            if self.monitoring.log_level == LogLevel.DEBUG:
                errors.append("LOG_LEVEL should not be DEBUG in production")

        return errors

    def _get_provider_specific_config(self, provider: LLMProvider) -> dict[str, Any]:
        """
        Get provider-specific configuration using a pattern-based approach.
        
        Args:
            provider: LLM provider to get config for
            
        Returns:
            Dictionary with provider-specific configuration
        """
        provider_name = provider.value.lower()
        
        return {
            "api_key": getattr(self.llm, f"{provider_name}_api_key", None),
            "base_url": getattr(self.llm, f"{provider_name}_base_url", None),
            "default_model": getattr(self.llm, f"{provider_name}_default_model", None),
        }

    def get_provider_config(self, provider: LLMProvider) -> dict[str, Any]:
        """
        Get configuration for a specific LLM provider.
        
        Args:
            provider: LLM provider to get config for
            
        Returns:
            Dictionary with complete provider configuration including common settings
        """
        # Get provider-specific config using pattern-based approach
        config = self._get_provider_specific_config(provider)
        
        # Add common settings
        config.update(
            {
                "max_tokens": self.llm.max_tokens,
                "temperature": self.llm.temperature,
                "timeout": self.llm.timeout,
                "max_retries": self.llm.max_retries,
            }
        )

        return config

    def to_safe_dict(self) -> dict[str, Any]:
        """
        Convert settings to dictionary with sensitive data masked.

        Returns:
            Dictionary representation with secrets masked
        """

        def mask_secrets(obj):
            if isinstance(obj, SecretStr):
                return "***" if obj else None
            if isinstance(obj, BaseModel):
                return {k: mask_secrets(v) for k, v in obj.model_dump().items()}
            if isinstance(obj, dict):
                return {k: mask_secrets(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [mask_secrets(item) for item in obj]
            return obj

        return mask_secrets(self.model_dump())

    def reload(self) -> None:
        """Reload configuration from all sources."""
        self._load_environment_specific_config()
        self._load_custom_config()

    @classmethod
    def from_file(cls, config_path: str | Path) -> "AutoPRSettings":
        """
        Create settings instance from configuration file.

        Args:
            config_path: Path to configuration file

        Returns:
            AutoPRSettings instance
        """
        config_path = Path(config_path)
        if not config_path.exists():
            msg = f"Configuration file not found: {config_path}"
            raise FileNotFoundError(msg)

        with open(config_path, encoding="utf-8") as f:
            if config_path.suffix.lower() in {".yaml", ".yml"}:
                config_data = yaml.safe_load(f)
            elif config_path.suffix.lower() == ".json":
                config_data = json.load(f)
            else:
                msg = f"Unsupported configuration file format: {config_path.suffix}"
                raise ValueError(msg)

        return cls(**config_data)


# Global settings instance
_settings: AutoPRSettings | None = None


def get_settings() -> AutoPRSettings:
    """
    Get the global settings instance.

    Returns:
        AutoPRSettings instance
    """
    global _settings
    if _settings is None:
        _settings = AutoPRSettings()
    return _settings


def reload_settings() -> AutoPRSettings:
    """
    Reload the global settings instance.

    Returns:
        Reloaded AutoPRSettings instance
    """
    global _settings
    _settings = None
    return get_settings()


def set_settings(settings: AutoPRSettings) -> None:
    """
    Set the global settings instance.

    Args:
        settings: AutoPRSettings instance to set as global
    """
    global _settings
    _settings = settings
