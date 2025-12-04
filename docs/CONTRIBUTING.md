# Contributing to AutoPR Engine

Thank you for your interest in contributing to AutoPR Engine! We welcome contributions from the community.

## How to Contribute

### Development Workflow

AutoPR Engine uses a **volume-aware, multi-stage workflow system** for automated quality checks:

#### Workflow Stages

1. **PR-Checks** (Ultra-fast validation)
   - Runs immediately on PR creation/update
   - Pre-commit hooks on changed files only
   - Minimal tests for draft PRs
   - 10-minute timeout for quick feedback

2. **Quality Feedback** (Detailed PR feedback)
   - Pre-commit hooks on all files
   - Security scanning (Bandit + Safety)
   - Detailed PR comments with reports
   - Artifact uploads for security reports

3. **CI** (Comprehensive checks)
   - Volume-aware conditional execution
   - Full test suite with coverage
   - Type checking (MyPy)
   - Linting (Ruff) with volume-based rules
   - Security checks (volume ≥ 600)

4. **Background Fixer** (Maintenance)
   - Scheduled daily runs
   - Automated code fixing
   - Volume-aware fix aggressiveness

#### Volume System

The workflow system uses a volume-based approach (0-1000) to determine check intensity:

- **0-199:** Tests only
- **200-399:** Tests + relaxed linting
- **400-599:** Tests + linting + type checking
- **600+:** All checks including security

### Contributing Steps

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

**Note:** The workflow system will automatically run appropriate checks based on your PR and repository volume settings. See [Workflow Documentation](.github/workflows/README.md) for detailed information.

## Code Standards

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guidelines
- Add type hints for all functions
- Write comprehensive tests for new features
- Update documentation for user-facing changes

## Development Setup

```bash
# Clone repository
git clone https://github.com/JustAGhosT/autopr-engine.git
cd autopr-engine

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run with live reload
python -m autopr.server --reload
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=autopr --cov-report=html

# Run specific test categories
pytest tests/actions/      # Action tests
pytest tests/workflows/    # Workflow tests
pytest tests/integration/  # Integration tests

# Run performance tests
pytest tests/performance/ -v
```

## Questions?

If you have questions or need help, please:
- Open an issue on GitHub
- Join our community discussions
- Contact us at support@justaghost.com

We appreciate your contributions!
