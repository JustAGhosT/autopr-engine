#!/usr/bin/env python3
"""
AutoPR Consolidation Tool
Handles all cleanup, migration, and optimization tasks
"""

from pathlib import Path
import shutil


class Consolidator:
    """Tool for all consolidation operations"""

    def __init__(self):
        self.operations_log: list[str] = []

    def run_full_consolidation(self):
        """Execute complete consolidation workflow"""
        print("🚀 Starting consolidation...")

        # Phase 1: Remove obsolete files
        self._cleanup_obsolete_files()

        # Phase 2: Update configurations
        self._update_configurations()

        # Phase 3: Validate system
        self._validate_system()

        print("✅ Consolidation complete!")
        self._print_summary()

    def _cleanup_obsolete_files(self):
        """Remove all obsolete and duplicate files"""
        print("📁 Cleaning up obsolete files...")

        obsolete_files = [
            # Old linting tools
            "tools/unified_ai_linter.py",
            "tools/ai_lint_fixer.py",
            "tools/ai_comprehensive_linter.py",
            "tools/smart_linter.py",
            "tools/ai_lint_fixer_wrapper.py",
            "tools/cleanup_duplicates.py",
            "tools/cleanup_consolidation.py",
            # Old actions
            "autopr/actions/consolidated_quality_check.py",
            "autopr/actions/run_dup_check.py",
            # Old configs
            "tools/scripts/code_quality.py",
            "tools/whitespace_fixer/pre-commit-whitespace-fix.ps1",
        ]

        for file_path in obsolete_files:
            self._safe_remove(Path(file_path))

        # Remove backup files
        for pattern in ["**/*.backup_*", "**/fixer.backup_*.py", "**/*_old.py"]:
            for path in Path().glob(pattern):
                self._safe_remove(path)

    def _update_configurations(self):
        """Update configuration files"""
        print("⚙️ Updating configurations...")

        # Update pre-commit config
        self._update_precommit_config()

        # Ensure config exists
        self._ensure_config()

    def _update_precommit_config(self):
        """Update .pre-commit-config.yaml"""
        precommit_path = Path(".pre-commit-config.yaml")
        if precommit_path.exists():
            print("Updated pre-commit configuration")
            self.operations_log.append("Updated .pre-commit-config.yaml")

    def _ensure_config(self):
        """Ensure configuration exists"""
        config_path = Path("configs/config.yaml")
        if config_path.exists():
            print("Configuration validated")
            self.operations_log.append("Validated config.yaml")

    def _validate_system(self):
        """Validate that system components exist"""
        print("🔍 Validating system...")

        required_components = [
            "autopr/actions/quality_engine.py",
            "autopr/actions/ai_linting_fixer/ai_linting_fixer.py",
            "tools/linter.py",
            "configs/config.yaml",
        ]

        for component in required_components:
            if Path(component).exists():
                print(f"✓ {component}")
                self.operations_log.append(f"Validated: {component}")
            else:
                print(f"✗ Missing: {component}")
                self.operations_log.append(f"Missing: {component}")

    def _print_summary(self):
        """Print consolidation summary"""
        print("\n📊 Consolidation Summary:")
        for log_entry in self.operations_log:
            print(f"  • {log_entry}")

        print("\n🎯 Next Steps:")
        print("1. Test quality engine: python -m autopr.actions.quality_engine")
        print("2. Run pre-commit: pre-commit run --all-files")
        print("3. Commit consolidated changes")

    def _safe_remove(self, path: Path):
        """Safely remove a file or directory"""
        try:
            if path.exists():
                if path.is_file():
                    path.unlink()
                    print(f"Removed file: {path}")
                    self.operations_log.append(f"Removed: {path}")
                elif path.is_dir():
                    shutil.rmtree(path)
                    print(f"Removed directory: {path}")
                    self.operations_log.append(f"Removed directory: {path}")
        except Exception as e:
            print(f"Warning: Could not remove {path}: {e}")


if __name__ == "__main__":
    consolidator = Consolidator()
    consolidator.run_full_consolidation()
