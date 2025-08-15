#!/usr/bin/env python3
"""
Branch Protection Rules Update Helper

This script helps you update GitHub branch protection rules to match the current workflow status checks.
"""

import json
from pathlib import Path
from typing import Dict, List


class BranchProtectionHelper:
    """Helps update GitHub branch protection rules."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        
    def get_current_status_checks(self) -> Dict[str, List[str]]:
        """Get the current status checks that should be required."""
        return {
            "required_checks": [
                "CI / test (pull_request)",
                "Quality Feedback / quality-feedback (3.13) (pull_request)", 
                "Quality Feedback / security-feedback (pull_request)",
                "PR Checks / Essential Checks (pull_request)"
            ],
            "optional_checks": [
                "CI / setup (pull_request)",
                "CI / notify (pull_request)"
            ],
            "deprecated_checks": [
                "build",
                "e2e", 
                "performance",
                "quality",
                "test (3.8)",
                "test (3.9)",
                "test (3.10)",
                "test (3.11)",
                "test (3.12)"
            ]
        }
    
    def generate_instructions(self) -> str:
        """Generate step-by-step instructions for updating branch protection rules."""
        checks = self.get_current_status_checks()
        
        instructions = """# 🔧 Branch Protection Rules Update Instructions

## 📋 Current Status Check Names

### ✅ Required Checks (Add These):
"""
        
        for check in checks["required_checks"]:
            instructions += f"- `{check}`\n"
        
        instructions += """
### ❌ Deprecated Checks (Remove These):
"""
        
        for check in checks["deprecated_checks"]:
            instructions += f"- `{check}`\n"
        
        instructions += """
## 🚀 Step-by-Step Update Process

### 1. Navigate to Repository Settings
1. Go to your repository on GitHub
2. Click **Settings** tab
3. Click **Branches** in the left sidebar

### 2. Edit Branch Protection Rule
1. Find your protected branch (usually `main` or `develop`)
2. Click **Edit** on the branch protection rule

### 3. Update Status Checks
1. Scroll to **"Require status checks to pass before merging"**
2. **Remove** all deprecated checks listed above
3. **Add** all required checks listed above
4. Make sure **"Require branches to be up to date"** is checked

### 4. Save Changes
1. Click **Save changes**
2. Test with a new PR to verify everything works

## 🔍 Verification

After updating, your PR should show:
- ✅ All required checks passing
- ❌ No more "pending" checks
- 🚀 Ability to merge when all checks pass

## 🆘 Troubleshooting

If you still see issues:
1. **Clear browser cache** and refresh
2. **Wait 5-10 minutes** for GitHub to update
3. **Create a new PR** to test the changes
4. **Check workflow logs** if any checks are failing

## 📞 Need Help?

If you need assistance:
1. Check the workflow logs in the Actions tab
2. Verify all workflows are running successfully
3. Ensure the status check names match exactly (case-sensitive)
"""
        
        return instructions
    
    def generate_json_config(self) -> str:
        """Generate a JSON configuration for reference."""
        checks = self.get_current_status_checks()
        
        config = {
            "branch_protection": {
                "required_status_checks": checks["required_checks"],
                "optional_status_checks": checks["optional_checks"],
                "deprecated_checks": checks["deprecated_checks"],
                "settings": {
                    "require_status_checks": True,
                    "require_branches_to_be_up_to_date": True,
                    "dismiss_stale_reviews": True,
                    "require_review": True,
                    "required_approving_review_count": 1
                }
            }
        }
        
        return json.dumps(config, indent=2)
    
    def create_documentation_files(self) -> None:
        """Create documentation files for the branch protection update."""
        print("📝 Creating branch protection documentation...")
        
        # Create instructions file
        instructions_file = self.project_root / "docs" / "branch-protection-update.md"
        instructions_file.parent.mkdir(exist_ok=True)
        
        with open(instructions_file, 'w', encoding='utf-8') as f:
            f.write(self.generate_instructions())
        
        # Create JSON config file
        config_file = self.project_root / "docs" / "branch-protection-config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(self.generate_json_config())
        
        print(f"✅ Created: {instructions_file}")
        print(f"✅ Created: {config_file}")
    
    def show_current_checks(self) -> None:
        """Display current status checks."""
        checks = self.get_current_status_checks()
        
        print("🔍 Current Workflow Status Checks\n")
        
        print("✅ **Required Checks (Add to Branch Protection):**")
        for check in checks["required_checks"]:
            print(f"   - {check}")
        
        print("\n⚠️  **Optional Checks (Not Required):**")
        for check in checks["optional_checks"]:
            print(f"   - {check}")
        
        print("\n❌ **Deprecated Checks (Remove from Branch Protection):**")
        for check in checks["deprecated_checks"]:
            print(f"   - {check}")
    
    def validate_workflow_names(self) -> None:
        """Validate that workflow names match expected status checks."""
        print("🔍 Validating Workflow Names\n")
        
        workflow_files = [
            ".github/workflows/ci.yml",
            ".github/workflows/quality.yml", 
            ".github/workflows/pr-checks.yml",
            ".github/workflows/bg-fix.yml"
        ]
        
        all_valid = True
        
        for workflow_file in workflow_files:
            file_path = self.project_root / workflow_file
            if file_path.exists():
                print(f"✅ {workflow_file}")
            else:
                print(f"❌ {workflow_file} - Missing!")
                all_valid = False
        
        if all_valid:
            print("\n🎉 All workflow files exist!")
        else:
            print("\n⚠️  Some workflow files are missing!")


def main():
    parser = argparse.ArgumentParser(description="Branch Protection Rules Helper")
    parser.add_argument("command", choices=[
        "show", "docs", "validate", "config"
    ], help="Command to execute")
    
    args = parser.parse_args()
    
    helper = BranchProtectionHelper()
    
    if args.command == "show":
        helper.show_current_checks()
    elif args.command == "docs":
        helper.create_documentation_files()
    elif args.command == "validate":
        helper.validate_workflow_names()
    elif args.command == "config":
        print(helper.generate_json_config())


if __name__ == "__main__":
    import argparse
    main()
