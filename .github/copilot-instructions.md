# GitHub Copilot Workspace Instructions

This document provides guidance for GitHub Copilot when working with the AutoPR Engine repository.

## Project Overview

AutoPR Engine is a comprehensive AI-powered automation platform for GitHub pull request workflows. It provides intelligent analysis, automated issue creation, and multi-agent collaboration for code review and quality assurance.

## Architecture

### Core Components

- **AI-Powered PR Analysis**: Multi-agent review system with platform detection
- **Workflow Engine**: Volume-aware orchestration (0-1000 scale)
- **Integration Hub**: Slack, Linear, GitHub Issues, Jira support
- **Quality System**: Multi-stage quality gates and validation
- **Database Layer**: SQLAlchemy with async support, PostgreSQL backend
- **Security**: Multi-tiered permissions, information leakage prevention

### Technology Stack

- **Language**: Python 3.12+
- **Framework**: FastAPI, Flask-SocketIO
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Testing**: pytest, pytest-asyncio
- **AI/LLM**: OpenAI, Anthropic, Mistral, Groq
- **Package Manager**: Poetry

## Coding Guidelines

### General Principles

1. **Minimal Changes**: Make the smallest possible modifications to achieve the goal
2. **No Placeholders**: Always include complete, functional code
3. **Test Coverage**: Add tests for new functionality
4. **Type Hints**: Use type hints for all functions
5. **Error Handling**: Use custom exception classes from `autopr.exceptions`

### Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings for public APIs
- Keep functions focused and single-purpose
- Use async/await patterns where appropriate

### Security

- **Never expose sensitive data** in error messages (use `sanitize_error_message()`)
- **Validate all inputs** before processing
- **Use secure credential handling** (environment variables, secret managers)
- **Sanitize file paths, database credentials, API keys** in logs and responses
- See `autopr/exceptions.py` for security patterns

### Volume-Aware Development

The system uses a volume scale (0-1000) to control feature intensity:

- **0-199**: Ultra-fast mode (minimal checks)
- **200-399**: Fast mode (basic validation)
- **400-599**: Smart mode (standard checks)
- **600-799**: Comprehensive mode (thorough validation)
- **800-1000**: AI-enhanced mode (maximum scrutiny)

When adding features, consider volume-based behavior via `VolumeConfig`.

## File Organization

```
autopr-engine/
├── autopr/                    # Main source code
│   ├── actions/              # Action implementations
│   ├── ai/                   # AI integration layer
│   ├── database/             # Database models and config
│   ├── exceptions.py         # Custom exceptions with sanitization
│   ├── integrations/         # External service integrations
│   ├── quality/              # Quality analysis components
│   ├── security/             # Authorization and security
│   └── workflows/            # Workflow orchestration
├── tests/                     # Test suite
│   ├── actions/              # Action tests
│   ├── agents/               # Agent tests
│   ├── integration/          # Integration tests
│   └── unit/                 # Unit tests
├── configs/                   # Configuration files
├── docs/                      # Documentation
└── templates/                 # Template system
```

## Common Tasks

### Adding a New Action

1. Create action class in `autopr/actions/`
2. Inherit from `Action` base class
3. Implement `execute()` method
4. Register in action registry
5. Add tests in `tests/actions/`
6. Document in `docs/actions/`

### Adding Database Models

1. Create model in `autopr/database/models/`
2. Use SQLAlchemy declarative base
3. Add to Alembic migrations
4. Update database config if needed
5. Add model tests

### Adding Tests

1. Use pytest fixtures for setup/teardown
2. Mock external dependencies
3. Test both success and failure cases
4. Use descriptive test names
5. Aim for >80% coverage on new code

### Handling Exceptions

```python
from autopr.exceptions import (
    AutoPRException,
    WorkflowError,
    ValidationError,
    sanitize_error_message,
    handle_exception_safely,
)

# Use custom exceptions
raise WorkflowError("Workflow failed", workflow_name="my-workflow")

# Sanitize sensitive data
safe_message = sanitize_error_message(error_message)

# Handle exceptions safely
response = handle_exception_safely(error, context={"operation": "test"})
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_exception_sanitization.py

# Run with coverage
pytest --cov=autopr --cov-report=html

# Run verbose
pytest -v
```

### Test Structure

- **Unit tests**: Fast, isolated, no external dependencies
- **Integration tests**: Test component interactions
- **Skipped tests**: Use `@pytest.mark.skip` for incomplete features

## Dependencies

### Required Dependencies

Installed via `pyproject.toml`:
- pydantic, pydantic-settings (configuration)
- sqlalchemy (database ORM)
- aiohttp, httpx (HTTP clients)
- structlog, loguru (logging)
- openai, anthropic, mistralai, groq (LLM providers)

### Development Dependencies

- pytest, pytest-asyncio (testing)
- ruff (linting)
- mypy (type checking)
- bandit, safety (security scanning)

### Database Dependencies

The database dependencies are included in the `database` group. If using Poetry:
```bash
poetry install --with database
```

Or if installing directly with pip (non-Poetry environments):
```bash
pip install 'sqlalchemy[asyncio]>=2.0.0' alembic asyncpg psycopg2-binary
```

## Workflow Stages

The repository uses automated workflows:

1. **PR-Checks**: Fast validation on PR creation
2. **Quality Feedback**: Detailed analysis with reports
3. **CI**: Comprehensive checks (volume-aware)
4. **Background Fixer**: Automated maintenance

## MCP (Model Context Protocol) Integration

The repository supports MCP servers configured in `mcp-servers.json`:

- **filesystem**: Local file access
- **github**: GitHub API operations
- **postgres**: Database access
- **slack**: Team notifications
- **brave-search**: Web search
- **memory**: Knowledge graph
- **puppeteer**: Browser automation
- **sequential-thinking**: Complex reasoning

## Best Practices

### When Adding Features

1. Check existing patterns in similar components
2. Follow the volume-aware design
3. Add comprehensive tests
4. Update relevant documentation
5. Ensure security best practices
6. Consider performance implications

### When Fixing Bugs

1. Understand the root cause first
2. Add a regression test
3. Make minimal, targeted changes
4. Verify the fix doesn't break other functionality
5. Update error messages if needed

### When Refactoring

1. Maintain backward compatibility when possible
2. Update tests to match new structure
3. Keep commits focused and incremental
4. Document architectural changes

## Resources

- **Main Documentation**: `/docs/`
- **API Reference**: `/docs/api/`
- **Development Guide**: `/docs/development/`
- **Architecture Docs**: `/docs/architecture/`
- **Contributing Guide**: `CONTRIBUTING.md`
- **Changelog**: `CHANGELOG.md`

## Contact

- **Issues**: https://github.com/JustAGhosT/autopr-engine/issues
- **Discussions**: https://github.com/JustAGhosT/autopr-engine/discussions
- **Email**: support@justaghost.com
