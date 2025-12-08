"""
File Splitter for AI Linting Fixer

Main orchestrator for file splitting operations.
"""

import logging
import time

from codeflow_engine.actions.ai_linting_fixer.analyzers.complexity_analyzer import \
    FileComplexityAnalyzer
from codeflow_engine.actions.ai_linting_fixer.engines.ai_split_decision_engine import \
    AISplitDecisionEngine
from codeflow_engine.actions.ai_linting_fixer.performance_optimizer import \
    ParallelProcessor
from codeflow_engine.actions.ai_linting_fixer.split_models.split_models import (
    SplitConfig, SplitResult)
from codeflow_engine.actions.ai_linting_fixer.splitters.component_splitter import \
    ComponentSplitter
from codeflow_engine.ai.core.providers.manager import LLMProviderManager
from codeflow_engine.quality.metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)


class FileSplitter:
    """Main file splitter with performance optimization."""

    def __init__(
        self,
        llm_manager: LLMProviderManager,
        metrics_collector: MetricsCollector | None = None,
        parallel_processor: ParallelProcessor | None = None,
    ):
        self.llm_manager = llm_manager
        self.metrics_collector = metrics_collector or MetricsCollector()

        # Initialize components
        self.parallel_processor = parallel_processor or ParallelProcessor()
        self.complexity_analyzer = FileComplexityAnalyzer()
        self.ai_decision_engine = AISplitDecisionEngine(llm_manager)
        self.component_splitter = ComponentSplitter(self.parallel_processor)

    async def split_file(
        self, file_path: str, content: str, config: SplitConfig | None = None
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

            logger.info("Complexity analysis complete:")
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
            components = self.component_splitter.split_file_components(content, config)

            logger.info(f"Split complete! Created {len(components)} components:")
            for i, component in enumerate(components, 1):
                msg = (
                    f"  {i}. {component.name} ({component.component_type}) - "
                    f"Lines {component.start_line}-{component.end_line} "
                    f"(complexity: {component.complexity_score:.2f})"
                )
                logger.info(msg)

            # Performance metrics
            processing_time = time.time() - start_time
            cache_stats = {"hits": 0, "misses": 0}

            # Get performance metrics
            perf_metrics = {"memory_usage_mb": 0.0}

            logger.info("Performance Summary:")
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
                    "split_strategy": self.component_splitter._choose_splitting_strategy(complexity),
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

    def cleanup(self):
        """Cleanup resources."""
        pass
        pass
