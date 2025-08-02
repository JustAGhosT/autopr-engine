"""
Quality Engine - Main engine for running quality analysis tools.
"""

import os
from typing import Any

import structlog

from ..base.action import Action
from .config import load_config
from .handler_registry import HandlerRegistry
from .models import QualityInputs, QualityMode, QualityOutputs
from .platform_detector import PlatformDetector
from .tool_runner import determine_smart_tools, run_tool
from .tools.registry import ToolRegistry

logger = structlog.get_logger(__name__)


class QualityEngine(Action):
    """Engine for all code quality operations"""

    id = "quality_engine"

    def __init__(
        self,
        config_path: str = "pyproject.toml",
        tool_registry: ToolRegistry | None = None,
        handler_registry: HandlerRegistry | None = None,
        config: Any | None = None,
    ):
        super().__init__(
            name="quality_engine",
            description="Engine for all code quality operations",
            version="1.0.0",
        )

        # Use injected registry or create a new one
        self.tool_registry = tool_registry
        if self.tool_registry is None:
            # Fallback to discover tools if not injected
            from .tools import discover_tools

            tools = discover_tools()
            self.tools = {tool().name: tool() for tool in tools}
        else:
            # Use the tool instances from the registry
            tools_list = self.tool_registry.get_all_tools()
            self.tools = {tool.name: tool for tool in tools_list}

        # Initialize platform detector
        self.platform_detector = PlatformDetector()

        # Show Windows warning if needed
        if self.platform_detector.should_show_windows_warning():
            self._show_windows_warning()

        # Filter tools based on platform compatibility
        self.tools = self._filter_tools_for_platform()

        # Apply tool substitutions for Windows
        self._apply_tool_substitutions()

        self.handler_registry = handler_registry
        self.config = config or load_config(config_path)
        self.llm_manager = None

        logger.info(
            "Quality Engine initialized",
            default_mode="smart",
            discovered_tools=list(self.tools.keys()),
            platform=self.platform_detector.detect_platform(),
        )

    def _show_windows_warning(self):
        """Show Windows-specific warnings and recommendations."""
        platform_info = self.platform_detector.detect_platform()
        limitations = self.platform_detector.get_windows_limitations()
        recommendations = self.platform_detector.get_windows_recommendations()

        logger.warning(
            "Running on Windows - some tools may have limitations",
            platform_info=platform_info,
            limitations=limitations,
            recommendations=recommendations,
        )

        print("\n" + "=" * 60)
        print("WINDOWS DETECTED - QUALITY ENGINE ADAPTATIONS")
        print("=" * 60)
        print(f"Platform: {platform_info['platform']}")
        print(f"Architecture: {platform_info['architecture']}")
        print(f"Python: {platform_info['python_version'].split()[0]}")
        print()

        if limitations:
            print("LIMITATIONS:")
            for limitation in limitations:
                print(f"  • {limitation}")
            print()

        if recommendations:
            print("RECOMMENDATIONS:")
            for rec in recommendations:
                print(f"  • {rec}")
            print()

        print("The quality engine will automatically adapt tools for Windows compatibility.")
        print("=" * 60 + "\n")

    def _filter_tools_for_platform(self) -> dict[str, Any]:
        """Filter tools based on platform compatibility."""
        all_tool_names = list(self.tools.keys())
        available_tools = self.platform_detector.get_available_tools(all_tool_names)

        filtered_tools = {}
        for tool_name in available_tools:
            if tool_name in self.tools:
                filtered_tools[tool_name] = self.tools[tool_name]

        return filtered_tools

    def _apply_tool_substitutions(self):
        """Apply tool substitutions for Windows-incompatible tools."""
        substitutions = self.platform_detector.get_tool_substitutions()

        for old_tool, new_tool in substitutions.items():
            if old_tool in self.tools and new_tool in self.tools:
                logger.info(
                    f"Substituting {old_tool} with {new_tool} for Windows compatibility",
                    old_tool=old_tool,
                    new_tool=new_tool,
                )
                # Replace the old tool with the new one
                self.tools[new_tool] = self.tools.pop(old_tool)

    def _determine_tools_for_mode(self, mode: QualityMode, files: list[str]) -> list[str]:
        """Determine which tools to run based on mode and files."""
        if mode == QualityMode.SMART:
            return determine_smart_tools(files)
        elif mode == QualityMode.FAST:
            return ["ruff", "bandit"]  # Fast mode with essential tools
        elif mode == QualityMode.COMPREHENSIVE:
            return list(self.tools.keys())  # All available tools
        else:
            return list(self.tools.keys())

    def _get_tool_config(self, tool_name: str) -> Any:
        """Get configuration for a specific tool."""
        if not self.config:
            return {"enabled": True, "config": {}}

        tool_config = getattr(self.config, "tools", {})
        tool_settings = tool_config.get(tool_name, {})

        # Handle different config formats
        if isinstance(tool_settings, dict):
            if "enabled" in tool_settings:
                return tool_settings
            else:
                return {"enabled": True, "config": tool_settings}
        else:
            return {"enabled": True, "config": {}}

    async def execute(self, inputs: QualityInputs, context: dict[str, Any]) -> QualityOutputs:
        """Execute the quality engine with the given inputs"""
        logger.info("Executing Quality Engine", mode=inputs.mode)

        # Determine files to check
        files_to_check = inputs.files or ["."]

        # Determine tools to run
        tools_to_run = self._determine_tools_for_mode(inputs.mode, files_to_check)

        # Filter tools based on what's actually available
        available_tools = [tool for tool in tools_to_run if tool in self.tools]

        if not available_tools:
            logger.warning("No tools available for the specified mode and files")
            return QualityOutputs(
                success=True,
                total_issues_found=0,
                total_issues_fixed=0,
                files_modified=[],
                issues_by_tool={},
                files_by_tool={},
                tool_execution_times={},
                summary="No tools available for analysis",
                ai_enhanced=False,
                ai_summary=None,
            )

        # Initialize results
        results = {}

        # Add detailed logging for comprehensive mode
        if inputs.mode == QualityMode.COMPREHENSIVE:
            logger.info(
                "Comprehensive mode activated",
                tools=available_tools,
                file_count=len(files_to_check),
                file_types=list(set([os.path.splitext(f)[1] for f in files_to_check if "." in f])),
            )

        # Run tools in parallel for better performance
        tool_tasks = []
        for tool_name in available_tools:
            tool_instance = self.tools.get(tool_name)
            if not tool_instance:
                logger.warning("Tool not available", tool=tool_name)
                continue

            tool_config = self._get_tool_config(tool_name)

            if tool_config.get("enabled", True):
                task = run_tool(
                    tool_name=tool_name,
                    tool_instance=tool_instance,
                    files=files_to_check,
                    tool_config=tool_config.get("config", {}),
                    handler_registry=self.handler_registry,
                )
                tool_tasks.append((tool_name, task))

        # Execute tools and gather results
        for tool_name, task in tool_tasks:
            tool_result = await task
            if tool_result:
                results[tool_name] = tool_result

        # Handle AI-enhanced mode
        ai_result = None
        ai_summary = None

        if inputs.mode == QualityMode.AI_ENHANCED and inputs.enable_ai_agents:
            # Lazy load the LLM manager if needed
            if not self.llm_manager:
                from .ai import initialize_llm_manager

                self.llm_manager = await initialize_llm_manager()

            if self.llm_manager:
                from .ai import run_ai_analysis

                ai_result = await run_ai_analysis(
                    files_to_check,
                    self.llm_manager,
                    provider_name=inputs.ai_provider,
                    model=inputs.ai_model,
                )

                if ai_result:
                    from .ai import create_tool_result_from_ai_analysis

                    results["ai_analysis"] = create_tool_result_from_ai_analysis(ai_result)
                    ai_summary = ai_result.get("summary")

        # Build the comprehensive summary
        from .summary import build_comprehensive_summary

        summary = build_comprehensive_summary(results, ai_summary)

        # Collect issues and files by tool
        issues_by_tool = {tool_name: result.issues for tool_name, result in results.items()}
        files_by_tool = {
            tool_name: result.files_with_issues for tool_name, result in results.items()
        }

        # Get execution times by tool
        tool_execution_times = {
            tool_name: result.execution_time for tool_name, result in results.items()
        }

        # Calculate total issues
        total_issues_found = sum(len(result.issues) for result in results.values())

        # Get unique files with issues
        unique_files_with_issues = set()
        for result in results.values():
            unique_files_with_issues.update(result.files_with_issues)

        return QualityOutputs(
            success=total_issues_found == 0,
            total_issues_found=total_issues_found,
            total_issues_fixed=0,  # Placeholder for future fix implementation
            files_modified=[],  # Placeholder for future fix implementation
            issues_by_tool=issues_by_tool,
            files_by_tool=files_by_tool,
            tool_execution_times=tool_execution_times,
            summary=summary,
            ai_enhanced=inputs.mode == QualityMode.AI_ENHANCED and ai_result is not None,
            ai_summary=ai_summary,
        )

    async def run(self, inputs: QualityInputs) -> QualityOutputs:
        """Execute the quality engine with the given inputs"""
        # Create an empty context dictionary to satisfy the base class contract
        return await self.execute(inputs, {})


# Factory function to create a quality engine with dependencies
def create_engine(
    config_path: str = "pyproject.toml",
    tool_registry: ToolRegistry | None = None,
    handler_registry: HandlerRegistry | None = None,
    config: Any | None = None,
) -> QualityEngine:
    """Create a quality engine with the given dependencies."""
    return QualityEngine(
        config_path=config_path,
        tool_registry=tool_registry,
        handler_registry=handler_registry,
        config=config,
    )
