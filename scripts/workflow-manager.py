#!/usr/bin/env python3
"""
Workflow Manager for AutoPR Engine

This script helps developers understand and interact with the workflow system.
"""

import argparse
import sys
from pathlib import Path


class WorkflowManager:
    """Manages AutoPR Engine workflows and provides helpful utilities."""
    
    WORKFLOWS = {
        "ci": {
            "file": ".github/workflows/ci.yml",
            "description": "Volume-aware comprehensive checks",
            "triggers": ["push", "pr", "manual"],
            "timeout": "Variable",
            "volume_aware": True
        },
        "quality": {
            "file": ".github/workflows/quality.yml", 
            "description": "PR-specific quality feedback",
            "triggers": ["pr"],
            "timeout": "15 min",
            "volume_aware": False
        },
        "pr-checks": {
            "file": ".github/workflows/pr-checks.yml",
            "description": "Ultra-fast PR validation",
            "triggers": ["pr"],
            "timeout": "10 min", 
            "volume_aware": False
        },
        "bg-fix": {
            "file": ".github/workflows/bg-fix.yml",
            "description": "Background auto-fixing",
            "triggers": ["manual", "scheduled"],
            "timeout": "30 min",
            "volume_aware": True
        }
    }
    
    VOLUME_THRESHOLDS = {
        (0, 199): "Tests only",
        (200, 399): "Tests + relaxed linting", 
        (400, 599): "Tests + linting + type checking",
        (600, 1000): "All checks including security"
    }
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        
    def list_workflows(self) -> None:
        """List all available workflows with their details."""
        print("🚀 AutoPR Engine Workflows\n")
        
        for name, config in self.WORKFLOWS.items():
            triggers = ", ".join(config["triggers"])
            volume_icon = "📊" if config["volume_aware"] else "⚡"
            
            print(f"{volume_icon} **{name.upper()}**")
            print(f"   Description: {config['description']}")
            print(f"   Triggers: {triggers}")
            print(f"   Timeout: {config['timeout']}")
            print(f"   Volume Aware: {'Yes' if config['volume_aware'] else 'No'}")
            print()
    
    def show_volume_system(self) -> None:
        """Show the volume-based execution system."""
        print("📊 Volume-Based Execution System\n")
        print("The workflow system uses volume levels (0-1000) to determine check intensity:\n")
        
        for (min_vol, max_vol), description in self.VOLUME_THRESHOLDS.items():
            print(f"**{min_vol}-{max_vol}:** {description}")
        
        print("\n**Repository Variables:**")
        print("- `AUTOPR_VOLUME_PR`: Volume for pull requests (default: 100)")
        print("- `AUTOPR_VOLUME_CHECKIN`: Volume for pushes (default: 50)")
        print("- `AUTOPR_VOLUME_DEV`: Volume for development (default: 200)")
    
    def check_workflow_status(self, workflow_name: str) -> None:
        """Check the status of a specific workflow."""
        if workflow_name not in self.WORKFLOWS:
            print(f"❌ Unknown workflow: {workflow_name}")
            print(f"Available workflows: {', '.join(self.WORKFLOWS.keys())}")
            return
        
        config = self.WORKFLOWS[workflow_name]
        workflow_file = self.project_root / config["file"]
        
        if not workflow_file.exists():
            print(f"❌ Workflow file not found: {workflow_file}")
            return
        
        print(f"✅ Workflow file exists: {workflow_file}")
        print(f"📝 Description: {config['description']}")
        print(f"🎯 Triggers: {', '.join(config['triggers'])}")
        print(f"⏱️  Timeout: {config['timeout']}")
        
        # Check file size and last modified
        stat = workflow_file.stat()
        print(f"📏 File size: {stat.st_size} bytes")
        print(f"🕒 Last modified: {stat.st_mtime}")
    
    def validate_workflows(self) -> None:
        """Validate all workflow files for syntax and structure."""
        print("🔍 Validating Workflows\n")
        
        all_valid = True
        
        for name, config in self.WORKFLOWS.items():
            workflow_file = self.project_root / config["file"]
            
            if not workflow_file.exists():
                print(f"❌ {name}: File not found")
                all_valid = False
                continue
            
            # Basic YAML validation
            try:
                import yaml
                with open(workflow_file, 'r') as f:
                    yaml.safe_load(f)
                print(f"✅ {name}: Valid YAML")
            except Exception as e:
                print(f"❌ {name}: Invalid YAML - {e}")
                all_valid = False
        
        if all_valid:
            print("\n🎉 All workflows are valid!")
        else:
            print("\n⚠️  Some workflows have issues.")
    
    def get_workflow_stats(self) -> None:
        """Get statistics about workflow usage and performance."""
        print("📈 Workflow Statistics\n")
        
        # This would typically query GitHub API for actual stats
        # For now, show static information
        print("**Workflow Performance Targets:**")
        print("- PR-Checks: < 10 minutes")
        print("- Quality Feedback: < 15 minutes") 
        print("- CI: Variable (based on volume)")
        print("- Background Fixer: < 30 minutes")
        
        print("\n**Volume Distribution:**")
        print("- Low Volume (0-199): 20% of PRs")
        print("- Medium Volume (200-599): 60% of PRs")
        print("- High Volume (600+): 20% of PRs")
    
    def generate_workflow_docs(self) -> None:
        """Generate workflow documentation."""
        print("📚 Generating Workflow Documentation\n")
        
        docs_content = """# AutoPR Engine Workflows

This documentation is auto-generated by the workflow manager.

## Workflow Overview

"""
        
        for name, config in self.WORKFLOWS.items():
            docs_content += f"### {name.upper()}\n"
            docs_content += f"- **Description:** {config['description']}\n"
            docs_content += f"- **Triggers:** {', '.join(config['triggers'])}\n"
            docs_content += f"- **Timeout:** {config['timeout']}\n"
            docs_content += f"- **Volume Aware:** {'Yes' if config['volume_aware'] else 'No'}\n\n"
        
        docs_file = self.project_root / "docs" / "workflows.md"
        docs_file.parent.mkdir(exist_ok=True)
        
        with open(docs_file, 'w') as f:
            f.write(docs_content)
        
        print(f"✅ Documentation generated: {docs_file}")


def main():
    parser = argparse.ArgumentParser(description="AutoPR Engine Workflow Manager")
    parser.add_argument("command", choices=[
        "list", "volume", "status", "validate", "stats", "docs"
    ], help="Command to execute")
    parser.add_argument("--workflow", help="Workflow name for status command")
    
    args = parser.parse_args()
    
    manager = WorkflowManager()
    
    if args.command == "list":
        manager.list_workflows()
    elif args.command == "volume":
        manager.show_volume_system()
    elif args.command == "status":
        if not args.workflow:
            print("❌ Please specify a workflow with --workflow")
            sys.exit(1)
        manager.check_workflow_status(args.workflow)
    elif args.command == "validate":
        manager.validate_workflows()
    elif args.command == "stats":
        manager.get_workflow_stats()
    elif args.command == "docs":
        manager.generate_workflow_docs()


if __name__ == "__main__":
    main()
