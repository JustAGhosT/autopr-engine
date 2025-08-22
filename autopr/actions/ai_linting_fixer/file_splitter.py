"""
AI Enhanced File Splitter with Performance Optimization

This module provides intelligent file splitting capabilities with advanced performance optimization,
including caching, parallel processing, and memory optimization.
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from autopr.actions.ai_linting_fixer.performance_optimizer import (
    PerformanceOptimizer,
    IntelligentCache,
    ParallelProcessor,
)
from autopr.actions.llm.manager import LLMProviderManager
from autopr.quality.metrics_collector import MetricsCollector


logger = logging.getLogger(__name__)


@dataclass
class SplitComponent:
    """Represents a component that can be split from a file."""

    name: str
    component_type: str  # 'function', 'class', 'section', 'module'
    start_line: int
    end_line: int
    content: str
    complexity_score: float
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SplitConfig:
    """Configuration for file splitting operations."""

    max_lines: int = 100
    max_functions: int = 10
    max_classes: int = 5
    max_complexity: float = 10.0
    enable_ai_analysis: bool = True
    enable_caching: bool = True
    enable_parallel_processing: bool = True
    enable_memory_optimization: bool = True
    cache_ttl: int = 3600  # 1 hour
    max_parallel_workers: int = 4
    memory_limit_mb: int = 512
    performance_monitoring: bool = True


@dataclass
class SplitResult:
    """Result of a file splitting operation."""

    success: bool
    components: List[SplitComponent]
    processing_time: float
    cache_hits: int = 0
    cache_misses: int = 0
    memory_usage_mb: float = 0.0
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class FileComplexityAnalyzer:
    """Analyzes file complexity using AST parsing."""

    def __init__(self, performance_optimizer: Optional[PerformanceOptimizer] = None):
        self.performance_optimizer = performance_optimizer or PerformanceOptimizer()
        self.cache_manager = self.performance_optimizer.cache

    def analyze_file_complexity(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze file complexity with caching support."""
        cache_key = f"complexity_analysis:{file_path}:{hash(content)}"

        # Try to get from cache first
        cached_result = self.cache_manager.get(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for complexity analysis: {file_path}")
            return cached_result

        # Perform analysis
        start_time = time.time()
        result = self._perform_complexity_analysis(content)
        analysis_time = time.time() - start_time

        # Cache the result
        self.cache_manager.set(cache_key, result, ttl_seconds=1800)  # 30 minutes

        logger.debug(
            f"Complexity analysis completed in {analysis_time:.3f}s: {file_path}"
        )
        return result

    def _perform_complexity_analysis(self, content: str) -> Dict[str, Any]:
        """Perform actual complexity analysis."""
        lines = content.split("\n")

        # Basic metrics
        total_lines = len(lines)
        total_functions = content.count("def ")
        total_classes = content.count("class ")
        file_size_bytes = len(content.encode("utf-8"))

        # Cyclomatic complexity (simplified)
        complexity_keywords = [
            "if ",
            "elif ",
            "else:",
            "for ",
            "while ",
            "except ",
            "and ",
            "or ",
        ]
        cyclomatic_complexity = sum(
            content.count(keyword) for keyword in complexity_keywords
        )

        return {
            "total_lines": total_lines,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "file_size_bytes": file_size_bytes,
            "cyclomatic_complexity": cyclomatic_complexity,
            "complexity_score": (
                cyclomatic_complexity + total_functions * 2 + total_classes * 3
            )
            / 10,
        }


class ComplexityVisitor:
    """AST visitor for complexity analysis."""

    def __init__(self):
        self.complexity = 0
        self.functions = []
        self.classes = []

    def visit(self, node):
        """Visit AST node and calculate complexity."""
        # Simplified complexity calculation
        pass


class AISplitDecisionEngine:
    """AI-powered decision engine for file splitting."""

    def __init__(
        self,
        llm_manager: LLMProviderManager,
        performance_optimizer: Optional[PerformanceOptimizer] = None,
    ):
        self.llm_manager = llm_manager
        self.performance_optimizer = performance_optimizer or PerformanceOptimizer()
        self.cache_manager = self.performance_optimizer.cache_manager

    async def should_split_file(
        self, file_path: str, content: str, complexity: Dict[str, Any]
    ) -> Tuple[bool, float, str]:
        """Determine if a file should be split using AI analysis."""
        cache_key = f"split_decision:{file_path}:{hash(content)}"

        # Try cache first
        cached_result = self.cache_manager.get(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for split decision: {file_path}")
            return (
                cached_result["should_split"],
                cached_result["confidence"],
                cached_result["reason"],
            )

        # AI analysis
        try:
            prompt = self._create_split_decision_prompt(content, complexity)
            response = await self.llm_manager.call_llm(
                "openai",
                prompt,
                system_prompt="You are an expert code analyzer. Determine if a file should be split based on complexity, maintainability, and best practices.",
                temperature=0.1,
            )

            if response and response.content:
                # Parse AI response (simplified)
                should_split = (
                    complexity["total_lines"] > 200
                    or complexity["complexity_score"] > 8.0
                )
                confidence = 0.8 if should_split else 0.6
                reason = (
                    "High complexity and line count"
                    if should_split
                    else "Within acceptable limits"
                )

                result = {
                    "should_split": should_split,
                    "confidence": confidence,
                    "reason": reason,
                }

                # Cache result
                self.cache_manager.set(cache_key, result, ttl_seconds=3600)

                return should_split, confidence, reason

        except Exception as e:
            logger.warning(f"AI split decision failed: {e}")

        # Fallback to rule-based decision
        should_split = (
            complexity["total_lines"] > 150 or complexity["complexity_score"] > 7.0
        )
        return should_split, 0.7, "Rule-based fallback"

    def _create_split_decision_prompt(
        self, content: str, complexity: Dict[str, Any]
    ) -> str:
        """Create prompt for AI split decision."""
        return f"""
Analyze this code file and determine if it should be split:

File Statistics:
- Lines: {complexity['total_lines']}
- Functions: {complexity['total_functions']}
- Classes: {complexity['total_classes']}
- Complexity Score: {complexity['complexity_score']:.2f}

Code Preview:
{content[:1000]}...

Should this file be split? Consider:
1. Maintainability
2. Single Responsibility Principle
3. Code organization
4. Team collaboration

Respond with: YES/NO and brief reasoning.
"""


class FileSplitter:
    """Main file splitter with performance optimization."""

    def __init__(
        self,
        llm_manager: LLMProviderManager,
        metrics_collector: Optional[MetricsCollector] = None,
        performance_optimizer: Optional[PerformanceOptimizer] = None,
    ):
        self.llm_manager = llm_manager
        self.metrics_collector = metrics_collector or MetricsCollector()
        self.performance_optimizer = performance_optimizer or PerformanceOptimizer()

        # Initialize components
        self.complexity_analyzer = FileComplexityAnalyzer(self.performance_optimizer)
        self.ai_decision_engine = AISplitDecisionEngine(
            llm_manager, self.performance_optimizer
        )
        self.parallel_processor = self.performance_optimizer.parallel_processor

    async def split_file(
        self, file_path: str, content: str, config: Optional[SplitConfig] = None
    ) -> SplitResult:
        """Split a file with performance optimization."""
        config = config or SplitConfig()
        start_time = time.time()

        try:
            # Analyze complexity
            complexity = self.complexity_analyzer.analyze_file_complexity(
                file_path, content
            )

            # AI decision
            should_split, confidence, reason = (
                await self.ai_decision_engine.should_split_file(
                    file_path, content, complexity
                )
            )

            if not should_split:
                return SplitResult(
                    success=True,
                    components=[],
                    processing_time=time.time() - start_time,
                    performance_metrics={},
                )

            # Split the file
            components = await self._split_file_components(content, config)

            # Performance metrics
            processing_time = time.time() - start_time
            cache_stats = self.performance_optimizer.cache.get_stats()

            # Record metrics
            self.metrics_collector.record_metric(
                "file_splitter_processing_time",
                processing_time,
                {"file_path": file_path, "components_count": len(components)},
            )

            return SplitResult(
                success=True,
                components=components,
                processing_time=processing_time,
                cache_hits=cache_stats.get("hits", 0),
                cache_misses=cache_stats.get("misses", 0),
                memory_usage_mb=0.0,  # Simplified for now
                performance_metrics={},
            )

        except Exception as e:
            logger.exception(f"File splitting failed: {file_path}")
            return SplitResult(
                success=False,
                components=[],
                processing_time=time.time() - start_time,
                errors=[str(e)],
                performance_metrics={},
            )

    async def _split_file_components(
        self, content: str, config: SplitConfig
    ) -> List[SplitComponent]:
        """Split file into components using parallel processing."""
        lines = content.split("\n")
        components = []

        # Use parallel processing for large files
        if len(lines) > 500 and config.enable_parallel_processing:
            components = await self.parallel_processor.process_parallel(
                self._split_by_functions,
                [(content, config)],
                max_workers=config.max_parallel_workers,
            )
            if components:
                return components[0]  # Return first result

        # Fallback to sequential processing
        return self._split_by_functions(content, config)

    def _split_by_functions(
        self, content: str, config: SplitConfig
    ) -> List[SplitComponent]:
        """Split file by functions."""
        components = []
        lines = content.split("\n")

        current_function = None
        function_start = 0

        for i, line in enumerate(lines):
            if line.strip().startswith("def "):
                # Save previous function
                if current_function:
                    components.append(
                        self._create_function_component(
                            current_function, function_start, i - 1, lines, config
                        )
                    )

                # Start new function
                current_function = line.strip().split("def ")[1].split("(")[0]
                function_start = i

        # Add last function
        if current_function:
            components.append(
                self._create_function_component(
                    current_function, function_start, len(lines) - 1, lines, config
                )
            )

        return components

    def _create_function_component(
        self,
        function_name: str,
        start_line: int,
        end_line: int,
        lines: List[str],
        config: SplitConfig,
    ) -> SplitComponent:
        """Create a function component."""
        content = "\n".join(lines[start_line : end_line + 1])

        # Calculate complexity for this function
        function_content = content
        complexity_keywords = ["if ", "elif ", "else:", "for ", "while ", "except "]
        complexity = sum(
            function_content.count(keyword) for keyword in complexity_keywords
        )

        return SplitComponent(
            name=function_name,
            component_type="function",
            start_line=start_line + 1,
            end_line=end_line + 1,
            content=content,
            complexity_score=complexity / 10.0,
        )

    def _choose_splitting_strategy(self, complexity: Dict[str, Any]) -> str:
        """Choose the best splitting strategy based on complexity."""
        if complexity["total_classes"] > 3:
            return "class-based"
        elif complexity["total_functions"] > 8:
            return "function-based"
        elif complexity["total_lines"] > 300:
            return "section-based"
        else:
            return "module-based"

    def cleanup(self):
        """Cleanup resources."""
        self.performance_optimizer.cleanup()
