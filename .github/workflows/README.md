# GitHub Workflows

This directory contains the GitHub Actions workflows for AutoPR Engine.

## Workflow Architecture

AutoPR uses a **volume-aware, multi-stage workflow system** designed to provide fast feedback while
maintaining comprehensive quality checks.

### Workflow Overview

| Workflow             | Purpose                           | Triggers          | Timeout  | Key Features                                          |
| -------------------- | --------------------------------- | ----------------- | -------- | ----------------------------------------------------- |
| **CI**               | Volume-aware comprehensive checks | Push, PR, Manual  | Variable | Volume-based execution, MyPy, full test suite         |
| **Quality Feedback** | PR-specific quality feedback      | PR only           | 15 min   | Pre-commit hooks, detailed comments, security reports |
| **PR-Checks**        | Ultra-fast PR validation          | PR only           | 10 min   | Draft PR handling, minimal checks                     |
| **BG-Fix**           | Background auto-fixing            | Manual, Scheduled | 30 min   | Scheduled fixes, auto-fix queue                       |

## Workflow Details

### CI Workflow (`ci.yml`)

**Purpose:** Volume-aware comprehensive quality checks with conditional execution based on
repository volume settings.

**Key Features:**

- **Volume-based execution:** Different checks run based on volume level (0-1000)
- **Conditional jobs:** Tests (vol≥1), Lint (vol≥200), Typecheck (vol≥400), Security (vol≥600)
- **Manual dispatch:** Supports manual volume override
- **Full test suite:** Complete pytest coverage with Codecov integration

**Volume Thresholds:**

- **0-199:** Tests only
- **200-399:** Tests + Linting (relaxed rules)
- **400-599:** Tests + Linting + Type checking
- **600+:** All checks (including security)

### Quality Feedback Workflow (`quality.yml`)

**Purpose:** PR-specific quality feedback and detailed reporting.

**Key Features:**

- **Pre-commit hooks:** Runs all pre-commit validations
- **Detailed PR comments:** Provides comprehensive feedback
- **Security reports:** Bandit and Safety scanning with artifact uploads
- **Fork-aware:** Only runs on non-fork PRs

**Jobs:**

- `quality-feedback`: Pre-commit hooks and PR comments
- `security-feedback`: Security scanning and reporting

### PR-Checks Workflow (`pr-checks.yml`)

**Purpose:** Ultra-fast validation for PRs, especially draft PRs.

**Key Features:**

- **Fast execution:** 10-minute timeout for essential checks
- **Draft PR support:** Special handling for draft PRs
- **Changed files only:** Pre-commit runs only on modified files
- **Minimal tests:** Reduced test scope for speed

**Jobs:**

- `essential-checks`: Fast pre-commit and minimal tests
- `draft-validation`: Quick syntax check for draft PRs

### Background Fixer Workflow (`bg-fix.yml`)

**Purpose:** Automated background code fixing and maintenance.

**Key Features:**

- **Scheduled execution:** Daily runs at 3 AM UTC
- **Manual dispatch:** Supports volume override
- **Auto-fix queue:** Processes fixable issues in batches
- **Volume-aware:** Respects volume settings for fix aggressiveness

## Workflow Coordination

### Execution Order

1. **PR Created/Updated:**
   - `PR-Checks` runs immediately (fast validation)
   - `Quality Feedback` runs (detailed feedback)
   - `CI` runs (comprehensive checks)

2. **Push to Main/Develop:**
   - `CI` runs with full volume settings

3. **Manual/Scheduled:**
   - `BG-Fix` runs for maintenance

### Volume Integration

All workflows respect the AutoPR volume system:

```bash
# Repository variables (set in GitHub settings)
AUTOPR_VOLUME_PR=100      # PR volume
AUTOPR_VOLUME_CHECKIN=50  # Push volume
AUTOPR_VOLUME_DEV=200     # Development volume
```

### Status Badges

Add these badges to your README:

```markdown
![CI](https://github.com/owner/repo/workflows/CI/badge.svg)
![Quality](https://github.com/owner/repo/workflows/Quality%20Feedback/badge.svg)
![PR Checks](https://github.com/owner/repo/workflows/PR%20Checks/badge.svg)
```

## Troubleshooting

### Common Issues

**Workflow not running:**

- Check branch protection rules
- Verify workflow file syntax
- Check repository permissions

**Volume-based execution issues:**

- Verify repository variables are set
- Check volume calculation logic
- Review conditional job logic

**Pre-commit failures:**

- Run `pre-commit install` locally
- Check `.pre-commit-config.yaml` syntax
- Verify hook dependencies

**Codecov warnings ("Please install the 'codecov app svg image'"):**

- Install the Codecov GitHub App: https://github.com/apps/codecov
- Grant access to your repository in the app settings
- Ensure `CODECOV_TOKEN` secret is set in repository settings
- See `codecov.yml` in the repository root for configuration

### Debugging

**Enable debug logging:**

```yaml
env:
  ACTIONS_STEP_DEBUG: true
  ACTIONS_RUNNER_DEBUG: true
```

**Check workflow runs:**

- Go to Actions tab in GitHub
- Select specific workflow
- Review logs for errors

## Contributing

### Adding New Workflows

1. **Define purpose:** What unique value does this workflow provide?
2. **Check overlap:** Ensure no redundancy with existing workflows
3. **Add documentation:** Update this README
4. **Test thoroughly:** Verify triggers and conditions

### Modifying Existing Workflows

1. **Update documentation:** Reflect changes in this README
2. **Test changes:** Use workflow dispatch for testing
3. **Consider impact:** How do changes affect other workflows?

### Best Practices

- **Keep workflows focused:** Each workflow should have a single, clear purpose
- **Use volume awareness:** Leverage the volume system for conditional execution
- **Provide feedback:** Always give clear feedback to contributors
- **Handle failures gracefully:** Use `continue-on-error` and `if: always()` appropriately
- **Optimize for speed:** Minimize redundant work and optimize execution time

## Configuration

### Repository Variables

Set these in GitHub repository settings:

| Variable                | Description              | Default |
| ----------------------- | ------------------------ | ------- |
| `AUTOPR_VOLUME_PR`      | Volume for pull requests | 100     |
| `AUTOPR_VOLUME_CHECKIN` | Volume for pushes        | 50      |
| `AUTOPR_VOLUME_DEV`     | Volume for development   | 200     |

### Environment Variables

| Variable                  | Description               | Default |
| ------------------------- | ------------------------- | ------- |
| `PYTHON_VERSION`          | Python version to use     | 3.13    |
| `AUTOPR_PRECOMMIT_VOLUME` | Pre-commit volume         | 100     |
| `AUTOPR_BG_BATCH`         | Background fix batch size | 30      |

## Support

For workflow issues:

1. Check this documentation
2. Review workflow logs
3. Create an issue with workflow name and error details
4. Tag with `workflow` label
