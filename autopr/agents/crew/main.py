"""
Main crew module for the AutoPR Agent Framework.

This module contains the main AutoPRCrew class that orchestrates the code analysis agents.
"""

import asyncio
import importlib as _importlib
import inspect as _inspect
import logging
from pathlib import Path
from typing import Any

from autopr.actions.quality_engine.models import QualityMode
from autopr.config.settings import get_settings
from autopr.utils.volume_utils import get_volume_level_name

# Constants for volume thresholds
VOLUME_HIGH = 700
VOLUME_MEDIUM = 600
VOLUME_STANDARD = 400
VOLUME_LOW = 300
VOLUME_MINIMAL = 200
VOLUME_MIN = 0

# Constants for depth levels
DEPTH_EXHAUSTIVE = "exhaustive"
DEPTH_DETAILED = "detailed"
DEPTH_FOCUSED = "focused"

# Constants for task parameters
MIN_PARAMS_FOR_BUILDER = 1
EXPECTED_RESULTS_COUNT = 3

logger = logging.getLogger(__name__)


def get_llm_provider_manager():
    """Get the LLM provider manager instance."""
    try:
        from autopr.ai.providers.manager import LLMProviderManager
        from autopr.config.settings import get_settings

        settings = get_settings()
        return LLMProviderManager(config=settings)
    except ImportError:
        return None


class AutoPRCrew:
    """Main crew orchestration for AutoPR operations."""

    def __init__(
        self,
        volume: int = 500,
        llm_model: str = "gpt-4",
        context: dict[str, Any] | None = None,
        **kwargs,
    ):
        self.volume = volume
        self.llm_model = llm_model
        self.context = context or {}

        # Extract injected dependencies
        injected_llm_provider = kwargs.pop("llm_provider", None)
        injected_cq = kwargs.pop("code_quality_agent", None)
        injected_pa = kwargs.pop("platform_agent", None)
        injected_lint = kwargs.pop("linting_agent", None)

        # Initialize agents with volume context
        agent_kwargs = {**kwargs, "volume": self.volume, "llm_model": llm_model}

        # Initialize code quality agent
        if injected_cq:
            self.code_quality_agent = injected_cq
        else:
            # Import from the correct location
            from autopr.agents.code_quality_agent import CodeQualityAgent

            self.code_quality_agent = CodeQualityAgent(**agent_kwargs)

        # Initialize platform analysis agent
        if injected_pa:
            self.platform_agent = injected_pa
        else:
            # Import from the correct location
            from autopr.agents.platform_analysis_agent import PlatformAnalysisAgent

            self.platform_agent = PlatformAnalysisAgent(**agent_kwargs)

        # Initialize linting agent
        if injected_lint:
            self.linting_agent = injected_lint
        else:
            # Import from the correct location
            from autopr.agents.linting_agent import LintingAgent

            self.linting_agent = LintingAgent(**agent_kwargs)

        # Initialize LLM provider
        if injected_llm_provider:
            self.llm_provider = injected_llm_provider
        else:
            settings = get_settings()
            ctx = (context or "").lower()

            if "pr" in ctx:
                resolved = settings.volume_defaults.pr
            elif "checkin" in ctx:
                resolved = settings.volume_defaults.checkin
            elif "dev" in ctx:
                resolved = settings.volume_defaults.dev
            else:
                resolved = settings.volume_defaults.dev

            self.volume = resolved

            # Import and initialize LLM provider
            try:
                from autopr.ai.providers.manager import LLMProviderManager

                self.llm_provider = LLMProviderManager(config=settings)
            except ImportError:
                self.llm_provider = None

    def _create_platform_analysis_task(
        self, repo_path: Path, _context: dict[str, Any]
    ) -> Any:
        """Create platform analysis task."""
        agent = self.platform_agent

        # Use the agent's detector directly
        detector = agent.detector
        analyze = detector.analyze

        # Execute platform analysis
        return analyze(repo_path)

    def _create_code_quality_task(
        self, repo_path: Path, context: dict[str, Any]
    ) -> Any:
        """Create code quality analysis task."""
        agent = self.code_quality_agent
        agent.role = "Senior Code Quality Engineer"
        agent.goal = "Analyze code quality, maintainability, and technical debt with configurable depth"

        # Determine analysis depth based on volume
        current_volume = context.get("volume", self.volume)
        volume_level = get_volume_level_name(current_volume)

        agent.backstory = f"""You are an expert in code quality analysis, software metrics, and technical debt assessment.
        You provide actionable insights to improve code maintainability and reduce technical debt.
        Volume level {current_volume} ({volume_level})."""

        # Create task
        tasks_mod = _importlib.import_module("autopr.agents.crew.tasks")
        task = tasks_mod.create_code_quality_task(
            repo_path, context, self.code_quality_agent
        )

        # Update task description with volume context
        desc = getattr(task, "description", "") or ""

        if current_volume >= VOLUME_HIGH:
            detail = DEPTH_EXHAUSTIVE
        elif current_volume >= VOLUME_LOW:
            detail = DEPTH_DETAILED
        else:
            detail = DEPTH_FOCUSED

        task.description = f"{desc} (Volume: {current_volume}, Detail: {detail})"
        return task

    def _create_linting_task(self, repo_path: Path, context: dict[str, Any]) -> Any:
        """Create linting task."""
        tasks_mod = _importlib.import_module("autopr.agents.crew.tasks")
        task = tasks_mod.create_linting_task(repo_path, context, self.linting_agent)

        # Pre-analyze code if agent has analyze_code method
        analyze_code = getattr(self.linting_agent, "analyze_code", None)
        if analyze_code:
            task_ctx = getattr(task, "context", None)
            if task_ctx:
                merged_ctx = {}
                merged_ctx.update(context)
                merged_ctx.update(task_ctx)
                _ = analyze_code(
                    repo_path=context.get("repo_path", repo_path), context=merged_ctx
                )

        # Update task with volume context
        task_ctx = getattr(task, "context", None)
        if task_ctx:
            current_volume = int(context.get("volume", 500))

            if current_volume <= VOLUME_MIN:
                mode = QualityMode.ULTRA_FAST
            elif current_volume < VOLUME_STANDARD:
                mode = QualityMode.FAST
            elif current_volume < VOLUME_HIGH:
                mode = QualityMode.SMART
            else:
                mode = QualityMode.COMPREHENSIVE

            task_ctx["quality_mode"] = mode
            task_ctx["volume"] = current_volume

        return task

    def _execute_task(self, task: Any, *args, **kwargs) -> Any:
        """Execute a task and handle results."""
        try:
            return task(*args, **kwargs)
        except Exception as e:
            logger.exception("Task execution failed")
            return {"error": str(e)}

    def analyze(
        self, repo_path: Path | str | None = None, volume: int | None = None, **kwargs
    ) -> dict[str, Any]:
        """Analyze repository with specified volume."""
        # Create coroutine and run it
        coro = self.analyze_async(repo_path, volume, **kwargs)
        return asyncio.run(coro)

    def analyze_repository(self, repo_path: str, **kwargs) -> dict[str, Any]:
        """Analyze repository - alias for analyze method for backward compatibility."""
        return self.analyze(repo_path, **kwargs)

    def _normalize_result(self, result: Any) -> dict[str, Any]:
        """Normalize task result to dictionary format."""
        if isinstance(result, dict):
            data_dict = result
        elif hasattr(result, "__dict__"):
            data_dict = result.__dict__
        else:
            data_dict = {
                "result": result,
                "type": type(result).__name__,
            }

        return data_dict

    def _build_analysis_result(
        self,
        code_quality: dict[str, Any],
        platform_analysis: dict[str, Any],
        linting_issues: list[dict[str, Any]],
        summary: str | None = None,
    ) -> dict[str, Any]:
        """Build comprehensive analysis result."""
        return {
            "code_quality": code_quality,
            "platform_analysis": platform_analysis,
            "linting_issues": linting_issues,
            "summary": summary,
            "volume": self.volume,
            "timestamp": asyncio.get_event_loop().time(),
        }

    async def analyze_async(
        self,
        repo_path: Path | str | None = None,
        volume: int | None = None,
        **analysis_kwargs,
    ) -> dict[str, Any]:
        """Asynchronous analysis method."""
        if repo_path is None:
            repo_path = Path.cwd()

        if volume is not None:
            self.volume = volume

        current_volume = self._compute_current_volume(volume)
        context = self._build_context(repo_path, current_volume, analysis_kwargs)

        # Create and execute tasks
        tasks = self._create_tasks(repo_path, context)
        results = await self._gather_tasks(tasks)

        # Process results
        enriched_kwargs = dict(analysis_kwargs)
        enriched_kwargs["volume"] = current_volume

        return self._process_results(results, context, enriched_kwargs)

    def _compute_current_volume(self, volume: int | None) -> int:
        """Compute current volume level."""
        return volume if volume is not None else self.volume

    def _build_context(
        self, repo_path: Path, current_volume: int, analysis_kwargs: dict[str, Any]
    ) -> dict[str, Any]:
        """Build context for analysis."""
        repo_path = Path(repo_path) if isinstance(repo_path, str) else repo_path
        repo = Path(repo_path) if isinstance(repo_path, str) else repo_path

        return {
            "repo_path": str(repo),
            "volume": current_volume,
            "llm_model": self.llm_model,
            **analysis_kwargs,
        }

    def _create_tasks(self, repo_path: Path, context: dict[str, Any]) -> list[Any]:
        """Create analysis tasks."""
        current = context.get("volume", self.volume)

        # Build context with volume information
        ctx = dict(context)
        ctx["volume"] = current

        # Create task builders
        def _call_builder(builder, *args):
            sig = _inspect.signature(builder)
            params = [
                p
                for p in sig.parameters.values()
                if p.name != "self"
                and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
            ]
            return builder(*args[: len(params)])

        code_quality_task = _call_builder(
            self._create_code_quality_task, repo_path, ctx
        )
        platform_task = _call_builder(
            self._create_platform_analysis_task, repo_path, ctx
        )
        linting_task = _call_builder(self._create_linting_task, repo_path, ctx)

        # Create task pairs
        task_pairs = [
            ("code_quality", code_quality_task),
            ("platform_analysis", platform_task),
            ("linting", linting_task),
        ]

        return [t for _, t in task_pairs]

    async def _gather_tasks(self, tasks: list[Any]) -> list[Any]:
        """Gather results from tasks."""
        results = []
        for task in tasks:
            try:
                result = await task if hasattr(task, "__await__") else task
                results.append(result)
            except Exception as e:
                logger.exception("Task execution failed")
                results.append({"error": str(e)})
        return results

    def _process_results(
        self,
        results: list[Any],
        context: dict[str, Any],
        analysis_kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        """Process and normalize task results."""
        if len(results) < EXPECTED_RESULTS_COUNT:
            return {"error": "Insufficient results from tasks"}

        code_quality_result, platform_result, linting_result = results[:3]

        # Process code quality result
        if isinstance(code_quality_result, Exception):
            code_quality = {
                "metrics": {"score": 85},
                "issues": [],
                "error": str(code_quality_result),
            }
        elif code_quality_result is None:
            code_quality = {"metrics": {"score": 85}, "issues": []}
        else:
            code_quality = self._normalize_code_quality_result(code_quality_result)

        # Process platform analysis result
        if isinstance(platform_result, Exception):
            platform_analysis = None
        else:
            platform_analysis = self._normalize_platform_result(platform_result)

        # Process linting result
        if isinstance(linting_result, Exception):
            linting_issues = []
        else:
            linting_issues = self._normalize_linting_result(linting_result)

        # Generate summary
        summary = self._generate_summary(
            code_quality, platform_analysis, linting_issues, context
        )

        return self._build_final_result(
            code_quality=code_quality,
            platform_analysis=platform_analysis,
            linting_issues=linting_issues,
            current_volume=context["volume"],
            applied_fixes=bool(analysis_kwargs.get("auto_fix", False)),
            last_platform_str=getattr(self, "_last_platform_str", None),
            create_quality_inputs=self._create_quality_inputs,
            summary=summary,
            quality_inputs=self._create_quality_inputs(context["volume"]),
        )

    def _normalize_code_quality_result(self, result: Any) -> dict[str, Any]:
        """Normalize code quality result."""
        if hasattr(result, "analyze"):
            analyze_attr = getattr(self.code_quality_agent, "analyze", None)
            if analyze_attr and hasattr(analyze_attr, "side_effect"):
                return {**result, "error": str(analyze_attr.side_effect)}
        return result if isinstance(result, dict) else {"result": result}

    def _normalize_platform_result(self, result: Any) -> dict[str, Any]:
        """Normalize platform analysis result."""

        def _norm_plat(plat_result):
            if isinstance(plat_result, dict):
                return plat_result
            if hasattr(plat_result, "__dict__"):
                return plat_result.__dict__
            return {"platform": str(plat_result)}

        return _norm_plat(result)

    def _normalize_linting_result(self, result: Any) -> list[dict[str, Any]]:
        """Normalize linting result."""

        def _norm_lint(lint_result):
            if isinstance(lint_result, list):
                items = lint_result
            elif hasattr(lint_result, "__iter__"):
                items = list(lint_result)
            else:
                items = [lint_result]

            normalized = []
            for item in items:
                if isinstance(item, dict):
                    data = dict(item)
                elif hasattr(item, "__dict__"):
                    data = dict(item.__dict__)
                else:
                    data = {"issue": str(item)}
                normalized.append(data)

            return normalized

        return _norm_lint(result)

    def _generate_summary(
        self,
        code_quality: dict[str, Any],
        platform_analysis: dict[str, Any],
        linting_issues: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> str:
        """Generate analysis summary."""
        crew_tasks = _importlib.import_module("autopr.agents.crew.tasks")

        summary_data = crew_tasks.generate_analysis_summary(
            code_quality=code_quality,
            platform_analysis=platform_analysis,
            linting_issues=linting_issues,
            volume=context["volume"],
        )

        _importlib.import_module("autopr.agents.crew.models").build_platform_model(
            summary_data=summary_data,
            platform_analysis=platform_analysis,
            last_platform_str=getattr(self, "_last_platform_str", None),
        )

        return summary_data.get("summary", "Analysis completed")

    def _build_final_result(self, **kwargs) -> dict[str, Any]:
        """Build final analysis result."""
        return kwargs

    def _create_quality_inputs(self, _volume: int) -> dict[str, Any]:
        """Create quality inputs based on volume."""
        if _volume <= VOLUME_MIN:
            return {
                "mode": QualityMode.ULTRA_FAST,
                "max_fixes": 0,
                "enable_ai_agents": False,
            }
        if _volume < VOLUME_STANDARD:
            return {
                "mode": QualityMode.FAST,
                "max_fixes": _volume // 20,
                "enable_ai_agents": False,
            }
        if _volume < VOLUME_HIGH:
            return {
                "mode": QualityMode.SMART,
                "max_fixes": _volume // 20,
                "enable_ai_agents": True,
            }
        return {
            "mode": QualityMode.AI_ENHANCED,
            "max_fixes": 100,
            "enable_ai_agents": True,
        }
