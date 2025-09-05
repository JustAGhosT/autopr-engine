"""
Component Splitter for AI Linting Fixer

Handles splitting files into individual components.
"""

import itertools
import logging
from typing import Any

from autopr.actions.ai_linting_fixer.split_models.split_models import (
    SplitComponent, SplitConfig)

logger = logging.getLogger(__name__)


class ComponentSplitter:
    """Handles splitting files into individual components."""

    def __init__(self, parallel_processor: Any):
        self.parallel_processor = parallel_processor

    def split_file_components(self, content: str, config: SplitConfig) -> list[SplitComponent]:
        """Split file into components using parallel processing."""
        lines = content.split("\n")
        components = []

        logger.debug("Splitting file into components (lines: %d)", len(lines))

        # Use parallel processing for large files
        if len(lines) > 500 and config.enable_parallel_processing:
            logger.info("Using parallel processing for large file (%d lines)", len(lines))
            # Use custom chunking with overlap
            chunk_results = self._process_file_chunks_with_overlap(content, config)
            if chunk_results:
                # Flatten the list-of-lists into a single list of components
                components = list(
                    itertools.chain.from_iterable(
                        result for result in chunk_results if result is not None
                    )
                )
                logger.info(
                    "Parallel processing complete, found %d total components",
                    len(components),
                )
                # Post-process to merge adjacent components with same name
                components = self._merge_adjacent_components(components)
                logger.info("After merging adjacent components: %d components", len(components))
                return components

        # Fallback to sequential processing
        logger.info("Using sequential processing for component splitting")
        components = self._split_by_functions(content)
        logger.info("Sequential processing complete, found %d components", len(components))
        return components

    def _process_file_chunks_with_overlap(
        self, content: str, config: SplitConfig
    ) -> list[list[SplitComponent]]:
        """Process file in chunks with configurable overlap."""
        lines = content.split("\n")
        chunk_size = 500
        overlap = config.line_overlap

        # Create overlapping chunks
        chunks = []
        for i in range(0, len(lines), chunk_size - overlap):
            end_idx = min(i + chunk_size, len(lines))
            chunk_content = "\n".join(lines[i:end_idx])
            chunks.append(chunk_content)

            # Don't create overlapping chunks if we've reached the end
            if end_idx >= len(lines):
                break

        logger.debug("Created %d overlapping chunks with %d line overlap", len(chunks), overlap)

        # Process chunks in parallel
        with self.parallel_processor.executor_class(
            max_workers=self.parallel_processor.max_workers
        ) as executor:
            futures = [executor.submit(self._split_by_functions, chunk) for chunk in chunks]

            results = []
            for future in futures:
                try:
                    result = future.result(timeout=60)
                    results.append(result)
                except Exception:
                    logger.exception("Error processing chunk")
                    results.append(None)

        return results

    def _merge_adjacent_components(self, components: list[SplitComponent]) -> list[SplitComponent]:
        """Merge adjacent components with the same name and overlapping/contiguous line ranges."""
        if not components:
            return components

        # Sort components by start_line to ensure proper ordering
        sorted_components = sorted(components, key=lambda c: c.start_line)
        merged_components = []

        current_component = sorted_components[0]

        for next_component in sorted_components[1:]:
            # Check if components have the same name and overlapping/contiguous ranges
            if (
                current_component.name == next_component.name
                and current_component.component_type == next_component.component_type
                and (current_component.end_line >= next_component.start_line - 1)
            ):
                # Merge the components
                logger.debug(
                    "Merging components '%s' (lines %d-%d and %d-%d)",
                    current_component.name,
                    current_component.start_line,
                    current_component.end_line,
                    next_component.start_line,
                    next_component.end_line,
                )

                # Extend the current component's range
                current_component.end_line = max(
                    current_component.end_line, next_component.end_line
                )

                # Combine content (remove duplicate lines)
                current_lines = current_component.content.split("\n")
                next_lines = next_component.content.split("\n")

                # Find the overlap point and merge
                overlap_start = max(0, next_component.start_line - current_component.start_line)
                if overlap_start < len(current_lines):
                    # Remove overlapping lines from next component
                    next_lines = next_lines[overlap_start:]
                    current_component.content = "\n".join(current_lines + next_lines)
                else:
                    # No overlap, just append
                    current_component.content = "\n".join(current_lines + next_lines)

                # Combine metadata
                current_component.metadata.update(next_component.metadata)

                # Combine dependencies (remove duplicates)
                current_component.dependencies = list(
                    set(current_component.dependencies + next_component.dependencies)
                )

                # Update complexity score (take the maximum)
                current_component.complexity_score = max(
                    current_component.complexity_score, next_component.complexity_score
                )

            else:
                # No merge possible, add current component and move to next
                merged_components.append(current_component)
                current_component = next_component

        # Add the last component
        merged_components.append(current_component)

        logger.info(
            "Merged %d components into %d components",
            len(components),
            len(merged_components),
        )
        return merged_components

    def _split_by_functions(self, content: str) -> list[SplitComponent]:
        """Split file by functions."""
        components = []
        lines = content.split("\n")

        current_function = None
        function_start = 0
        function_count = 0

        logger.debug("Analyzing %d lines for function definitions...", len(lines))

        for i, line in enumerate(lines):
            if line.strip().startswith("def "):
                # Save previous function
                if current_function:
                    function_count += 1
                    logger.debug(
                        "Found function %d: %s (lines %d-%d)",
                        function_count,
                        current_function,
                        function_start + 1,
                        i,
                    )
                    components.append(
                        self._create_function_component(
                            current_function, function_start, i - 1, lines
                        )
                    )

                # Start new function
                current_function = line.strip().split("def ")[1].split("(")[0]
                function_start = i

        # Add last function
        if current_function:
            function_count += 1
            logger.debug(
                "Found function %d: %s (lines %d-%d)",
                function_count,
                current_function,
                function_start + 1,
                len(lines),
            )
            components.append(
                self._create_function_component(
                    current_function, function_start, len(lines) - 1, lines
                )
            )

        logger.info("Function analysis complete: found %d functions", len(components))
        return components

    def _create_function_component(
        self,
        function_name: str,
        start_line: int,
        end_line: int,
        lines: list[str],
    ) -> SplitComponent:
        """Create a function component."""
        content = "\n".join(lines[start_line : end_line + 1])

        # Calculate complexity for this function
        function_content = content
        complexity_keywords = ["if ", "elif ", "else:", "for ", "while ", "except "]
        complexity = sum(function_content.count(keyword) for keyword in complexity_keywords)

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
            return "module-based"
