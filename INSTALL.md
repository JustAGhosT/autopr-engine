# AutoPR Engine - Installation Guide

Choose the installation method that works best for you.

**Requirements:** Python 3.12+ (3.13 also supported)

## Quick Installation Options

| Method | Linux/macOS | Windows | Best For |
|--------|-------------|---------|----------|
| **One-liner** | `curl ... \| bash` | `irm ... \| iex` | Fastest setup |
| **pip** | `pip install codeflow-engine` | Same | Local development |
| **Docker** | `docker compose up -d` | Same | Production deployment |
| **GitHub Action** | Copy workflow file | Same | CI/CD integration |

---

## Option 1: One-Line Install (Recommended)

> **Security Note:** Piping scripts to bash is convenient but review scripts before running.
> You can inspect the script first: `curl -sSL https://raw.githubusercontent.com/JustAGhosT/codeflow-engine/main/install.sh | less`

```bash
# Standard installation
curl -sSL https://raw.githubusercontent.com/JustAGhosT/codeflow-engine/main/install.sh | bash

# Full installation with all features
curl -sSL https://raw.githubusercontent.com/JustAGhosT/codeflow-engine/main/install.sh | bash -s -- --full

# Development installation
curl -sSL https://raw.githubusercontent.com/JustAGhosT/codeflow-engine/main/install.sh | bash -s -- --dev
```

### Windows (PowerShell)

```powershell
# Standard installation
irm https://raw.githubusercontent.com/JustAGhosT/codeflow-engine/main/install.ps1 | iex

# Full installation
irm https://raw.githubusercontent.com/JustAGhosT/codeflow-engine/main/install.ps1 -OutFile install.ps1; .\install.ps1 -Full

# Development installation
irm https://raw.githubusercontent.com/JustAGhosT/codeflow-engine/main/install.ps1 -OutFile install.ps1; .\install.ps1 -Dev
```

---

## Option 2: pip Install (Recommended with Virtual Environment)

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1

# Basic installation
pip install codeflow-engine

# With all features
pip install "codeflow-engine[full]"

# Development mode (from cloned repo)
git clone https://github.com/JustAGhosT/codeflow-engine.git
cd codeflow-engine
pip install -e ".[dev]"
```

---

## Option 3: Using Make (from repo)

```bash
# Clone and install
git clone https://github.com/JustAGhosT/codeflow-engine.git
cd codeflow-engine

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
curl -sSL https://raw.githubusercontent.com/JustAGhosT/codeflow-engine/main/install.sh | bash -s -- --docker

# Or manually:
git clone https://github.com/JustAGhosT/codeflow-engine.git
cd codeflow-engine
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
      - run: pip install codeflow-engine
      - run: autopr analyze --repo ${{ github.repository }} --pr ${{ github.event.pull_request.number }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

### One-Command Setup

```bash
# From your repository root:
curl -sSL https://raw.githubusercontent.com/JustAGhosT/codeflow-engine/main/templates/quick-start/autopr-minimal.yml \
  -o .github/workflows/autopr.yml --create-dirs

# Or use make (if codeflow-engine is cloned):
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
pip install --user codeflow-engine
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
pip uninstall codeflow-engine

# Docker
docker-compose down -v

# Remove workflow
rm .github/workflows/autopr.yml
```
