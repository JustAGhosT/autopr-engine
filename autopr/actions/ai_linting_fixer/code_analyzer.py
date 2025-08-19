"""
Code Analyzer Module

This module handles code analysis, validation, and complexity calculations.
"""

import ast
import logging

try:
    import psutil  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional dependency in tests/CI
    psutil = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """Handles code analysis and validation."""

    def __init__(self):
        """Initialize the code analyzer."""

    def validate_python_syntax(self, content: str) -> bool:
        """Validate Python syntax of content."""
        try:
            ast.parse(content)
            return True
        except SyntaxError as e:
            logger.debug(f"Syntax validation failed: {e}")
            return False
        except Exception as e:
            logger.debug(f"Unexpected error during syntax validation: {e}")
            return False

    def check_import_usage(self, file_content: str, import_line: str) -> bool:
        """Check if an import is actually used in the file content."""
        try:
            # Extract the imported name(s)
            import_parts = import_line.strip()

            # Handle different import patterns
            if import_parts.startswith("from "):
                # from module import name1, name2
                if " import " in import_parts:
                    import_names = import_parts.split(" import ")[1]
                    names = [name.strip() for name in import_names.split(",")]
                else:
                    return True  # Conservative: assume it's used if we can't parse
            elif import_parts.startswith("import "):
                # import module.submodule as alias
                import_part = import_parts[7:]  # Remove "import "
                if " as " in import_part:
                    names = [import_part.split(" as ")[1].strip()]
                else:
                    names = [import_part.split(".")[0].strip()]  # First part of module
            else:
                return True  # Conservative: assume it's used

            # Check if any of the names are used in the content
            return any(name in file_content for name in names)
        except Exception as e:
            logger.debug(f"Error checking import usage: {e}")
            return True  # Conservative: assume it's used if analysis fails

    def calculate_file_complexity(self, content: str) -> float:
        """Calculate cyclomatic complexity of a Python file."""
        try:
            tree = ast.parse(content)
            complexity = 1  # Base complexity

            for node in ast.walk(tree):
                if isinstance(
                    node,
                    ast.If
                    | ast.While
                    | ast.For
                    | ast.AsyncFor
                    | ast.ExceptHandler
                    | ast.With
                    | ast.AsyncWith,
                ):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1

            return complexity
        except Exception as e:
            logger.debug(f"Error calculating complexity: {e}")
            return 1.0  # Default complexity

    def analyze_imports(self, content: str) -> dict[str, list[str]]:
        """Analyze imports in a Python file."""
        try:
            tree = ast.parse(content)
            imports = {"standard_library": [], "third_party": [], "local": []}

            # Common standard library modules
            stdlib_modules = {
                "os",
                "sys",
                "re",
                "json",
                "datetime",
                "time",
                "pathlib",
                "typing",
                "collections",
                "itertools",
                "functools",
                "logging",
                "subprocess",
                "threading",
                "asyncio",
                "urllib",
                "http",
                "sqlite3",
                "pickle",
                "hashlib",
                "base64",
                "random",
                "math",
            }

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split(".")[0]
                        if module_name in stdlib_modules:
                            imports["standard_library"].append(alias.name)
                        else:
                            imports["third_party"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module_name = node.module.split(".")[0] if node.module else ""
                    if module_name in stdlib_modules:
                        imports["standard_library"].append(node.module or "")
                    elif module_name.startswith("."):
                        imports["local"].append(node.module or "")
                    else:
                        imports["third_party"].append(node.module or "")

            return imports
        except Exception as e:
            logger.debug(f"Error analyzing imports: {e}")
            return {"standard_library": [], "third_party": [], "local": []}

    def count_lines_of_code(self, content: str) -> dict[str, int]:
        """Count different types of lines in the code."""
        lines = content.split("\n")

        total_lines = len(lines)
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        docstring_lines = 0

        in_docstring = False
        docstring_quotes = None

        for line in lines:
            stripped = line.strip()

            # Skip completely blank lines
            if not stripped:
                blank_lines += 1
                continue

            # Check for docstrings
            if '"""' in stripped or "'''" in stripped:
                if not in_docstring:
                    # Start of docstring
                    in_docstring = True
                    docstring_quotes = '"""' if '"""' in stripped else "'''"
                    docstring_lines += 1
                else:
                    # End of docstring
                    if docstring_quotes in stripped:
                        in_docstring = False
                        docstring_quotes = None
                    docstring_lines += 1
                continue

            if in_docstring:
                docstring_lines += 1
                continue

            # Check for comments
            if stripped.startswith("#"):
                comment_lines += 1
                continue

            # Must be code
            code_lines += 1

        return {
            "total_lines": total_lines,
            "code_lines": code_lines,
            "comment_lines": comment_lines,
            "blank_lines": blank_lines,
            "docstring_lines": docstring_lines,
        }

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            if psutil is None:
                return 0.0
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / 1024 / 1024  # Convert to MB
        except Exception as e:
            logger.debug(f"Error getting memory usage: {e}")
            return 0.0

    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        try:
            if psutil is None:
                return 0.0
            return psutil.cpu_percent(interval=0.1)
        except Exception as e:
            logger.debug(f"Error getting CPU usage: {e}")
            return 0.0

    def analyze_function_complexity(self, content: str) -> list[dict[str, any]]:
        """Analyze complexity of individual functions."""
        try:
            tree = ast.parse(content)
            functions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    func_info = {
                        "name": node.name,
                        "line_number": node.lineno,
                        "complexity": self._calculate_function_complexity(node),
                        "parameters": len(node.args.args),
                        "decorators": len(node.decorator_list),
                    }
                    functions.append(func_info)

            return functions
        except Exception as e:
            logger.debug(f"Error analyzing function complexity: {e}")
            return []

    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(
                child,
                ast.If
                | ast.While
                | ast.For
                | ast.AsyncFor
                | ast.ExceptHandler
                | ast.With
                | ast.AsyncWith,
            ):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def detect_code_smells(self, content: str) -> list[dict[str, any]]:
        """Detect common code smells and anti-patterns."""
        smells = []

        try:
            tree = ast.parse(content)

            # Check for long functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    func_complexity = self._calculate_function_complexity(node)
                    if func_complexity > 10:
                        smells.append(
                            {
                                "type": "high_complexity",
                                "line": node.lineno,
                                "name": node.name,
                                "complexity": func_complexity,
                                "message": f"Function '{node.name}' has high cyclomatic complexity ({func_complexity})",
                            }
                        )

            # Check for long lines
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                if len(line) > 120:
                    smells.append(
                        {
                            "type": "long_line",
                            "line": i,
                            "length": len(line),
                            "message": f"Line {i} is too long ({len(line)} characters)",
                        }
                    )

            # Check for unused imports (basic check)
            self.analyze_imports(content)
            # This is a simplified check - a more sophisticated analysis would be needed

        except Exception as e:
            logger.debug(f"Error detecting code smells: {e}")

        return smells

    def get_code_metrics(self, content: str) -> dict[str, any]:
        """Get comprehensive code metrics."""
        return {
            "complexity": self.calculate_file_complexity(content),
            "imports": self.analyze_imports(content),
            "lines_of_code": self.count_lines_of_code(content),
            "functions": self.analyze_function_complexity(content),
            "code_smells": self.detect_code_smells(content),
            "syntax_valid": self.validate_python_syntax(content),
        }
