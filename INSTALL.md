# AutoPR Engine - Installation Guide

Choose the installation method that works best for you:

## Quick Installation Options

| Method | Command | Best For |
|--------|---------|----------|
| **One-liner** | `curl -sSL https://raw.githubusercontent.com/JustAGhosT/autopr-engine/main/install.sh \| bash` | Fastest setup |
| **pip** | `pip install autopr-engine` | Local development |
| **Docker** | `docker-compose up -d` | Production deployment |
| **GitHub Action** | Copy workflow file | CI/CD integration |

---

## Option 1: One-Line Install (Recommended)

```bash
# Standard installation
curl -sSL https://raw.githubusercontent.com/JustAGhosT/autopr-engine/main/install.sh | bash

# Full installation with all features
curl -sSL https://raw.githubusercontent.com/JustAGhosT/autopr-engine/main/install.sh | bash -s -- --full

# Development installation
curl -sSL https://raw.githubusercontent.com/JustAGhosT/autopr-engine/main/install.sh | bash -s -- --dev
```

---

## Option 2: pip Install

```bash
# Basic installation
pip install autopr-engine

# With all features
pip install "autopr-engine[full]"

# Development mode (from cloned repo)
git clone https://github.com/JustAGhosT/autopr-engine.git
cd autopr-engine
pip install -e ".[dev]"
```

---

## Option 3: Using Make (from repo)

```bash
# Clone and install
git clone https://github.com/JustAGhosT/autopr-engine.git
cd autopr-engine

# Quick start (creates .env and installs)
make quickstart

# Or step by step:
make env          # Create .env file
make install      # Standard install
make install-dev  # Development install
make install-full # Full install
```

**Available make commands:**
```bash
make help         # Show all commands
make test         # Run tests
make lint         # Run linters
make server       # Start API server
make docker-up    # Start with Docker
```

---

## Option 4: Docker Installation

```bash
# Quick start
curl -sSL https://raw.githubusercontent.com/JustAGhosT/autopr-engine/main/install.sh | bash -s -- --docker

# Or manually:
git clone https://github.com/JustAGhosT/autopr-engine.git
cd autopr-engine
cp .env.example .env
# Edit .env with your API keys
docker-compose up -d
```

**Docker commands:**
```bash
docker-compose up -d      # Start services
docker-compose down       # Stop services
docker-compose logs -f    # View logs
docker-compose ps         # Check status
```

---

## Option 5: Add to Your GitHub Repository

### Minimal Setup (5 lines)

Create `.github/workflows/autopr.yml`:

```yaml
name: AutoPR
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install autopr-engine
      - run: autopr analyze --repo ${{ github.repository }} --pr ${{ github.event.pull_request.number }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

### One-Command Setup

```bash
# From your repository root:
curl -sSL https://raw.githubusercontent.com/JustAGhosT/autopr-engine/main/templates/quick-start/autopr-minimal.yml \
  -o .github/workflows/autopr.yml --create-dirs

# Or use make (if autopr-engine is cloned):
make setup-action
```

### Using Pre-built Templates

| Template | Description | Download |
|----------|-------------|----------|
| **Minimal** | Simplest setup, basic analysis | [autopr-minimal.yml](templates/quick-start/autopr-minimal.yml) |
| **Standard** | Recommended setup with comments | [autopr-workflow.yml](templates/quick-start/autopr-workflow.yml) |
| **Advanced** | Full features, multi-job | [autopr-advanced.yml](templates/quick-start/autopr-advanced.yml) |

---

## Configuration

### Required: Set Your API Keys

**For local installation:**
```bash
export GITHUB_TOKEN=ghp_your_token_here
export OPENAI_API_KEY=sk-your_key_here
```

**For GitHub Actions:**

1. Go to your repository Settings > Secrets and variables > Actions
2. Add these secrets:
   - `OPENAI_API_KEY` - Your OpenAI API key

Note: `GITHUB_TOKEN` is automatically provided by GitHub Actions.

### Optional: Additional Providers

```bash
# Anthropic (Claude)
export ANTHROPIC_API_KEY=sk-ant-your_key

# Mistral
export MISTRAL_API_KEY=your_mistral_key

# Groq
export GROQ_API_KEY=gsk_your_key
```

---

## Verify Installation

```bash
# Check CLI is installed
autopr --version

# Run help
autopr --help

# Test connection
autopr status
```

---

## Troubleshooting

### Python Version Error
```
Error: Python 3.12+ required
```
**Solution:** Install Python 3.12 or higher
```bash
# Ubuntu/Debian
sudo apt install python3.12

# macOS
brew install python@3.12

# Windows
winget install Python.Python.3.12
```

### Permission Denied
```
Error: Permission denied
```
**Solution:** Use pip with --user flag
```bash
pip install --user autopr-engine
```

### Missing API Key
```
Error: OPENAI_API_KEY not set
```
**Solution:** Set your API key
```bash
export OPENAI_API_KEY=sk-your_key_here
```

---

## Next Steps

1. **Local Development:** Run `autopr --help` to see available commands
2. **GitHub Integration:** Add the workflow file and set secrets
3. **Full Documentation:** See [README.md](README.md)
4. **Configuration Options:** See [.env.example](.env.example)

---

## Uninstall

```bash
# pip
pip uninstall autopr-engine

# Docker
docker-compose down -v

# Remove workflow
rm .github/workflows/autopr.yml
```
