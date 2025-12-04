# AutoPR Engine - Quick Start Templates

Ready-to-use GitHub Action workflow templates for adding AutoPR to your repository.

## Available Templates

| Template | Description | Use Case |
|----------|-------------|----------|
| [autopr-minimal.yml](autopr-minimal.yml) | ~20 lines, basic setup | Quick testing, simple repos |
| [autopr-workflow.yml](autopr-workflow.yml) | Standard setup with comments | Most repositories |
| [autopr-advanced.yml](autopr-advanced.yml) | Full-featured with multi-job | Enterprise, complex needs |

## Quick Setup

### Option 0: One-Line Setup (Easiest)

```bash
# Linux/macOS
./install.sh --action

# Windows PowerShell
.\install.ps1 -Action
```

### Option 1: Download and Copy

```bash
# Minimal (simplest)
curl -sSL https://raw.githubusercontent.com/JustAGhosT/autopr-engine/main/templates/quick-start/autopr-minimal.yml \
  -o .github/workflows/autopr.yml --create-dirs

# Standard (recommended)
curl -sSL https://raw.githubusercontent.com/JustAGhosT/autopr-engine/main/templates/quick-start/autopr-workflow.yml \
  -o .github/workflows/autopr.yml --create-dirs

# Advanced (full features)
curl -sSL https://raw.githubusercontent.com/JustAGhosT/autopr-engine/main/templates/quick-start/autopr-advanced.yml \
  -o .github/workflows/autopr.yml --create-dirs
```

### Option 2: Manual Copy

1. Choose a template from above
2. Copy the contents
3. Create `.github/workflows/autopr.yml` in your repository
4. Paste and commit

## Required Setup

After adding the workflow, you need to set up secrets:

1. Go to your repository on GitHub
2. Navigate to **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret**
4. Add:
   - Name: `OPENAI_API_KEY`
   - Value: Your OpenAI API key (starts with `sk-`)

**Note:** `GITHUB_TOKEN` is automatically provided by GitHub Actions.

## Optional: Additional AI Providers

For fallback support, add these optional secrets:

| Secret | Provider | Get Key From |
|--------|----------|--------------|
| `ANTHROPIC_API_KEY` | Anthropic (Claude) | [console.anthropic.com](https://console.anthropic.com) |
| `MISTRAL_API_KEY` | Mistral AI | [console.mistral.ai](https://console.mistral.ai) |
| `GROQ_API_KEY` | Groq | [console.groq.com](https://console.groq.com) |

## Template Comparison

### Minimal (`autopr-minimal.yml`)
- ~20 lines of YAML
- Triggers on PR open/sync
- Basic analysis only
- No comments posted

**Best for:** Quick testing, simple projects

### Standard (`autopr-workflow.yml`)
- ~80 lines of YAML
- Triggers on PR open/sync/reopen
- Posts analysis as PR comment
- Uploads analysis artifact

**Best for:** Most repositories

### Advanced (`autopr-advanced.yml`)
- ~200 lines of YAML
- Multiple trigger types
- PR comment commands (`/autopr analyze`)
- Risk assessment and blocking
- Automatic issue creation
- Detailed reporting

**Best for:** Enterprise, teams with complex workflows

## Customization

### Change Trigger Events

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened]
    # Add specific paths:
    paths:
      - 'src/**'
      - '*.py'
```

### Add Branch Filters

```yaml
on:
  pull_request:
    branches:
      - main
      - develop
```

### Use Different Python Version

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.13'  # or '3.12'
```

### Skip Draft PRs

```yaml
jobs:
  analyze:
    if: github.event.pull_request.draft == false
```

## Troubleshooting

### Workflow Not Running

1. Check the workflow file is in `.github/workflows/`
2. Ensure file has `.yml` or `.yaml` extension
3. Verify YAML syntax is valid
4. Check repository Actions are enabled (Settings > Actions)

### API Key Errors

```
Error: OPENAI_API_KEY not found
```

1. Verify secret is set in repository settings
2. Check secret name matches exactly (case-sensitive)
3. Ensure key is valid and has credits

### Permission Errors

Add permissions to your workflow:

```yaml
permissions:
  contents: read
  pull-requests: write
  issues: write
```

## Support

- [Full Documentation](../../README.md)
- [Installation Guide](../../INSTALL.md)
- [Report Issues](https://github.com/JustAGhosT/autopr-engine/issues)
