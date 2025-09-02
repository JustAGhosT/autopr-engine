"""
Component Splitter for AI Linting Fixer

Handles splitting files into individual components.
"""

import itertools
import logging
from pathlib import Path
from typing import Any

from autopr.actions.ai_linting_fixer.split_models.split_models import (
    SplitComponent, SplitConfig)

logger = logging.getLogger(__name__)


class ComponentSplitter:
    """Handles splitting files into individual components."""

    def __init__(self, parallel_processor: Any):
        self.parallel_processor = parallel_processor

    def split_file_components(
        self, content: str, config: SplitConfig
    ) -> list[SplitComponent]:
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
            chunk_results = self.parallel_processor.process_file_chunks_parallel(
                Path("temp"),  # Temporary path for processing
                content,
                lambda chunk: self._split_by_functions(chunk, config),
                chunk_size=500,
            )
            if chunk_results:
                # Flatten the list-of-lists into a single list of components
                components = list(itertools.chain.from_iterable(
                    result for result in chunk_results if result is not None
                ))
                logger.info(
                    f"Parallel processing complete, found {len(components)} total components"
                )
                return components

        # Fallback to sequential processing
        logger.info("Using sequential processing for component splitting")
        components = self._split_by_functions(content, config)
        logger.info(
            f"Sequential processing complete, found {len(components)} components"
        )
        return components

    def _split_by_functions(
        self, content: str, config: SplitConfig
    ) -> list[SplitComponent]:
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
        lines: list[str],
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

    def _choose_splitting_strategy(self, complexity: dict[str, Any]) -> str:
        """Choose the best splitting strategy based on complexity."""
        if complexity["total_classes"] > 3:
            return "class-based"
        elif complexity["total_functions"] > 8:
            return "function-based"
        elif complexity["total_lines"] > 300:
            return "section-based"
        else:
            return "module-based"
            return "module-based"
