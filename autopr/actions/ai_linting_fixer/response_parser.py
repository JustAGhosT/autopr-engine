"""
Response Parser Module

Handles parsing and extraction of code from LLM responses following the Single Responsibility Principle.
"""

import logging
import re


logger = logging.getLogger(__name__)


class ResponseParser:
    """Parses LLM responses to extract code and metadata."""

    def extract_code_from_response(self, response_content: str) -> str | None:
        """Extract code from LLM response.
        
        Args:
            response_content: Raw response content from LLM
            
        Returns:
            Extracted code or None if no valid code found
        """
        if not response_content:
            return None

        # Try to extract from code blocks first
        code_block_patterns = [
            r"```python\n(.*?)\n```",
            r"```\n(.*?)\n```",
            r"<code>(.*?)</code>",
        ]

        for pattern in code_block_patterns:
            matches = re.findall(pattern, response_content, re.DOTALL)
            if matches:
                code = matches[0].strip()
                if self._is_valid_python_structure(code):
                    return code

        # If no code blocks, look for complete Python structures
        lines = response_content.split('\n')
        code_lines = []
        in_code = False

        for line in lines:
            if any(keyword in line for keyword in ["def ", "class ", "import ", "from "]):
                in_code = True
                code_lines.append(line)
            elif in_code and line.strip():
                code_lines.append(line)
            elif in_code and not line.strip():
                # Empty line in code block
                code_lines.append(line)

        if code_lines:
            code = '\n'.join(code_lines)
            if self._is_valid_python_structure(code):
                return code

        logger.warning("No valid code structure found in response")
        return None

    def _is_valid_python_structure(self, code: str) -> bool:
        """Check if code contains valid Python structures.
        
        Args:
            code: Code to validate
            
        Returns:
            True if code appears to be valid Python
        """
        if not code or not code.strip():
            return False

        lines = [line.strip() for line in code.split('\n') if line.strip()]

        # Must have some actual content
        if not lines:
            return False

        # Check for Python keywords that indicate real code
        python_indicators = [
            "def ", "class ", "import ", "from ", "if ", "for ", "while ",
            "try:", "except", "with ", "return", "yield", "async def", "await"
        ]

        has_python_structure = any(
            any(indicator in line for indicator in python_indicators)
            for line in lines
        )

        return has_python_structure

    def is_complete_file(self, code: str) -> bool:
        """Determine if code represents a complete file replacement.
        
        Args:
            code: Code to analyze
            
        Returns:
            True if code appears to be a complete file
        """
        if not code:
            return False

        lines = [line.strip() for line in code.split('\n') if line.strip()]

        # 1. Must have significant content (more than just a few lines)
        if len(lines) < 5:
            return False

        # 2. Has class or function definitions
        has_definitions = any("def " in line or "class " in line for line in lines)

        # 3. Has imports (usually indicates full file)
        has_imports = any(line.startswith("import ") or line.startswith("from ") for line in lines)

        # 4. Has docstrings or comments (indicates complete context)
        has_docs = any('"""' in line or "'''" in line or line.startswith("#") for line in lines)

        # Complete file typically has multiple indicators
        indicators = sum([has_definitions, has_imports, has_docs])
        return indicators >= 2

    def extract_targeted_changes(self, full_response: str, code_block: str) -> str:
        """Extract targeted line changes from response.
        
        Args:
            full_response: Complete LLM response
            code_block: Extracted code block
            
        Returns:
            Processed targeted changes
        """
        # Look for line-specific change patterns
        change_patterns = [
            r"Line (\d+):\s*(.*?)(?=\nLine|\n\n|$)",
            r"(?:Replace|Change|Fix) line (\d+):\s*(.*?)(?=\n|$)",
        ]

        changes = {}
        for pattern in change_patterns:
            matches = re.findall(pattern, full_response, re.MULTILINE | re.DOTALL)
            for line_num, change in matches:
                try:
                    changes[int(line_num)] = change.strip()
                except ValueError:
                    continue

        if changes:
            # Apply targeted changes to create modified code
            original_lines = code_block.split('\n')
            modified_lines = original_lines.copy()

            for line_num, new_content in changes.items():
                if 1 <= line_num <= len(modified_lines):
                    modified_lines[line_num - 1] = new_content

            return '\n'.join(modified_lines)

        # If no targeted changes found, return original code block
        return code_block

    def parse_strategy_response(self, response_content: str) -> dict[str, str]:
        """Parse strategy selection response.
        
        Args:
            response_content: LLM response about strategy selection
            
        Returns:
            Dictionary with strategy and reasoning
        """
        if not response_content:
            return {"strategy": "targeted", "reasoning": "No response received"}

        content_lower = response_content.lower()

        # Look for strategy indicators
        if "full" in content_lower and "file" in content_lower:
            strategy = "full_file"
        elif "targeted" in content_lower or "specific" in content_lower:
            strategy = "targeted"
        else:
            # Default fallback
            strategy = "targeted"

        # Extract reasoning if present
        reasoning_patterns = [
            r"reason(?:ing)?[:\s]+(.*?)(?=\n\n|\n[A-Z]|$)",
            r"because[:\s]+(.*?)(?=\n\n|\n[A-Z]|$)",
            r"explanation[:\s]+(.*?)(?=\n\n|\n[A-Z]|$)",
        ]

        reasoning = "Strategy selection based on analysis"
        for pattern in reasoning_patterns:
            matches = re.findall(pattern, response_content, re.IGNORECASE | re.DOTALL)
            if matches:
                reasoning = matches[0].strip()
                break

        return {"strategy": strategy, "reasoning": reasoning}
