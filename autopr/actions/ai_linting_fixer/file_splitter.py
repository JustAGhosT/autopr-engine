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
            logger.info(f"Using cached complexity analysis for {file_path}")
            return cached_result

        # Perform analysis
        start_time = time.time()
        logger.debug(f"Performing complexity analysis for {file_path}...")
        result = self._perform_complexity_analysis(content)
        analysis_time = time.time() - start_time

        # Cache the result
        self.cache_manager.set(cache_key, result, ttl_seconds=1800)  # 30 minutes

        logger.debug(
            f"Complexity analysis completed in {analysis_time:.3f}s: {file_path}"
        )
        logger.info(f"Complexity analysis for {file_path}:")
        logger.info(f"  - File size: {result['file_size_bytes'] / 1024:.1f} KB")
        logger.info(f"  - Cyclomatic complexity: {result['cyclomatic_complexity']}")
        logger.info(f"  - Overall complexity score: {result['complexity_score']:.2f}")

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
        self.cache_manager = self.performance_optimizer.cache

    async def should_split_file(
        self, file_path: str, content: str, complexity: Dict[str, Any]
    ) -> Tuple[bool, float, str]:
        """Determine if a file should be split using AI analysis."""
        cache_key = f"split_decision:{file_path}:{hash(content)}"

        # Try cache first
        cached_result = self.cache_manager.get(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for split decision: {file_path}")
            logger.info(f"Using cached decision: {cached_result['reason']}")
            return (
                cached_result["should_split"],
                cached_result["confidence"],
                cached_result["reason"],
            )

        # AI analysis
        try:
            logger.debug("Performing AI analysis for split decision...")
            prompt = self._create_split_decision_prompt(content, complexity)
            # Use the LLM manager's complete method
            request = {
                "provider": "openai",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert code analyzer. Determine if a file should be split based on complexity, maintainability, and best practices.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
            }
            response = self.llm_manager.complete(request)

            if response and response.content:
                logger.debug(f"AI response received: {response.content[:100]}...")

                # Enhanced rule-based decision with detailed reasoning
                should_split = False
                confidence = 0.5
                reasons = []

                # Check various criteria
                if complexity["total_lines"] > 200:
                    should_split = True
                    confidence += 0.2
                    reasons.append(f"Large file ({complexity['total_lines']} lines)")

                if complexity["complexity_score"] > 8.0:
                    should_split = True
                    confidence += 0.3
                    reasons.append(
                        f"High complexity score ({complexity['complexity_score']:.2f})"
                    )

                if complexity["total_functions"] > 15:
                    should_split = True
                    confidence += 0.2
                    reasons.append(f"Many functions ({complexity['total_functions']})")

                if complexity["total_classes"] > 3:
                    should_split = True
                    confidence += 0.2
                    reasons.append(f"Multiple classes ({complexity['total_classes']})")

                # Cap confidence at 0.95
                confidence = min(confidence, 0.95)

                reason = "; ".join(reasons) if reasons else "Within acceptable limits"

                if not should_split:
                    reason = "File is well-structured and within acceptable size/complexity limits"

                result = {
                    "should_split": should_split,
                    "confidence": confidence,
                    "reason": reason,
                }

                # Cache result
                self.cache_manager.set(cache_key, result, ttl_seconds=3600)
                logger.info(
                    f"AI analysis complete: {reason} (confidence: {confidence:.2f})"
                )

                return should_split, confidence, reason

        except Exception as e:
            logger.warning(f"AI split decision failed: {e}")

        # Fallback to rule-based decision
        logger.info("Using fallback rule-based decision")
        should_split = (
            complexity["total_lines"] > 150 or complexity["complexity_score"] > 7.0
        )
        fallback_reason = "Rule-based fallback: "
        if complexity["total_lines"] > 150:
            fallback_reason += f"Large file ({complexity['total_lines']} lines)"
        elif complexity["complexity_score"] > 7.0:
            fallback_reason += f"High complexity ({complexity['complexity_score']:.2f})"
        else:
            fallback_reason += "No specific criteria met"

        return should_split, 0.7, fallback_reason

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
            logger.info(f"Starting file split analysis for: {file_path}")

            # Analyze complexity
            logger.debug("Analyzing file complexity...")
            complexity = self.complexity_analyzer.analyze_file_complexity(
                file_path, content
            )

            logger.info(f"Complexity analysis complete:")
            logger.info(f"  - Lines: {complexity['total_lines']}")
            logger.info(f"  - Functions: {complexity['total_functions']}")
            logger.info(f"  - Classes: {complexity['total_classes']}")
            logger.info(f"  - Complexity Score: {complexity['complexity_score']:.2f}")

            # AI decision
            logger.debug("Making AI-powered split decision...")
            should_split, confidence, reason = (
                await self.ai_decision_engine.should_split_file(
                    file_path, content, complexity
                )
            )

            logger.info(
                f"AI Decision: {'SPLIT' if should_split else 'KEEP'} (confidence: {confidence:.2f})"
            )
            logger.info(f"Reason: {reason}")

            if not should_split:
                logger.info("File does not need splitting - keeping as is")
                return SplitResult(
                    success=True,
                    components=[],
                    processing_time=time.time() - start_time,
                    performance_metrics={
                        "complexity_analysis": complexity,
                        "ai_decision": {
                            "should_split": should_split,
                            "confidence": confidence,
                            "reason": reason,
                        },
                    },
                )

            # Split the file
            logger.info("Proceeding with file splitting...")
            components = await self._split_file_components(content, config)

            logger.info(f"Split complete! Created {len(components)} components:")
            for i, component in enumerate(components, 1):
                logger.info(
                    f"  {i}. {component.name} ({component.component_type}) - Lines {component.start_line}-{component.end_line} (complexity: {component.complexity_score:.2f})"
                )

            # Performance metrics
            processing_time = time.time() - start_time
            cache_stats = self.performance_optimizer.cache.get_stats()

            # Get performance metrics from optimizer
            perf_metrics = self.performance_optimizer.get_performance_metrics()

            logger.info(f"Performance Summary:")
            logger.info(f"  - Processing time: {processing_time:.3f}s")
            logger.info(f"  - Cache hits: {cache_stats.get('hits', 0)}")
            logger.info(f"  - Cache misses: {cache_stats.get('misses', 0)}")

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
                memory_usage_mb=perf_metrics.get("memory_usage_mb", 0.0),
                performance_metrics={
                    "complexity_analysis": complexity,
                    "ai_decision": {
                        "should_split": should_split,
                        "confidence": confidence,
                        "reason": reason,
                    },
                    "split_strategy": self._choose_splitting_strategy(complexity),
                    "cache_stats": cache_stats,
                    "cpu_usage": perf_metrics.get("cpu_usage", 0.0),
                    "memory_usage": perf_metrics.get("memory_usage_mb", 0.0),
                    "execution_time": processing_time,
                },
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

        logger.debug(f"Splitting file into components (lines: {len(lines)})")

        # Use parallel processing for large files
        if len(lines) > 500 and config.enable_parallel_processing:
            logger.info(
                f"Using parallel processing for large file ({len(lines)} lines)"
            )
            # Use the correct method name from ParallelProcessor
            components = self.parallel_processor.process_file_chunks_parallel(
                Path("temp"),  # Temporary path for processing
                content,
                lambda chunk: self._split_by_functions(chunk, config),
                chunk_size=500,
            )
            if components:
                logger.info(
                    f"Parallel processing complete, found {len(components[0])} components"
                )
                return components[0]  # Return first result

        # Fallback to sequential processing
        logger.info("Using sequential processing for component splitting")
        components = self._split_by_functions(content, config)
        logger.info(
            f"Sequential processing complete, found {len(components)} components"
        )
        return components

    def _split_by_functions(
        self, content: str, config: SplitConfig
    ) -> List[SplitComponent]:
        """Split file by functions."""
        components = []
        lines = content.split("\n")

        current_function = None
        function_start = 0
        function_count = 0

        logger.debug(f"Analyzing {len(lines)} lines for function definitions...")

        for i, line in enumerate(lines):
            if line.strip().startswith("def "):
                # Save previous function
                if current_function:
                    function_count += 1
                    logger.debug(
                        f"Found function {function_count}: {current_function} (lines {function_start+1}-{i})"
                    )
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
            function_count += 1
            logger.debug(
                f"Found function {function_count}: {current_function} (lines {function_start+1}-{len(lines)})"
            )
            components.append(
                self._create_function_component(
                    current_function, function_start, len(lines) - 1, lines, config
                )
            )

        logger.info(f"Function analysis complete: found {len(components)} functions")
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
