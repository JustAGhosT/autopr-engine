"""
File Splitter Module - Complete AI integration for intelligent file splitting.

This module provides AI-enhanced file splitting capabilities that integrate with
the learning memory system, performance tracking, and specialist agents for
intelligent decision-making about when and how to split large files.
"""

import ast
from dataclasses import dataclass
from datetime import datetime
import logging
import time
from typing import Any

from pydantic import BaseModel, Field

from autopr.actions.ai_linting_fixer.metrics import MetricsCollector
from autopr.actions.learning_memory_system import LearningMemorySystem, MemoryInputs
from autopr.actions.llm.manager import LLMProviderManager


logger = logging.getLogger(__name__)


@dataclass
class SplitComponent:
    """Represents a component after file splitting."""

    name: str
    content: str
    start_line: int
    end_line: int
    component_type: str  # "class", "function", "module", "section"
    dependencies: list[str]
    complexity_score: float
    file_path: str


class SplitConfig(BaseModel):
    """Configuration for file splitting behavior."""

    # Size thresholds
    max_file_size_bytes: int = Field(
        default=50000, description="Maximum file size before splitting"
    )
    max_lines_per_file: int = Field(default=1000, description="Maximum lines per file")
    max_functions_per_file: int = Field(
        default=20, description="Maximum functions per file"
    )
    max_classes_per_file: int = Field(
        default=10, description="Maximum classes per file"
    )

    # Complexity thresholds
    max_cyclomatic_complexity: int = Field(
        default=15, description="Maximum cyclomatic complexity"
    )
    max_cognitive_complexity: int = Field(
        default=10, description="Maximum cognitive complexity"
    )

    # AI decision making
    use_ai_analysis: bool = Field(
        default=True, description="Use AI for splitting decisions"
    )
    confidence_threshold: float = Field(
        default=0.7, description="Minimum confidence for AI decisions"
    )
    learning_enabled: bool = Field(
        default=True, description="Enable learning from splitting patterns"
    )

    # Performance controls
    max_processing_time_seconds: int = Field(
        default=30, description="Maximum time for splitting analysis"
    )
    enable_parallel_processing: bool = Field(
        default=True, description="Enable parallel processing"
    )

    # Safety controls
    create_backups: bool = Field(
        default=True, description="Create backups before splitting"
    )
    validate_splits: bool = Field(default=True, description="Validate split components")
    preserve_imports: bool = Field(
        default=True, description="Preserve import statements in all components"
    )


class SplitResult(BaseModel):
    """Result of file splitting operation."""

    success: bool
    original_file: str
    components: list[SplitComponent] = Field(default_factory=list)
    split_strategy: str = ""
    reasoning: str = ""
    processing_time: float = 0.0
    confidence_score: float = 0.0
    error_message: str = ""
    backup_created: bool = False
    validation_passed: bool = False


class FileComplexityAnalyzer:
    """Analyzes file complexity for splitting decisions."""

    def __init__(self):
        self.complexity_cache: dict[str, dict[str, Any]] = {}

    def analyze_file_complexity(self, file_path: str, content: str) -> dict[str, Any]:
        """Analyze file complexity metrics."""
        if file_path in self.complexity_cache:
            return self.complexity_cache[file_path]

        try:
            tree = ast.parse(content)
            analyzer = ComplexityVisitor()
            analyzer.visit(tree)

            complexity_data = {
                "total_lines": len(content.splitlines()),
                "total_functions": len(analyzer.functions),
                "total_classes": len(analyzer.classes),
                "max_function_complexity": (
                    max(analyzer.function_complexities)
                    if analyzer.function_complexities
                    else 0
                ),
                "max_class_complexity": (
                    max(analyzer.class_complexities)
                    if analyzer.class_complexities
                    else 0
                ),
                "average_function_complexity": (
                    sum(analyzer.function_complexities)
                    / len(analyzer.function_complexities)
                    if analyzer.function_complexities
                    else 0
                ),
                "import_count": len(analyzer.imports),
                "file_size_bytes": len(content.encode("utf-8")),
                "cyclomatic_complexity": analyzer.total_cyclomatic_complexity,
                "cognitive_complexity": analyzer.total_cognitive_complexity,
            }

            self.complexity_cache[file_path] = complexity_data
            return complexity_data

        except SyntaxError as e:
            logger.warning("Syntax error in %s: %s", file_path, e)
            return {
                "total_lines": len(content.splitlines()),
                "total_functions": 0,
                "total_classes": 0,
                "max_function_complexity": 0,
                "max_class_complexity": 0,
                "average_function_complexity": 0,
                "import_count": 0,
                "file_size_bytes": len(content.encode("utf-8")),
                "cyclomatic_complexity": 0,
                "cognitive_complexity": 0,
                "syntax_error": str(e),
            }

    def should_split_by_complexity(
        self, complexity_data: dict[str, Any], config: SplitConfig
    ) -> tuple[bool, str]:
        """Determine if file should be split based on complexity metrics."""
        reasons = []

        if complexity_data["total_lines"] > config.max_lines_per_file:
            reasons.append(
                f"Too many lines ({complexity_data['total_lines']} > {config.max_lines_per_file})"
            )

        if complexity_data["total_functions"] > config.max_functions_per_file:
            reasons.append(
                f"Too many functions ({complexity_data['total_functions']} > "
                f"{config.max_functions_per_file})"
            )

        if complexity_data["total_classes"] > config.max_classes_per_file:
            reasons.append(
                f"Too many classes ({complexity_data['total_classes']} > {config.max_classes_per_file})"
            )

        if (
            complexity_data["max_function_complexity"]
            > config.max_cyclomatic_complexity
        ):
            reasons.append(
                f"Function too complex (complexity {complexity_data['max_function_complexity']} > {config.max_cyclomatic_complexity})"
            )

        if complexity_data["file_size_bytes"] > config.max_file_size_bytes:
            reasons.append(
                f"File too large ({complexity_data['file_size_bytes']} bytes > {config.max_file_size_bytes})"
            )

        should_split = len(reasons) > 0
        reasoning = "; ".join(reasons) if reasons else "No complexity issues detected"

        return should_split, reasoning


class ComplexityVisitor(ast.NodeVisitor):
    """AST visitor for analyzing code complexity."""

    def __init__(self):
        self.functions = []
        self.classes = []
        self.imports = []
        self.function_complexities = []
        self.class_complexities = []
        self.total_cyclomatic_complexity = 0
        self.total_cognitive_complexity = 0

    def visit_FunctionDef(self, node):
        self.functions.append(node.name)
        complexity = self._calculate_function_complexity(node)
        self.function_complexities.append(complexity)
        self.total_cyclomatic_complexity += complexity
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)  # Treat async functions the same

    def visit_ClassDef(self, node):
        self.classes.append(node.name)
        complexity = self._calculate_class_complexity(node)
        self.class_complexities.append(complexity)
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.append(node.module)
        self.generic_visit(node)

    def _calculate_function_complexity(self, node) -> int:
        """Calculate cyclomatic complexity for a function."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if (
                isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor))
                or isinstance(child, ast.ExceptHandler)
                or isinstance(child, ast.With)
            ):
                complexity += 1
            elif isinstance(child, ast.Compare):
                # Count comparison operators
                complexity += len(child.ops) - 1

        return complexity

    def _calculate_class_complexity(self, node) -> int:
        """Calculate complexity for a class."""
        complexity = 0
        for child in ast.walk(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity += self._calculate_function_complexity(child)
        return complexity


class AISplitDecisionEngine:
    """AI-powered decision engine for file splitting."""

    def __init__(
        self, llm_manager: LLMProviderManager, learning_system: LearningMemorySystem
    ):
        self.llm_manager = llm_manager
        self.learning_system = learning_system
        self.decision_cache: dict[str, dict[str, Any]] = {}

    def analyze_split_decision(
        self,
        file_path: str,
        content: str,
        complexity_data: dict[str, Any],
        config: SplitConfig,
    ) -> tuple[bool, str, float]:
        """Use AI to analyze whether and how to split a file."""

        cache_key = f"{file_path}_{hash(content)}"
        if cache_key in self.decision_cache:
            cached = self.decision_cache[cache_key]
            return cached["should_split"], cached["reasoning"], cached["confidence"]

        try:
            # Get historical patterns
            patterns = self._get_historical_patterns(file_path, complexity_data)

            # Create AI prompt
            prompt = self._create_split_decision_prompt(
                file_path, content, complexity_data, patterns, config
            )

            # Get AI decision
            response = self.llm_manager.call_llm(
                "gpt-4o",
                prompt,
                system_prompt=self._get_system_prompt(),
                temperature=0.1,
            )

            if not response or not response.content:
                return False, "AI analysis failed", 0.0

            # Parse AI response
            decision = self._parse_ai_decision(response.content)

            # Cache decision
            self.decision_cache[cache_key] = decision

            # Learn from decision
            if config.learning_enabled:
                self._learn_from_decision(file_path, complexity_data, decision)

            return (
                decision["should_split"],
                decision["reasoning"],
                decision["confidence"],
            )

        except Exception as e:
            logger.error(f"AI split decision failed for {file_path}: {e}")
            return False, f"AI analysis error: {e}", 0.0

    def _get_historical_patterns(
        self, file_path: str, complexity_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Get historical splitting patterns for similar files."""
        try:
            # Query learning memory system for similar patterns
            patterns = self.learning_system.get_fix_recommendations(
                "file_splitting", file_path
            )
            return patterns
        except Exception as e:
            logger.debug(f"Could not retrieve historical patterns: {e}")
            return []

    def _create_split_decision_prompt(
        self,
        file_path: str,
        content: str,
        complexity_data: dict[str, Any],
        patterns: list[dict[str, Any]],
        config: SplitConfig,
    ) -> str:
        """Create prompt for AI split decision."""

        # Get file preview (first and last 20 lines)
        lines = content.splitlines()
        preview_lines = lines[:20] + ["..."] + lines[-20:] if len(lines) > 40 else lines
        preview = "\n".join(preview_lines)

        prompt = f"""
Analyze the following Python file and determine if it should be split into smaller components.

File: {file_path}
Complexity Metrics:
- Total lines: {complexity_data['total_lines']}
- Total functions: {complexity_data['total_functions']}
- Total classes: {complexity_data['total_classes']}
- Max function complexity: {complexity_data['max_function_complexity']}
- File size: {complexity_data['file_size_bytes']} bytes
- Cyclomatic complexity: {complexity_data['cyclomatic_complexity']}

Configuration Thresholds:
- Max lines per file: {config.max_lines_per_file}
- Max functions per file: {config.max_functions_per_file}
- Max classes per file: {config.max_classes_per_file}
- Max cyclomatic complexity: {config.max_cyclomatic_complexity}
- Max file size: {config.max_file_size_bytes} bytes

Historical Patterns: {patterns}

File Preview:
{preview}

Based on the complexity metrics, configuration thresholds, and historical patterns, determine:

1. Should this file be split? (yes/no)
2. What is the reasoning for your decision?
3. What is your confidence level (0.0-1.0)?

Respond in this exact format:
DECISION: [yes/no]
REASONING: [detailed explanation]
CONFIDENCE: [0.0-1.0]
"""
        return prompt

    def _get_system_prompt(self) -> str:
        """Get system prompt for AI split decisions."""
        return """You are an expert code architect specializing in Python file organization and refactoring. Your task is to analyze Python files and determine if they should be split into smaller, more manageable components.

Consider the following factors:
1. Code complexity and maintainability
2. Single responsibility principle
3. Module cohesion and coupling
4. Performance implications
5. Team collaboration and code review efficiency

Provide clear, actionable decisions with confidence scores based on your analysis."""

    def _parse_ai_decision(self, response: str) -> dict[str, Any]:
        """Parse AI response into structured decision."""
        try:
            lines = response.strip().split("\n")
            decision = {"should_split": False, "reasoning": "", "confidence": 0.0}

            for line in lines:
                if line.startswith("DECISION:"):
                    decision["should_split"] = "yes" in line.lower()
                elif line.startswith("REASONING:"):
                    decision["reasoning"] = line.replace("REASONING:", "").strip()
                elif line.startswith("CONFIDENCE:"):
                    try:
                        confidence_str = line.replace("CONFIDENCE:", "").strip()
                        decision["confidence"] = float(confidence_str)
                    except ValueError:
                        decision["confidence"] = 0.5

            return decision

        except Exception as e:
            logger.error(f"Failed to parse AI decision: {e}")
            return {
                "should_split": False,
                "reasoning": "Failed to parse AI response",
                "confidence": 0.0,
            }

    def _learn_from_decision(
        self, file_path: str, complexity_data: dict[str, Any], decision: dict[str, Any]
    ):
        """Learn from the split decision for future improvements."""
        try:
            # Record the decision pattern in learning memory
            self.learning_system.record_fix_pattern(
                MemoryInputs(
                    action_type="record_fix",
                    file_path=file_path,
                    comment_type="file_splitting",
                    fix_applied="split_decision",
                    success=decision["should_split"],
                    context={
                        "complexity_data": complexity_data,
                        "reasoning": decision["reasoning"],
                        "confidence": decision["confidence"],
                    },
                )
            )
        except Exception as e:
            logger.debug(f"Failed to learn from split decision: {e}")


class FileSplitter:
    """AI-enhanced file splitter with learning capabilities."""

    def __init__(
        self,
        config: SplitConfig | None = None,
        llm_manager: LLMProviderManager | None = None,
        learning_system: LearningMemorySystem | None = None,
        metrics_collector: MetricsCollector | None = None,
    ):
        self.config = config or SplitConfig()
        self.llm_manager = llm_manager
        self.learning_system = learning_system or LearningMemorySystem()
        self.metrics_collector = metrics_collector or MetricsCollector()

        # Initialize components
        self.complexity_analyzer = FileComplexityAnalyzer()
        self.ai_decision_engine = (
            AISplitDecisionEngine(self.llm_manager, self.learning_system)
            if llm_manager
            else None
        )

        # Performance tracking
        self.split_history: list[dict[str, Any]] = []

    def should_split_file(self, file_path: str, content: str) -> tuple[bool, str]:
        """Determine if a file should be split based on complexity and AI analysis."""
        start_time = time.time()

        try:
            # Analyze file complexity
            complexity_data = self.complexity_analyzer.analyze_file_complexity(
                file_path, content
            )

            # Check basic complexity thresholds
            should_split, reasoning = (
                self.complexity_analyzer.should_split_by_complexity(
                    complexity_data, self.config
                )
            )

            # If basic thresholds are met, use AI for final decision
            if should_split and self.config.use_ai_analysis and self.ai_decision_engine:
                ai_should_split, ai_reasoning, confidence = (
                    self.ai_decision_engine.analyze_split_decision(
                        file_path, content, complexity_data, self.config
                    )
                )

                # Override basic decision with AI decision if confidence is high enough
                if confidence >= self.config.confidence_threshold:
                    should_split = ai_should_split
                    reasoning = (
                        f"AI decision (confidence: {confidence:.2f}): {ai_reasoning}"
                    )
                else:
                    reasoning = f"AI confidence too low ({confidence:.2f} < {self.config.confidence_threshold}), using basic analysis: {reasoning}"

            # Record metrics
            processing_time = time.time() - start_time
            self._record_split_analysis(
                file_path, complexity_data, should_split, reasoning, processing_time
            )

            return should_split, reasoning

        except Exception as e:
            logger.error(f"Error analyzing file {file_path} for splitting: {e}")
            return False, f"Analysis error: {e}"

    def split_file(self, file_path: str, content: str) -> SplitResult:
        """Split a file into smaller components."""
        start_time = time.time()

        try:
            # Check if splitting is needed
            should_split, reasoning = self.should_split_file(file_path, content)

            if not should_split:
                return SplitResult(
                    success=True,
                    original_file=file_path,
                    split_strategy="no_split_needed",
                    reasoning=reasoning,
                    processing_time=time.time() - start_time,
                    confidence_score=1.0,
                )

            # Create backup if enabled
            backup_created = False
            if self.config.create_backups:
                backup_created = self._create_backup(file_path)

            # Analyze file structure
            complexity_data = self.complexity_analyzer.analyze_file_complexity(
                file_path, content
            )

            # Choose splitting strategy
            strategy = self._choose_splitting_strategy(complexity_data, content)

            # Execute splitting
            components = self._execute_splitting_strategy(strategy, file_path, content)

            # Validate splits if enabled
            validation_passed = True
            if self.config.validate_splits:
                validation_passed = self._validate_split_components(components)

            # Record split in history
            self._record_split_result(
                file_path, strategy, components, validation_passed
            )

            processing_time = time.time() - start_time

            return SplitResult(
                success=True,
                original_file=file_path,
                components=components,
                split_strategy=strategy,
                reasoning=reasoning,
                processing_time=processing_time,
                confidence_score=0.9 if validation_passed else 0.5,
                backup_created=backup_created,
                validation_passed=validation_passed,
            )

        except Exception as e:
            logger.error(f"Error splitting file {file_path}: {e}")
            return SplitResult(
                success=False,
                original_file=file_path,
                error_message=str(e),
                processing_time=time.time() - start_time,
            )

    def _choose_splitting_strategy(
        self, complexity_data: dict[str, Any], content: str
    ) -> str:
        """Choose the best splitting strategy based on file characteristics."""
        if complexity_data["total_classes"] > complexity_data["total_functions"]:
            return "class_based"
        elif complexity_data["total_functions"] > 10:
            return "function_based"
        elif complexity_data["total_lines"] > 500:
            return "section_based"
        else:
            return "module_based"

    def _execute_splitting_strategy(
        self, strategy: str, file_path: str, content: str
    ) -> list[SplitComponent]:
        """Execute the chosen splitting strategy."""
        if strategy == "class_based":
            return self._split_by_classes(file_path, content)
        elif strategy == "function_based":
            return self._split_by_functions(file_path, content)
        elif strategy == "section_based":
            return self._split_by_sections(file_path, content)
        else:
            return self._split_by_modules(file_path, content)

    def _split_by_classes(self, file_path: str, content: str) -> list[SplitComponent]:
        """Split file by classes."""
        components = []
        lines = content.splitlines()

        try:
            tree = ast.parse(content)

            # Extract imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.append(ast.unparse(node))

            # Split by classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_content = ast.unparse(node)

                    # Add imports to class component
                    full_content = "\n".join(imports + [class_content])

                    component = SplitComponent(
                        name=node.name,
                        content=full_content,
                        start_line=node.lineno,
                        end_line=node.end_lineno or node.lineno,
                        component_type="class",
                        dependencies=self._extract_dependencies(node),
                        complexity_score=self._calculate_complexity_score(node),
                        file_path=f"{file_path}_{node.name}",
                    )
                    components.append(component)

            return components

        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return []

    def _split_by_functions(self, file_path: str, content: str) -> list[SplitComponent]:
        """Split file by functions."""
        components = []
        lines = content.splitlines()

        try:
            tree = ast.parse(content)

            # Extract imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.append(ast.unparse(node))

            # Group functions by module level
            module_functions = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not any(
                        isinstance(parent, ast.ClassDef)
                        for parent in ast.walk(tree)
                        if hasattr(parent, "body") and node in parent.body
                    ):
                        module_functions.append(node)

            # Create components for function groups
            if module_functions:
                function_content = "\n".join(
                    ast.unparse(func) for func in module_functions
                )
                full_content = "\n".join(imports + [function_content])

                component = SplitComponent(
                    name="functions",
                    content=full_content,
                    start_line=module_functions[0].lineno,
                    end_line=module_functions[-1].end_lineno
                    or module_functions[-1].lineno,
                    component_type="functions",
                    dependencies=[],
                    complexity_score=len(module_functions),
                    file_path=f"{file_path}_functions",
                )
                components.append(component)

            return components

        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return []

    def _split_by_sections(self, file_path: str, content: str) -> list[SplitComponent]:
        """Split file by logical sections."""
        components = []
        lines = content.splitlines()

        # Simple section-based splitting (can be enhanced with AI)
        section_size = max(100, len(lines) // 3)  # Split into ~3 sections

        for i in range(0, len(lines), section_size):
            section_lines = lines[i : i + section_size]
            section_content = "\n".join(section_lines)

            component = SplitComponent(
                name=f"section_{i//section_size + 1}",
                content=section_content,
                start_line=i + 1,
                end_line=min(i + section_size, len(lines)),
                component_type="section",
                dependencies=[],
                complexity_score=len(section_lines),
                file_path=f"{file_path}_section_{i//section_size + 1}",
            )
            components.append(component)

        return components

    def _split_by_modules(self, file_path: str, content: str) -> list[SplitComponent]:
        """Split file by modules (default strategy)."""
        # For now, return the original file as a single component
        return [
            SplitComponent(
                name="main",
                content=content,
                start_line=1,
                end_line=len(content.splitlines()),
                component_type="module",
                dependencies=[],
                complexity_score=1.0,
                file_path=file_path,
            )
        ]

    def _extract_dependencies(self, node: ast.AST) -> list[str]:
        """Extract dependencies from an AST node."""
        dependencies = []
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                dependencies.append(child.id)
            elif isinstance(child, ast.Attribute):
                if isinstance(child.value, ast.Name):
                    dependencies.append(f"{child.value.id}.{child.attr}")
        return list(set(dependencies))

    def _calculate_complexity_score(self, node: ast.AST) -> float:
        """Calculate complexity score for an AST node."""
        visitor = ComplexityVisitor()
        visitor.visit(node)
        return visitor.total_cyclomatic_complexity

    def _create_backup(self, file_path: str) -> bool:
        """Create a backup of the original file."""
        try:
            backup_path = f"{file_path}.backup_{int(time.time())}"
            with open(file_path, encoding="utf-8") as src:
                with open(backup_path, "w", encoding="utf-8") as dst:
                    dst.write(src.read())
            logger.info(f"Created backup: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup for {file_path}: {e}")
            return False

    def _validate_split_components(self, components: list[SplitComponent]) -> bool:
        """Validate that split components are syntactically correct."""
        for component in components:
            try:
                ast.parse(component.content)
            except SyntaxError as e:
                logger.error(f"Syntax error in component {component.name}: {e}")
                return False
        return True

    def _record_split_analysis(
        self,
        file_path: str,
        complexity_data: dict[str, Any],
        should_split: bool,
        reasoning: str,
        processing_time: float,
    ):
        """Record split analysis metrics."""
        if self.metrics_collector:
            self.metrics_collector.record_fix_attempt(
                success=should_split,
                processing_time=processing_time,
            )

    def _record_split_result(
        self,
        file_path: str,
        strategy: str,
        components: list[SplitComponent],
        validation_passed: bool,
    ):
        """Record split result in history."""
        self.split_history.append(
            {
                "file_path": file_path,
                "strategy": strategy,
                "components_count": len(components),
                "validation_passed": validation_passed,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def get_split_statistics(self) -> dict[str, Any]:
        """Get statistics about file splitting operations."""
        if not self.split_history:
            return {"total_splits": 0, "success_rate": 0.0}

        total_splits = len(self.split_history)
        successful_splits = sum(
            1 for split in self.split_history if split["validation_passed"]
        )
        success_rate = successful_splits / total_splits if total_splits > 0 else 0.0

        strategy_counts = {}
        for split in self.split_history:
            strategy = split["strategy"]
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        return {
            "total_splits": total_splits,
            "successful_splits": successful_splits,
            "success_rate": success_rate,
            "strategy_distribution": strategy_counts,
            "average_components_per_split": sum(
                split["components_count"] for split in self.split_history
            )
            / total_splits,
        }


# Global instance for convenience
file_splitter = FileSplitter()
