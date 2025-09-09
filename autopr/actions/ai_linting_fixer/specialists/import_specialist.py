"""
Import Specialist Module

This module provides specialized handling for import-related linting issues.
"""

import ast

from autopr.actions.ai_linting_fixer.models import LintingIssue
from autopr.actions.ai_linting_fixer.specialists.base_specialist import (
    AgentType, BaseSpecialist, FixStrategy)


class ImportSpecialist(BaseSpecialist):
    """Specialist for handling import-related linting issues."""

    def __init__(self):
        """Initialize the import specialist."""
        super().__init__(AgentType.IMPORT_OPTIMIZER)

    def _get_supported_codes(self) -> list[str]:
        """Get the list of error codes this specialist supports."""
        return [
            "F401",  # Unused imports
            "F403",  # Wildcard imports
            "F405",  # Name may be undefined or imported from star
            "TID252",  # Prefer absolute imports over relative imports
            "E402",  # Module level import not at top of file
        ]

    def _get_expertise_level(self) -> str:
        """Get the expertise level of this specialist."""
        return "expert"

    def _define_fix_strategies(self) -> list[FixStrategy]:
        """Define the fix strategies this specialist uses."""
        return [
            FixStrategy(
                name="import_optimization",
                description="Optimize import statements for clearness and performance",
                confidence_multiplier=1.2,
                max_retries=2,
                requires_context=True,
                priority=1,
            ),
            FixStrategy(
                name="unused_import_removal",
                description="Remove unused imports to clean up the code",
                confidence_multiplier=1.5,
                max_retries=1,
                requires_context=False,
                priority=2,
            ),
        ]

    def get_system_prompt(self) -> str:
        """Get the system prompt for this specialist."""
        return """You are an expert Python import optimizer. Your role is to:

1. Remove unused imports (F401)
2. Replace wildcard imports with specific imports (F403)
3. Convert relative imports to absolute imports (TID252)
4. Move imports to the top of the file (E402)
5. Optimize import organization and structure

Always maintain code functionality while improving import clarity and efficiency."""

    def get_specialty_score(self, issues: list[LintingIssue]) -> float:
        """Calculate specialty score for import issues."""
        if not issues:
            return 0.0

        import_issues = [
            issue for issue in issues if issue.error_code in self.supported_codes
        ]

        if not import_issues:
            return 0.0

        # High specialization for import issues
        return min(1.0, len(import_issues) / len(issues) * 2.0)

    def validate_fix(
        self, original_content: str, fixed_content: str, issues: list[LintingIssue]
    ) -> bool:
        """Validate that the fix addresses the import issues using AST analysis."""
        # Basic validation - check if content changed
        if original_content == fixed_content:
            return False

        # Parse original_content first
        try:
            original_ast = ast.parse(original_content)
        except SyntaxError:
            # If original content can't be parsed, use basic validation
            return original_content != fixed_content

        # Parse fixed_content separately - if this fails, validation fails
        try:
            fixed_ast = ast.parse(fixed_content)
        except SyntaxError:
            # Unparseable fixed content leads to validation failure
            return False

        # Extract import nodes from both ASTs
        original_imports = self._extract_import_nodes(original_ast)
        fixed_imports = self._extract_import_nodes(fixed_ast)

        # Check if there are any import changes
        if original_imports == fixed_imports:
            return False

        # Filter issues to only the ones this specialist handles
        supported_codes = set(self._get_supported_codes())
        applicable_issues = [
            issue for issue in issues if issue.error_code in supported_codes
        ]

        # If no applicable issues found, use AST-based change validation
        if not applicable_issues:
            return original_imports != fixed_imports

        # Analyze the specific import-related issues to determine if changes are applicable
        for issue in applicable_issues:
            if not self._is_import_change_applicable(
                issue, original_imports, fixed_imports
            ):
                return False

        return True

    def _extract_import_nodes(self, tree: ast.AST) -> set[tuple]:
        """Extract all import nodes from AST as comparable tuples."""
        imports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(("import", "", alias.name, alias.asname, node.lineno, 0))
            elif isinstance(node, ast.ImportFrom):
                level = getattr(node, "level", 0)
                module = node.module or ""
                for alias in node.names:
                    imports.add(
                        ("from", module, alias.name, alias.asname, node.lineno, level)
                    )

        return imports

    def _is_import_change_applicable(
        self, issue: LintingIssue, original_imports: set, fixed_imports: set
    ) -> bool:
        """Check if the import changes are applicable to the specific issue."""
        if issue.error_code == "F401":  # Unused imports
            # Check if unused imports were removed
            removed_imports = original_imports - fixed_imports
            return len(removed_imports) > 0

        elif issue.error_code in ("F403", "F405"):  # Wildcard imports
            # Check if wildcard imports were replaced with specific imports
            # Only consider from-import wildcards (imp[2] == "*")
            original_wildcards = {
                imp for imp in original_imports if imp[2] == "*"
            }
            fixed_wildcards = {
                imp for imp in fixed_imports if imp[2] == "*"
            }
            return len(original_wildcards) > len(fixed_wildcards)

        elif issue.error_code == "TID252":  # Prefer absolute imports
            # Check if relative imports were converted to absolute
            original_relative = {imp for imp in original_imports if imp[5] > 0}
            fixed_relative = {imp for imp in fixed_imports if imp[5] > 0}
            return len(original_relative) > len(fixed_relative)

        elif issue.error_code == "E402":  # Module level import not at top
            # Check if imports were moved to top of file (before any non-import statements)
            # Get the earliest import line in both versions
            original_earliest_import_line = min(
                (imp[3] for imp in original_imports), default=float("inf")
            )
            fixed_earliest_import_line = min(
                (imp[3] for imp in fixed_imports), default=float("inf")
            )
            # E402 is fixed if the earliest import moved up (lower line number)
            return fixed_earliest_import_line < original_earliest_import_line

        else:
            # For other issues, any import change is considered applicable
            return original_imports != fixed_imports
