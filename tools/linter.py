#!/usr/bin/env python3
"""
AutoPR Code Linter
Tool for all code quality checks and AI-powered fixes
"""

import asyncio
import json
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any

from autopr.actions.ai_linting_fixer import AILintingFixer, AILintingFixerInputs


class LintMode(Enum):
    FAST = "fast"
    COMPREHENSIVE = "comprehensive"
    AI_ONLY = "ai_only"
    SMART = "smart"


@dataclass
class LintResult:
    tool: str
    success: bool
    issues_found: int
    issues_fixed: int
    files_processed: list[str]
    execution_time: float
    error: str | None = None


class CodeLinter:
    """Linting engine with smart mode selection"""

    def __init__(self) -> None:
        self.results: list[LintResult] = []
        self.total_issues_found = 0
        self.total_issues_fixed = 0

    async def run(self, mode: LintMode, files: list[str] | None = None) -> dict[str, Any]:
        """Main entry point for consolidated linting"""

        if mode == LintMode.SMART:
            return await self._smart_mode(files)
        elif mode == LintMode.FAST:
            return await self._fast_mode(files)
        elif mode == LintMode.COMPREHENSIVE:
            return await self._comprehensive_mode(files)
        elif mode == LintMode.AI_ONLY:
            return await self._ai_only_mode(files)

    async def _smart_mode(self, files: list[str] | None) -> dict[str, Any]:
        """Smart mode: adapts based on commit size and file types"""

        # Determine commit size
        commit_size = len(files) if files else await self._get_staged_files_count()

        if commit_size > 10:
            # Large commit: comprehensive linting
            await self._run_ruff_check(files)
            if self.results[-1].issues_found > 0:
                await self._run_ruff_fix(files)
                await self._run_ai_fixes(files)
        else:
            # Small commit: fast linting
            await self._run_flake8(files)
            if self.results[-1].issues_found > 0:
                await self._run_ai_fixes(files)

        return self._generate_report()

    async def _run_ai_fixes(self, files: list[str] | None):
        """Run AI-powered fixes using the modular system"""
        try:
            inputs = AILintingFixerInputs(
                target_path="." if not files else files[0],
                fix_types=[
                    "E501",
                    "F401",
                    "F841",
                    "E722",
                    "B001",
                    "E302",
                    "E305",
                    "D200",
                    "D205",
                    "D400",
                    "D401",
                    "FURB110",
                    "PERF401",
                ],
                max_fixes_per_run=25,
                provider="azure_openai",
                model="gpt-4.1",
                max_workers=2,
                use_specialized_agents=True,
                create_backups=True,
                dry_run=False,
            )

            with AILintingFixer() as fixer:
                result = await fixer.run(inputs)

                self.results.append(
                    LintResult(
                        tool="ai_fixer",
                        success=result.success,
                        issues_found=result.total_issues_found,
                        issues_fixed=result.issues_fixed,
                        files_processed=result.files_modified,
                        execution_time=0.0,  # TODO: track timing
                    )
                )

        except Exception as e:
            self.results.append(
                LintResult(
                    tool="ai_fixer",
                    success=False,
                    issues_found=0,
                    issues_fixed=0,
                    files_processed=[],
                    execution_time=0.0,
                    error=str(e),
                )
            )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AutoPR Code Linter")
    parser.add_argument(
        "--mode",
        choices=["fast", "comprehensive", "ai_only", "smart"],
        default="smart",
        help="Linting mode",
    )
    parser.add_argument("files", nargs="*", help="Files to lint")

    args = parser.parse_args()

    linter = CodeLinter()
    result = asyncio.run(linter.run(LintMode(args.mode), args.files))

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["success"] else 1)
