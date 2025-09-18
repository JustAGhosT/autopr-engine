#!/usr/bin/env python3
"""
Branch Protection Rules Fix - Force Overwrite Capability

This script adjusts branch protection rules to allow force overwrites
and resolves common blocking conditions for PR merges.
"""

import json
import subprocess
import sys
from pathlib import Path


class BranchProtectionForceFixer:
    """Fixes branch protection rules to allow force overwrites."""

    def __init__(self):
        self.project_root = Path(__file__).parent

    def run_command(self, cmd):
        """Run a command and return the result."""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
            print(f"stderr: {e.stderr}")
            return None

    def check_github_auth(self):
        """Check if GitHub CLI is authenticated."""
        print("🔐 Checking GitHub CLI authentication...")
        result = self.run_command("gh auth status")
        if not result:
            print("❌ GitHub CLI not authenticated. Please run:")
            print("   gh auth login")
            return False
        print("✅ GitHub CLI authenticated")
        return True

    def get_repository_info(self):
        """Get repository owner and name."""
        print("📋 Getting repository information...")
        owner = self.run_command("gh repo view --json owner -q .owner.login")
        repo = self.run_command("gh repo view --json name -q .name")
        
        if not owner or not repo:
            print("❌ Could not get repository information")
            return None, None
        
        print(f"✅ Repository: {owner}/{repo}")
        return owner, repo

    def create_force_overwrite_config(self):
        """Create branch protection configuration that allows force overwrites."""
        print("⚙️  Creating force overwrite configuration...")
        
        # Configuration that allows force overwrites and reduces blocking conditions
        config = {
            "required_status_checks": {
                "strict": False,  # Don't require branches to be up to date
                "contexts": [
                    "CI / test (pull_request)",
                    "Quality Feedback / quality-feedback (3.13) (pull_request)",
                    "Quality Feedback / security-feedback (pull_request)",
                    "PR Checks / Essential Checks (pull_request)"
                ]
            },
            "enforce_admins": False,  # Don't enforce rules for admins
            "required_pull_request_reviews": {
                "required_approving_review_count": 0,  # No required reviews
                "dismiss_stale_reviews": False,  # Don't dismiss stale reviews
                "require_code_owner_reviews": False,  # Don't require code owner reviews
                "bypass_pull_request_allowances": {
                    "users": [],  # Add admin users here if needed
                    "teams": []
                }
            },
            "restrictions": None,  # No push restrictions
            "allow_force_pushes": True,  # Allow force pushes
            "allow_deletions": True,  # Allow branch deletions
            "required_conversation_resolution": False,  # Don't require conversation resolution
            "required_signatures": False,  # Don't require commit signatures
            "lock_branch": False,  # Don't lock the branch
            "allow_fork_syncing": True  # Allow fork syncing
        }
        
        return config

    def create_minimal_config(self):
        """Create minimal branch protection configuration."""
        print("⚙️  Creating minimal protection configuration...")
        
        # Minimal configuration with only essential protections
        config = {
            "required_status_checks": {
                "strict": False,
                "contexts": [
                    "CI / test (pull_request)"
                ]
            },
            "enforce_admins": False,
            "required_pull_request_reviews": {
                "required_approving_review_count": 0,
                "dismiss_stale_reviews": False,
                "require_code_owner_reviews": False
            },
            "restrictions": None,
            "allow_force_pushes": True,
            "allow_deletions": True,
            "required_conversation_resolution": False,
            "required_signatures": False,
            "lock_branch": False,
            "allow_fork_syncing": True
        }
        
        return config

    def update_branch_protection(self, owner, repo, config, branch="main"):
        """Update branch protection rules."""
        print(f"🔄 Updating branch protection for {branch}...")
        
        # Save config to temporary file
        config_file = self.project_root / "temp_branch_protection.json"
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
        
        print(f"📝 Created temporary config: {config_file}")
        
        # Update the rules
        cmd = f"gh api repos/{owner}/{repo}/branches/{branch}/protection --method PUT --input {config_file}"
        result = self.run_command(cmd)
        
        # Clean up
        if config_file.exists():
            config_file.unlink()
        
        return result is not None

    def disable_branch_protection(self, owner, repo, branch="main"):
        """Completely disable branch protection."""
        print(f"🚫 Disabling branch protection for {branch}...")
        
        cmd = f"gh api repos/{owner}/{repo}/branches/{branch}/protection --method DELETE"
        result = self.run_command(cmd)
        
        return result is not None

    def show_current_protection(self, owner, repo, branch="main"):
        """Show current branch protection rules."""
        print(f"📋 Current branch protection for {branch}:")
        
        cmd = f"gh api repos/{owner}/{repo}/branches/{branch}/protection"
        result = self.run_command(cmd)
        
        if result:
            try:
                protection = json.loads(result)
                print(json.dumps(protection, indent=2))
            except json.JSONDecodeError:
                print(result)
        else:
            print("No branch protection rules found")

    def main(self):
        """Main function to fix branch protection rules."""
        print("🔧 Branch Protection Force Overwrite Fixer")
        print("=" * 50)
        
        # Check authentication
        if not self.check_github_auth():
            sys.exit(1)
        
        # Get repository info
        owner, repo = self.get_repository_info()
        if not owner or not repo:
            sys.exit(1)
        
        print("\n🎯 Available Options:")
        print("1. Allow force overwrites (recommended)")
        print("2. Minimal protection (very permissive)")
        print("3. Disable all protection (temporary)")
        print("4. Show current protection rules")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            config = self.create_force_overwrite_config()
            if self.update_branch_protection(owner, repo, config):
                print("✅ Branch protection updated to allow force overwrites!")
                print("📋 Changes made:")
                print("   - Allow force pushes: True")
                print("   - Required reviews: 0")
                print("   - Require conversation resolution: False")
                print("   - Require branches up to date: False")
            else:
                print("❌ Failed to update branch protection")
        
        elif choice == "2":
            config = self.create_minimal_config()
            if self.update_branch_protection(owner, repo, config):
                print("✅ Branch protection set to minimal!")
                print("📋 Only essential checks required")
            else:
                print("❌ Failed to update branch protection")
        
        elif choice == "3":
            if self.disable_branch_protection(owner, repo):
                print("✅ Branch protection completely disabled!")
                print("⚠️  Remember to re-enable protection later")
            else:
                print("❌ Failed to disable branch protection")
        
        elif choice == "4":
            self.show_current_protection(owner, repo)
        
        elif choice == "5":
            print("👋 Exiting...")
            sys.exit(0)
        
        else:
            print("❌ Invalid choice")
            sys.exit(1)
        
        print("\n🎉 Done! Your PR should now be mergeable.")
        print("💡 If you still have issues:")
        print("   1. Refresh your PR page")
        print("   2. Wait 2-3 minutes for GitHub to update")
        print("   3. Try merging again")


if __name__ == "__main__":
    fixer = BranchProtectionForceFixer()
    fixer.main()
