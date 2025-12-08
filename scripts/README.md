# GitHub Environment Setup Scripts

This directory contains scripts to automatically create GitHub environments for staging and production deployments.

## 📁 Files

- `setup-github-environments.ps1` - PowerShell script (Windows/macOS/Linux)
- `setup-github-environments.sh` - Bash script (Linux/macOS/WSL)
- `README.md` - This documentation

## 🚀 Quick Start

### Prerequisites

1. **GitHub Personal Access Token** with the following permissions:
   - `repo` (Full control of private repositories)
   - `admin:org` (if creating environments for organization repositories)

2. **Repository Access**: You must have admin access to the repository

### PowerShell Script (Recommended for Windows)

```powershell
# Run with parameters
.\scripts\setup-github-environments.ps1 -Repository "your-org/codeflow-engine" -Token "ghp_your_token_here"

# Dry run to see what would be created
.\scripts\setup-github-environments.ps1 -Repository "your-org/codeflow-engine" -Token "ghp_your_token_here" -DryRun
```

### Bash Script (Linux/macOS/WSL)

```bash
# Make executable (Linux/macOS only)
chmod +x scripts/setup-github-environments.sh

# Run with parameters
./scripts/setup-github-environments.sh -r "your-org/codeflow-engine" -t "ghp_your_token_here"

# Dry run to see what would be created
./scripts/setup-github-environments.sh -r "your-org/codeflow-engine" -t "ghp_your_token_here" --dry-run
```

## 🔧 What the Scripts Create

### Staging Environment
- **Name**: `staging`
- **Protection**: Manual workflow dispatch required
- **Branch Policy**: Protected branches only
- **Variables**:
  - `DEPLOYMENT_ENV=staging`
  - `NODE_ENV=staging`
  - `LOG_LEVEL=debug`

### Production Environment
- **Name**: `production`
- **Protection**: Requires approval + 5-minute wait timer
- **Branch Policy**: Protected branches only
- **Variables**:
  - `DEPLOYMENT_ENV=production`
  - `NODE_ENV=production`
  - `LOG_LEVEL=info`

## 📋 Script Parameters

### PowerShell Script
| Parameter     | Description                                 | Required |
| ------------- | ------------------------------------------- | -------- |
| `-Repository` | GitHub repository in format "owner/repo"    | ✅ Yes    |
| `-Token`      | GitHub personal access token                | ✅ Yes    |
| `-DryRun`     | Show what would be created without creating | ❌ No     |

### Bash Script
| Parameter   | Short | Description                                 | Required |
| ----------- | ----- | ------------------------------------------- | -------- |
| `--repo`    | `-r`  | GitHub repository in format "owner/repo"    | ✅ Yes    |
| `--token`   | `-t`  | GitHub personal access token                | ✅ Yes    |
| `--dry-run` | `-d`  | Show what would be created without creating | ❌ No     |
| `--help`    | `-h`  | Show help message                           | ❌ No     |

## 🔐 Creating a GitHub Token

1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `admin:org` (if organization repository)
4. Copy the token (starts with `ghp_`)

## 🎯 Example Usage

### For AutoPR Engine Repository

```powershell
# Replace with your actual repository and token
.\scripts\setup-github-environments.ps1 -Repository "your-username/codeflow-engine" -Token "ghp_xxxxxxxxxxxxxxxxxxxx"
```

### For Organization Repository

```bash
# Replace with your organization and token
./scripts/setup-github-environments.sh -r "your-org/codeflow-engine" -t "ghp_xxxxxxxxxxxxxxxxxxxx"
```

## ✅ Verification

After running the script:

1. **Check GitHub Repository**:
   - Go to your repository → Settings → Environments
   - Verify `staging` and `production` environments exist

2. **Test CI/CD Pipeline**:
   - Push to a branch to trigger staging deployment
   - Merge to `main` to trigger production deployment

3. **Review Protection Rules**:
   - Staging: Manual workflow dispatch
   - Production: Requires approval + wait timer

## 🛠️ Troubleshooting

### Common Issues

1. **"Environment already exists"**
   - ✅ Normal - script handles this gracefully
   - Environments are updated if they exist

2. **"Invalid repository format"**
   - ❌ Use format: `owner/repository-name`
   - ✅ Correct: `microsoft/vscode`
   - ❌ Wrong: `microsoft-vscode` or `microsoft/vscode/`

3. **"Failed to create environment"**
   - Check token permissions
   - Verify repository access
   - Ensure you have admin rights

4. **"Token authentication failed"**
   - Verify token is correct
   - Check token hasn't expired
   - Ensure token has required scopes

### Getting Help

```bash
# Show help for bash script
./scripts/setup-github-environments.sh --help
```

```powershell
# Show help for PowerShell script
Get-Help .\scripts\setup-github-environments.ps1 -Detailed
```

## 🔄 Updating Environments

The scripts are idempotent - you can run them multiple times safely:

- Existing environments are detected and skipped
- New protection rules are added
- Environment variables are updated

## 📚 Related Documentation

- [GitHub Environments Documentation](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [GitHub REST API - Environments](https://docs.github.com/en/rest/reference/deployments#environments)
- [GitHub CLI Documentation](https://cli.github.com/)