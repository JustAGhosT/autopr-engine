# AutoPR Engine Agent Guide

## Build/Test/Lint Commands

- **Run all tests**: `pytest`
- **Single test file**: `pytest tests/unit/test_file.py`
- **Single test function**: `pytest tests/unit/test_file.py::test_function`
- **Tests with coverage**: `pytest --cov=autopr --cov-report=html`
- **Unit tests only**: `pytest tests/unit/`
- **Integration tests**: `pytest tests/integration/`
- **Volume control tests**: `python tests/unit/test_volume_control_clean.py`
- **Code formatting**: `black autopr tests` (check: `black --check --diff .`)
- **Import sorting**: `isort autopr tests` (check: `isort --check-only --diff .`)
- **Type checking**: `mypy autopr` (very permissive config)
- **Install dev deps**: `pip install -e ".[dev]"`

## Architecture

- **Main package**: `autopr/` - Core engine with actions, workflows, integrations, AI providers
- **Actions**: 50+ automation actions in `autopr/actions/` (PR analysis, issue creation, quality
  gates)
- **Workflows**: Pre-built workflow definitions in `autopr/workflows/`
- **Integrations**: External services (GitHub, Linear, Slack, AI providers) in
  `autopr/integrations/`
- **AI/LLM**: Multi-provider AI system in `autopr/ai/` (OpenAI, Anthropic, Mistral, Groq)
- **Quality System**: AI-powered code analysis and quality gates in `autopr/quality/`
- **Volume Control**: HiFi-style volume control system in `scripts/volume-control/` (dev & commit
  knobs)

## Code Style & Conventions

- **Python 3.13** required
- **Type hints**: Optional (mypy configured to ignore most errors)
- **Line length**: Effectively unlimited (flake8 disabled)
- **Error handling**: Use AutoPRException base class and subclasses
- **Imports**: Use absolute imports, organize by category (stdlib, 3rd party, local)
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Async/await**: Preferred for I/O operations
- **Pydantic**: Used for configuration and data models
- **Logging**: Structured logging with configurable JSON output

_Context improved by Giga AI, using cursorrules and windsurfrules development guidelines._
