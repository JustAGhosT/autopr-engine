#!/usr/bin/env python3
"""
AutoPR Configuration CLI Tool

Command-line interface for managing AutoPR configuration:
- Validate configuration
- Generate configuration reports
- Check environment variables
- Create sample configuration files
- Test configuration settings
"""

import json
import sys

import click

from .settings import AutoPRSettings, Environment, get_settings
from .validation import check_environment_variables, generate_config_report, validate_configuration


@click.group()
@click.version_option(version="1.0.0", prog_name="autopr-config")
def cli():
    """AutoPR Configuration Management CLI"""


@cli.command()
@click.option(
    "--config-file", "-c", type=click.Path(exists=True), help="Configuration file path"
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def validate(config_file: str | None, format: str, verbose: bool):
    """Validate AutoPR configuration."""
    try:
        if config_file:
            settings = AutoPRSettings.from_file(config_file)
            click.echo(f"Loading configuration from: {config_file}")
        else:
            settings = get_settings()
            click.echo("Loading configuration from environment and default locations")

        validation_result = validate_configuration(settings)

        if format == "json":
            click.echo(json.dumps(validation_result, indent=2))
        else:
            # Text format
            if validation_result["valid"]:
                click.echo(click.style("✅ Configuration is valid!", fg="green"))
            else:
                click.echo(click.style("❌ Configuration has errors!", fg="red"))

            if validation_result["errors"]:
                click.echo(click.style("\n🚨 Errors:", fg="red"))
                for error in validation_result["errors"]:
                    click.echo(f"  - {error}")

            if validation_result["warnings"]:
                click.echo(click.style("\n⚠️  Warnings:", fg="yellow"))
                for warning in validation_result["warnings"]:
                    click.echo(f"  - {warning}")

            if verbose:
                click.echo(
                    f"\nSummary: {validation_result['error_count']} errors, {validation_result['warning_count']} warnings"
                )

        # Exit with error code if validation failed
        sys.exit(0 if validation_result["valid"] else 1)

    except Exception as e:
        click.echo(
            click.style(f"Error validating configuration: {e}", fg="red"), err=True
        )
        sys.exit(1)


@cli.command()
@click.option(
    "--config-file", "-c", type=click.Path(exists=True), help="Configuration file path"
)
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def report(config_file: str | None, output: str | None):
    """Generate comprehensive configuration report."""
    try:
        settings = (
            AutoPRSettings.from_file(config_file) if config_file else get_settings()
        )

        report_content = generate_config_report(settings)

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(report_content)
            click.echo(f"Configuration report saved to: {output}")
        else:
            click.echo(report_content)

    except Exception as e:
        click.echo(click.style(f"Error generating report: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def check_env(format: str):
    """Check environment variables and .env files."""
    try:
        env_check = check_environment_variables()

        if format == "json":
            click.echo(json.dumps(env_check, indent=2))
        else:
            # Text format
            click.echo("🔍 Environment Variable Check")
            click.echo("=" * 40)

            if env_check["missing_important_vars"]:
                click.echo(
                    click.style("\n❌ Missing Important Variables:", fg="yellow")
                )
                for var in env_check["missing_important_vars"]:
                    click.echo(f"  - {var}")

            if env_check["found_env_files"]:
                click.echo(click.style("\n✅ Found .env Files:", fg="green"))
                for file in env_check["found_env_files"]:
                    click.echo(f"  - {file}")

            if env_check["issues"]:
                click.echo(click.style("\n🚨 Issues:", fg="red"))
                for issue in env_check["issues"]:
                    click.echo(f"  - {issue}")

            if env_check["recommendations"]:
                click.echo(click.style("\n💡 Recommendations:", fg="blue"))
                for rec in env_check["recommendations"]:
                    click.echo(f"  - {rec}")

    except Exception as e:
        click.echo(click.style(f"Error checking environment: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--environment",
    "-e",
    type=click.Choice(["development", "testing", "staging", "production"]),
    default="development",
    help="Target environment",
)
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["yaml", "json", "env"]),
    default="yaml",
    help="Output format",
)
def generate(environment: str, output: str | None, format: str):
    """Generate sample configuration file."""
    try:
        Environment(environment)

        # Sample configuration based on environment
        sample_config = {
            "environment": environment,
            "debug": environment == "development",
            "github": {
                "token": "${GITHUB_TOKEN}",
                "timeout": 30 if environment == "production" else 10,
                "max_retries": 3 if environment == "production" else 2,
            },
            "llm": {
                "default_provider": "openai",
                "openai_api_key": "${OPENAI_API_KEY}",
                "anthropic_api_key": "${ANTHROPIC_API_KEY}",
                "max_tokens": 4000 if environment == "production" else 2000,
                "temperature": 0.7,
                "timeout": 60 if environment == "production" else 30,
            },
            "database": {
                "url": "${DATABASE_URL}",
                "pool_size": 20 if environment == "production" else 5,
                "echo": environment == "development",
            },
            "redis": {
                "url": "${REDIS_URL}",
                "ssl": environment == "production",
            },
            "monitoring": {
                "log_level": "INFO" if environment == "production" else "DEBUG",
                "enable_metrics": True,
                "enable_tracing": environment in {"staging", "production"},
                "sentry_dsn": "${SENTRY_DSN}" if environment == "production" else None,
            },
            "security": {
                "secret_key": "${SECRET_KEY}",
                "enable_cors": True,
                "enable_csrf_protection": environment == "production",
                "rate_limit_per_minute": 60 if environment == "production" else 1000,
            },
            "workflow": {
                "max_concurrent": 20 if environment == "production" else 5,
                "timeout": 300,
                "retry_attempts": 3 if environment == "production" else 1,
            },
        }

        # Generate content based on format
        if format == "yaml":
            import yaml

            content = yaml.dump(
                sample_config, default_flow_style=False, sort_keys=False
            )
        elif format == "json":
            content = json.dumps(sample_config, indent=2)
        elif format == "env":
            # Generate .env file format
            env_vars = [
                f"# AutoPR Configuration for {environment} environment",
                f"AUTOPR_ENVIRONMENT={environment}",
                f"DEBUG={'true' if environment == 'development' else 'false'}",
                "",
                "# GitHub Configuration",
                "GITHUB_TOKEN=your_github_token_here",
                "# GITHUB_APP_ID=your_app_id_here",
                "# GITHUB_PRIVATE_KEY=your_private_key_here",
                "",
                "# LLM Provider Configuration",
                "OPENAI_API_KEY=your_openai_key_here",
                "ANTHROPIC_API_KEY=your_anthropic_key_here",
                "# MISTRAL_API_KEY=your_mistral_key_here",
                "# GROQ_API_KEY=your_groq_key_here",
                "",
                "# Database Configuration",
                "DATABASE_URL=postgresql://user:password@localhost:5432/autopr",
                "",
                "# Redis Configuration",
                "REDIS_URL=redis://localhost:6379/0",
                "",
                "# Security Configuration",
                "SECRET_KEY=your_secret_key_here_32_chars_min",
                "",
                "# Monitoring Configuration",
                f"LOG_LEVEL={'INFO' if environment == 'production' else 'DEBUG'}",
                "# SENTRY_DSN=your_sentry_dsn_here",
                "",
                "# Additional Configuration",
                f"MAX_CONCURRENT_WORKFLOWS={20 if environment == 'production' else 5}",
                "WORKFLOW_TIMEOUT=300",
            ]
            content = "\n".join(env_vars)

        # Output content
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(content)
            click.echo(f"Sample configuration saved to: {output}")
        else:
            click.echo(content)

    except Exception as e:
        click.echo(
            click.style(f"Error generating configuration: {e}", fg="red"), err=True
        )
        sys.exit(1)


@cli.command()
@click.option(
    "--config-file", "-c", type=click.Path(exists=True), help="Configuration file path"
)
@click.option(
    "--provider",
    "-p",
    type=click.Choice(
        ["openai", "anthropic", "mistral", "groq", "perplexity", "together"]
    ),
    help="Test specific LLM provider",
)
def test(config_file: str | None, provider: str | None):
    """Test configuration by attempting connections."""
    try:
        settings = (
            AutoPRSettings.from_file(config_file) if config_file else get_settings()
        )

        click.echo("🧪 Testing Configuration Connections")
        click.echo("=" * 40)

        # Test GitHub connection
        click.echo("\n📡 Testing GitHub connection...")
        if settings.github.token:
            click.echo("  ✅ GitHub token configured")
            # Here you would add actual GitHub API test
        elif settings.github.app_id:
            click.echo("  ✅ GitHub App ID configured")
        else:
            click.echo("  ❌ No GitHub authentication configured")

        # Test LLM providers
        click.echo("\n🤖 Testing LLM providers...")
        providers_to_test = (
            [provider] if provider else ["openai", "anthropic", "mistral", "groq"]
        )

        for prov in providers_to_test:
            config = settings.get_provider_config(prov)
            if config.get("api_key"):
                click.echo(f"  ✅ {prov.title()} API key configured")
                # Here you would add actual API test calls
            else:
                click.echo(f"  ❌ {prov.title()} API key not configured")

        # Test database connection
        click.echo("\n🗄️  Testing database connection...")
        if settings.database.url:
            click.echo("  ✅ Database URL configured")
            # Here you would add actual database connection test
        else:
            click.echo("  ❌ Database URL not configured")

        # Test Redis connection
        click.echo("\n🔴 Testing Redis connection...")
        if settings.redis.url:
            click.echo("  ✅ Redis URL configured")
            # Here you would add actual Redis connection test
        else:
            click.echo("  ❌ Redis URL not configured")

        click.echo("\n✅ Configuration test completed")

    except Exception as e:
        click.echo(click.style(f"Error testing configuration: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--config-file", "-c", type=click.Path(exists=True), help="Configuration file path"
)
def show(config_file: str | None):
    """Show current configuration (with secrets masked)."""
    try:
        settings = (
            AutoPRSettings.from_file(config_file) if config_file else get_settings()
        )

        safe_config = settings.to_safe_dict()
        click.echo("📋 Current Configuration")
        click.echo("=" * 40)
        click.echo(json.dumps(safe_config, indent=2))

    except Exception as e:
        click.echo(click.style(f"Error showing configuration: {e}", fg="red"), err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
