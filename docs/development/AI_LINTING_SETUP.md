# AI Linting Setup Guide

## Overview

AI linting has been enabled for pre-commit but requires API keys to function. This guide will help
you set up the necessary configuration.

## Current Status

✅ **AI Linting Hook**: Enabled in pre-commit (changed from `manual` to `pre-commit` stage) ✅
**Tool Configuration**: Optimized for pre-commit with conservative limits ❌ **API Keys**: Not
configured (required for AI functionality) ✅ **Test File**: Created (`test_ai_lint.py`) for
verification

## Configuration Changes Made

### 1. Pre-commit Hook Configuration

```yaml
# In .pre-commit-config.yaml
- id: ai-lint-fixer
  name: AI Linting Fixer
  entry: python tools/ai_lint_fixer.py
  language: system
  types: [python]
  pass_filenames: false
  args:
    [--max-fixes=3, --fix-types=E501, F401, F841, --provider=azure_openai, --model=gpt-4.1, --quiet]
  stages: [pre-commit] # Now runs automatically on pre-commit
```

**Key Changes:**

- Changed `stages: [manual]` to `stages: [pre-commit]`
- Reduced `--max-fixes` from 5 to 3 (to limit API usage)
- Added `--quiet` flag for cleaner pre-commit output
- Focused on common issues: E501 (line length), F401 (unused imports), F841 (unused variables)

## Setup Steps

### Step 1: Get API Keys

You need either:

**Option A: Azure OpenAI**

```powershell
# Set environment variable
$env:AZURE_OPENAI_API_KEY = "your-azure-openai-api-key-here"
$env:AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"
```

**Option B: OpenAI**

```powershell
# Set environment variable
$env:OPENAI_API_KEY = "your-openai-api-key-here"
```

### Step 2: Test the Setup

```powershell
# Test with dry run
python tools/ai_lint_fixer.py test_ai_lint.py --dry-run --verbose

# Test actual fix
python tools/ai_lint_fixer.py test_ai_lint.py --max-fixes=2
```

### Step 3: Test Pre-commit

```powershell
# Test pre-commit with AI linting
pre-commit run ai-lint-fixer --all-files

# Or run all hooks
pre-commit run --all-files
```

## What AI Linting Will Fix

The current configuration will automatically fix:

- **E501**: Lines longer than 100 characters
- **F401**: Unused imports
- **F841**: Unused variables

## Performance & Cost Considerations

### Conservative Limits

- **Max fixes per run**: 3 (reduced from 5)
- **Targeted issue types**: Only the most common and safe fixes
- **Quiet mode**: Minimal output during pre-commit

### Cost Estimation

- **Typical cost**: ~$0.01-0.05 per pre-commit run
- **Monthly cost**: ~$1-5 for active development
- **Cost control**: Limited to 3 fixes per run

## Troubleshooting

### Common Issues

1. **API Key Errors**

   ```
   Error code: 401 - Access denied due to invalid subscription key
   ```

   **Solution**: Verify your API key is correct and has sufficient credits

1. **No Fixes Applied**

   ```
   Issues processed: 0, Issues fixed: 0
   ```

   **Solution**: Check if the specified fix types match available issues

1. **Pre-commit Hangs**

   **Solution**: The AI calls can take 5-15 seconds. This is normal.

### Debug Commands

```powershell
# Check API key status
python tools/ai_lint_fixer.py --verbose

# View database statistics
python tools/ai_lint_fixer.py --db-stats

# Search for specific fixes
python tools/ai_lint_fixer.py --search "import fixes"
```

## Disabling AI Linting (if needed)

If you want to disable AI linting temporarily:

1. **Option A: Change back to manual**

   ```yaml
   stages: [manual] # Only run when explicitly called
   ```

1. **Option B: Comment out the hook**

   ```yaml
   # - id: ai-lint-fixer
   #   name: AI Linting Fixer
   #   ...
   ```

1. **Option C: Skip for specific commits**

   ```bash
   git commit --no-verify
   ```

## Next Steps

1. **Get API Keys**: Obtain Azure OpenAI or OpenAI API keys
2. **Set Environment Variables**: Configure the API keys
3. **Test**: Run the test commands above
4. **Commit**: Try a commit to see AI linting in action

## Files Modified

- `.pre-commit-config.yaml`: Enabled AI linting for pre-commit
- `test_ai_lint.py`: Created test file with intentional linting issues
- `AI_LINTING_SETUP.md`: This setup guide

---

**Note**: AI linting is now enabled but requires valid API keys to function. The tool will
gracefully handle missing keys by skipping AI fixes while still running other pre-commit hooks.
