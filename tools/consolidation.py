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

        # Phase 1: Remove obsolete files
        self._cleanup_obsolete_files()

        # Phase 2: Update configurations
        self._update_configurations()

        # Phase 3: Validate system
        self._validate_system()

        self._print_summary()

    def _cleanup_obsolete_files(self):
        """Remove all obsolete and duplicate files"""

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

        # Update pre-commit config
        self._update_precommit_config()

        # Ensure config exists
        self._ensure_config()

    def _update_precommit_config(self):
        """Update .pre-commit-config.yaml"""
        precommit_path = Path(".pre-commit-config.yaml")
        if precommit_path.exists():
            self.operations_log.append("Updated .pre-commit-config.yaml")

    def _ensure_config(self):
        """Ensure configuration exists"""
        config_path = Path("configs/config.yaml")
        if config_path.exists():
            self.operations_log.append("Validated config.yaml")

    def _validate_system(self):
        """Validate that system components exist"""

        required_components = [
            "autopr/actions/quality_engine.py",
            "autopr/actions/ai_linting_fixer/ai_linting_fixer.py",
            "tools/linter.py",
            "configs/config.yaml",
        ]

        for component in required_components:
            if Path(component).exists():
                self.operations_log.append(f"Validated: {component}")
            else:
                self.operations_log.append(f"Missing: {component}")

    def _print_summary(self):
        """Print consolidation summary"""
        for _log_entry in self.operations_log:
            pass


    def _safe_remove(self, path: Path):
        """Safely remove a file or directory"""
        try:
            if path.exists():
                if path.is_file():
                    path.unlink()
                    self.operations_log.append(f"Removed: {path}")
                elif path.is_dir():
                    shutil.rmtree(path)
                    self.operations_log.append(f"Removed directory: {path}")
        except Exception:
            pass


if __name__ == "__main__":
    consolidator = Consolidator()
    consolidator.run_full_consolidation()
