# Fix Branch Protection Rules - Manual Steps

## Current Issue
The branch protection rules are expecting status checks that don't match our actual workflow:
- Expecting: `test (3.8)`, `test (3.9)`, `test (3.10)`, `test (3.11)`, `test (3.12)`
- Our workflow has: `quality-assurance`, `testing`, `security`, `performance`, `build`, `documentation`

## Solution Options

### Option 1: Update Branch Protection Rules (Recommended)
Update the branch protection rules to match our actual workflow:

1. **Go to GitHub Repository Settings**:
   - Navigate to: https://github.com/JustAGhosT/codeflow-engine/settings/branches
   - Find the branch protection rule for `main` (or your target branch)

2. **Update Required Status Checks**:
   - Remove: `test (3.8)`, `test (3.9)`, `test (3.10)`, `test (3.11)`, `test (3.12)`
   - Add: `quality-assurance`, `testing`, `security`, `performance`, `build`, `documentation`
   - Keep: `test`, `e2e`, `performance`, `quality` (if they exist)

3. **Save Changes**

### Option 2: Use GitHub CLI (When Authenticated)
If you have proper GitHub CLI authentication:

```bash
# Check current rules
gh api repos/JustAGhosT/codeflow-engine/branches/main/protection

# Update rules (replace with your actual requirements)
gh api repos/JustAGhosT/codeflow-engine/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["quality-assurance","testing","security","performance","build","documentation"]}'
```

### Option 3: Remove Job Aliases (Alternative)
If you prefer to keep the current branch protection rules, we can remove the job aliases we just added and keep the current workflow as-is.

## Recommended Status Checks for Our Workflow

Based on our `ci-cd-pipeline.yml`, the essential status checks should be:

1. **quality-assurance** - Quality analysis and linting
2. **testing** - Unit and integration tests  
3. **security** - Security scanning
4. **performance** - Performance testing
5. **build** - Package building
6. **documentation** - Documentation generation

## Next Steps

1. Choose one of the options above
2. Update the branch protection rules
3. Test by creating a new PR or pushing to the branch
4. Verify that all status checks pass

The "Expected — Waiting for status to be reported" issue should be resolved once the branch protection rules match our actual workflow.
