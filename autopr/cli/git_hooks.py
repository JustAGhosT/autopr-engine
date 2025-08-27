"""
Git Hooks Management for AutoPR

Provides functionality to install, manage, and execute git hooks
for automated quality checks and file operations.
"""

import logging
from pathlib import Path
import subprocess
import tempfile
from typing import Any


logger = logging.getLogger(__name__)


class GitHooksManager:
    """Manages git hooks for AutoPR automation."""

    def __init__(self, git_dir: str | None = None):
        self.git_dir = git_dir or self._find_git_dir()
        self.hooks_dir = self._resolve_hooks_dir() if self.git_dir else None

    def _resolve_hooks_dir(self) -> Path | None:
        """Resolve the hooks directory, honoring core.hooksPath and worktrees."""
        try:
            # 1) Respect core.hooksPath if set
            cfg = subprocess.run(
                ["git", "config", "--get", "core.hooksPath"],
                capture_output=True,
                text=True,
                check=False,
            )
            path = cfg.stdout.strip()
            if path:
                return Path(path).expanduser().resolve()

            # 2) Ask git for the hooks path (works with worktrees)
            gp = subprocess.run(
                ["git", "rev-parse", "--git-path", "hooks"],
                capture_output=True,
                text=True,
                check=True,
            )
            return Path(gp.stdout.strip()).resolve()
        except Exception:
            # 3) Fallback to <git_dir>/hooks
            return Path(self.git_dir).resolve() / "hooks" if self.git_dir else None

    def _find_git_dir(self) -> str | None:
        """Find the git directory for the current repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def install_hooks(self, config: dict[str, Any] | None = None) -> bool:
        """Install AutoPR git hooks."""
        if not self.hooks_dir:
            logger.error("Not in a git repository")
            return False

        try:
            # Create hooks directory if it doesn't exist
            self.hooks_dir.mkdir(parents=True, exist_ok=True)

            # Get enabled hooks from config
            config = config or {}
            enabled_hooks = config.get(
                "enabled_hooks", ["pre-commit", "post-commit", "commit-msg"]
            )

            # Map hook names to install functions
            hook_installers = {
                "pre-commit": self._install_pre_commit_hook,
                "post-commit": self._install_post_commit_hook,
                "commit-msg": self._install_commit_msg_hook,
            }

            # Install only enabled hooks
            installed_hooks = []
            for hook_name in enabled_hooks:
                if hook_name in hook_installers:
                    hook_installers[hook_name](config)
                    installed_hooks.append(hook_name)
                    logger.info(f"Installed {hook_name} hook")
                else:
                    logger.warning(f"Unknown hook type: {hook_name}")

            if installed_hooks:
                logger.info(
                    f"AutoPR git hooks installed successfully: {', '.join(installed_hooks)}"
                )
            else:
                logger.info("No hooks were installed (none enabled in configuration)")
            return True

        except Exception as e:
            logger.exception(f"Failed to install git hooks: {e}")
            return False

    def uninstall_hooks(self) -> bool:
        """Remove AutoPR git hooks."""
        if not self.hooks_dir:
            logger.error("Not in a git repository")
            return False

        try:
            hooks_to_remove = ["pre-commit", "post-commit", "commit-msg"]

            for hook_name in hooks_to_remove:
                hook_path = self.hooks_dir / hook_name
                if hook_path.exists():
                    hook_path.unlink()
                    logger.info(f"Removed {hook_name} hook")

            logger.info("AutoPR git hooks uninstalled successfully")
            return True

        except Exception as e:
            logger.exception(f"Failed to uninstall git hooks: {e}")
            return False

    def _install_pre_commit_hook(self, config: dict[str, Any] | None = None):
        """Install pre-commit hook for quality checks."""
        hook_content = self._generate_pre_commit_hook(config)
        hook_path = self.hooks_dir / "pre-commit"

        with open(hook_path, "w") as f:
            f.write(hook_content)

        # Make executable
        hook_path.chmod(0o755)

    def _install_post_commit_hook(self, config: dict[str, Any] | None = None):
        """Install post-commit hook for metrics collection."""
        hook_content = self._generate_post_commit_hook(config)
        hook_path = self.hooks_dir / "post-commit"

        with open(hook_path, "w") as f:
            f.write(hook_content)

        # Make executable
        hook_path.chmod(0o755)

    def _install_commit_msg_hook(self, config: dict[str, Any] | None = None):
        """Install commit-msg hook for commit message validation."""
        hook_content = self._generate_commit_msg_hook(config)
        hook_path = self.hooks_dir / "commit-msg"

        with open(hook_path, "w") as f:
            f.write(hook_content)

        # Make executable
        hook_path.chmod(0o755)

    def _generate_pre_commit_hook(self, config: dict[str, Any] | None = None) -> str:
        """Generate pre-commit hook content."""
        config = config or {}
        mode = config.get("quality_mode", "fast")
        auto_fix = config.get("auto_fix", False)

        return f"""#!/bin/bash
# AutoPR Pre-commit Hook
# Runs quality checks on staged files before commit

set -e

echo "🔍 AutoPR: Running pre-commit quality checks..."

# Get staged files using NUL-separated output for safety
files_array=()
while IFS= read -r -d '' file; do
    # Only process relevant file types
    if [[ "$file" =~ \\.(py|js|ts|jsx|tsx)$ ]]; then
        files_array+=("$file")
    fi
done < <(git diff --cached --name-only --diff-filter=ACM -z)

if [ ${{#files_array[@]}} -eq 0 ]; then
    echo "✅ No relevant files staged for commit"
    exit 0
fi

echo "📁 Processing ${{#files_array[@]}} staged files..."

# Run AutoPR quality check with proper array expansion
if python -m autopr.cli.main check \\
    --mode {mode} \\
    --files "${{files_array[@]}}" \\
    --format json \\
    --output /tmp/autopr_precommit_result.json; then

    echo "✅ AutoPR quality checks passed"

    # Apply auto-fixes if enabled
    if [ "{str(auto_fix).lower()}" = "true" ]; then
        echo "🔧 AutoPR: Applying automatic fixes..."
        if python -m autopr.cli.main check \\
            --mode {mode} \\
            --files "${{files_array[@]}}" \\
            --auto-fix; then

            # Re-stage fixed files using proper array expansion
            git add -- "${{files_array[@]}}"
            echo "✅ Auto-fixes applied and staged"
        else
            echo "⚠️  Auto-fix failed, but continuing with commit"
        fi
    fi

    exit 0
else
    echo "❌ AutoPR quality checks failed"
    echo "Please fix the issues before committing"
    exit 1
fi
"""

    def _generate_post_commit_hook(self, config: dict[str, Any] | None = None) -> str:
        """Generate post-commit hook content."""
        return """#!/bin/bash
# AutoPR Post-commit Hook
# Collects metrics and updates history after commit

set -e

echo "📊 AutoPR: Collecting post-commit metrics..."

# Get commit hash
COMMIT_HASH=$(git rev-parse HEAD)
COMMIT_MESSAGE=$(git log -1 --pretty=format:%s)

# Run metrics collection (non-blocking)
python -m autopr.cli.main metrics collect \\
    --commit-hash "$COMMIT_HASH" \\
    --commit-message "$COMMIT_MESSAGE" \\
    --background &

echo "✅ AutoPR post-commit metrics collection started"
"""

    def _generate_commit_msg_hook(self, config: dict[str, Any] | None = None) -> str:
        """Generate commit-msg hook content."""
        return """#!/bin/bash
# AutoPR Commit Message Hook
# Validates commit message format and content

set -e

COMMIT_MSG_FILE=$1
COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")

echo "📝 AutoPR: Validating commit message..."

# Basic commit message validation
COMMIT_PATTERN="^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\\(.+\\))?: .+"
if [[ ! "$COMMIT_MSG" =~ $COMMIT_PATTERN ]]; then
    echo "❌ Invalid commit message format"
    echo "Expected format: <type>(<scope>): <description>"
    echo "Types: feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert"
    echo "Example: feat(quality): add AI-enhanced file splitter"
    exit 1
fi

# Check message length
if [ ${#COMMIT_MSG} -gt 72 ]; then
    echo "⚠️  Commit message is longer than 72 characters"
    echo "Consider using a shorter description"
fi

echo "✅ Commit message validation passed"
"""

    def get_hooks_status(self) -> dict[str, bool]:
        """Get status of installed hooks."""
        if not self.hooks_dir:
            return {}

        hooks = ["pre-commit", "post-commit", "commit-msg"]
        status = {}

        for hook in hooks:
            hook_path = self.hooks_dir / hook
            status[hook] = hook_path.exists() and hook_path.stat().st_mode & 0o111 != 0

        return status

    def test_hooks(self) -> dict[str, bool]:
        """Test installed hooks."""
        status = self.get_hooks_status()
        results = {}

        for hook_name, installed in status.items():
            if installed:
                try:
                    # Test hook execution (dry run)
                    result = self._test_hook(hook_name)
                    results[hook_name] = result
                except Exception as e:
                    logger.exception(f"Failed to test {hook_name} hook: {e}")
                    results[hook_name] = False
            else:
                results[hook_name] = False

        return results

    def _test_hook(self, hook_name: str) -> bool:
        """Test a specific hook."""
        hook_path = self.hooks_dir / hook_name

        if not hook_path.exists():
            return False

        try:
            # Create temporary test environment
            with tempfile.TemporaryDirectory() as temp_dir:
                # Test pre-commit hook with proper git setup
                if hook_name == "pre-commit":
                    # Initialize git repository in temp directory
                    subprocess.run(
                        ["git", "init"],
                        cwd=temp_dir,
                        capture_output=True,
                        check=True,
                    )

                    # Set git user config
                    subprocess.run(
                        ["git", "config", "user.name", "AutoPR Test"],
                        cwd=temp_dir,
                        capture_output=True,
                        check=True,
                    )
                    subprocess.run(
                        ["git", "config", "user.email", "test@autopr.local"],
                        cwd=temp_dir,
                        capture_output=True,
                        check=True,
                    )

                    # Create a test file and stage it
                    test_file = Path(temp_dir) / "test.py"
                    test_file.write_text("# Test file for AutoPR pre-commit hook\n")

                    subprocess.run(
                        ["git", "add", str(test_file)],
                        cwd=temp_dir,
                        capture_output=True,
                        check=True,
                    )

                    # Run the pre-commit hook in the git repository
                    result = subprocess.run(
                        [str(hook_path)],
                        cwd=temp_dir,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    return result.returncode == 0

                # For other hooks, just check if they're executable
                return hook_path.stat().st_mode & 0o111 != 0

        except Exception as e:
            logger.exception(f"Error testing {hook_name} hook: {e}")
            return False


def install_hooks(config_path: str | None = None) -> bool:
    """Install AutoPR git hooks."""
    config = _load_config(config_path) if config_path else {}
    manager = GitHooksManager()
    return manager.install_hooks(config)


def uninstall_hooks() -> bool:
    """Uninstall AutoPR git hooks."""
    manager = GitHooksManager()
    return manager.uninstall_hooks()


def get_hooks_status() -> dict[str, bool]:
    """Get status of installed hooks."""
    manager = GitHooksManager()
    return manager.get_hooks_status()


def test_hooks() -> dict[str, bool]:
    """Test installed hooks."""
    manager = GitHooksManager()
    return manager.test_hooks()


def _load_config(config_path: str) -> dict[str, Any]:
    """Load configuration from file."""
    try:
        import json

        with open(config_path) as f:
            return json.load(f)
    except Exception as e:
        logger.exception(f"Failed to load config from {config_path}: {e}")
        return {}


def create_hook_config(
    quality_mode: str = "fast",
    auto_fix: bool = False,
    max_file_size: int = 10000,
    enabled_hooks: list[str] | None = None,
) -> dict[str, Any]:
    """Create a hook configuration."""
    if enabled_hooks is None:
        enabled_hooks = ["pre-commit", "post-commit", "commit-msg"]

    return {
        "quality_mode": quality_mode,
        "auto_fix": auto_fix,
        "max_file_size": max_file_size,
        "enabled_hooks": enabled_hooks,
        "notifications": {
            "show_success": True,
            "show_warnings": True,
            "show_errors": True,
        },
    }


def save_hook_config(config: dict[str, Any], config_path: str) -> bool:
    """Save hook configuration to file."""
    try:
        import json

        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logger.exception(f"Failed to save config to {config_path}: {e}")
        return False
