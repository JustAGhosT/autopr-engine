#!/usr/bin/env python3
"""
Simple script to update branch protection rules.
Run this when you have proper GitHub CLI authentication.
"""

import subprocess
import sys


def run_command(cmd):
    """Run a command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"stderr: {e.stderr}")
        return None

def main():
    print("🔧 Updating branch protection rules...")
    
    # Check if gh is authenticated
    if not run_command("gh auth status"):
        print("❌ Please authenticate with GitHub CLI first:")
        print("   gh auth login")
        sys.exit(1)
    
    # Get repository info
    owner = run_command("gh repo view --json owner -q .owner.login")
    repo = run_command("gh repo view --json name -q .name")
    
    if not owner or not repo:
        print("❌ Could not get repository information")
        sys.exit(1)
    
    print(f"Repository: {owner}/{repo}")
    
    # Create the branch protection rule
    protection_rule = {
        "required_status_checks": {
            "strict": True,
            "contexts": [
                "quality-assurance",
                "testing", 
                "security",
                "performance",
                "build",
                "documentation"
            ]
        },
        "enforce_admins": False,
        "required_pull_request_reviews": {
            "required_approving_review_count": 1,
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": False
        },
        "restrictions": None,
        "allow_force_pushes": False,
        "allow_deletions": False
    }
    
    # Save to file
    import json
    with open("branch_protection.json", "w") as f:
        json.dump(protection_rule, f, indent=2)
    
    print("📝 Created branch_protection.json")
    print("🔄 Updating branch protection rules...")
    
    # Update the rules
    cmd = f"gh api repos/{owner}/{repo}/branches/main/protection --method PUT --input branch_protection.json"
    result = run_command(cmd)
    
    if result is not None:
        print("✅ Branch protection rules updated successfully!")
        print("📋 Required status checks:")
        for check in protection_rule["required_status_checks"]["contexts"]:
            print(f"   - {check}")
    else:
        print("❌ Failed to update branch protection rules")
        print("💡 You may need to:")
        print("   1. Check your GitHub CLI authentication")
        print("   2. Ensure you have admin permissions on the repository")
        print("   3. Try updating manually via GitHub web interface")
    
    # Clean up
    import os
    if os.path.exists("branch_protection.json"):
        os.remove("branch_protection.json")

if __name__ == "__main__":
    main()
