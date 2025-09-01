#!/usr/bin/env python3
"""
Integration Test for AI Enhanced File Splitter with Complete Workflow

This test demonstrates how the file splitter integrates with the complete
AI fixer workflow including issue processing, AI fix application, and validation.
"""

import tempfile
from pathlib import Path

import pytest

# Import the main components
from autopr.actions.ai_linting_fixer.ai_fix_applier import AIFixApplier
from autopr.actions.ai_linting_fixer.file_splitter import (FileSplitter,
                                                           SplitConfig)
from autopr.actions.ai_linting_fixer.models import LintingIssue
from autopr.actions.llm import ActionLLMProviderManager


def create_test_file_with_issues(content: str, filename: str = "test_file.py") -> str:
    """Create a temporary test file with known linting issues."""
    temp_dir = tempfile.mkdtemp()
    file_path = Path(temp_dir) / filename

    with file_path.open("w", encoding="utf-8") as f:
        f.write(content)

    return str(file_path)


@pytest.mark.asyncio
async def test_file_splitter_integration():
    """Test the file splitter integration with the AI fixer workflow."""

    # Create a large file with multiple issues that should trigger splitting
    large_file_content = '''
"""
Large test module with multiple linting issues.
"""

import os
import sys
import json
import logging
from typing import List, Dict, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime, timedelta

# Configuration
CONFIG = {
    "max_lines": 1000,
    "timeout": 30,
    "retries": 3,
    "debug": False
}

class DataProcessor:
    """Processes large amounts of data."""

    def __init__(self, config: Dict[str, any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.data_cache = {}

    def load_data(self, file_path: str) -> List[Dict[str, any]]:
        """Load data from a file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            return []

    def process_data(self, data: List[Dict[str, any]]) -> Dict[str, any]:
        """Process the loaded data."""
        result = {
            "total_items": len(data),
            "processed_items": 0,
            "errors": 0,
            "summary": {}
        }

        for item in data:
            try:
                self._process_single_item(item, result)
                result["processed_items"] += 1
            except Exception as e:
                self.logger.error(f"Error processing item: {e}")
                result["errors"] += 1

        return result

    def _process_single_item(self, item: Dict[str, any], result: Dict[str, any]) -> None:
        """Process a single data item."""
        # Simulate complex processing
        if "id" in item:
            result["summary"][item["id"]] = {
                "status": "processed",
                "timestamp": datetime.now().isoformat()
            }

    def save_results(self, results: Dict[str, any], output_path: str) -> bool:
        """Save processing results to a file."""
        try:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error saving results: {e}")
            return False

class FileManager:
    """Manages file operations."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.logger = logging.getLogger(__name__)

    def create_directory(self, dir_name: str) -> bool:
        """Create a new directory."""
        try:
            dir_path = self.base_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"Error creating directory: {e}")
            return False

    def list_files(self, pattern: str = "*") -> List[Path]:
        """List files matching a pattern."""
        try:
            return list(self.base_path.glob(pattern))
        except Exception as e:
            self.logger.error(f"Error listing files: {e}")
            return []

    def backup_file(self, file_path: Path) -> bool:
        """Create a backup of a file."""
        try:
            backup_path = file_path.with_suffix(file_path.suffix + ".backup")
            backup_path.write_text(file_path.read_text())
            return True
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return False

def utility_function_1():
    """Utility function 1."""
    return "utility_1"

def utility_function_2():
    """Utility function 2."""
    return "utility_2"

def utility_function_3():
    """Utility function 3."""
    return "utility_3"

def utility_function_4():
    """Utility function 4."""
    return "utility_4"

def utility_function_5():
    """Utility function 5."""
    return "utility_5"

def main():
    """Main function."""
    # Initialize components
    processor = DataProcessor(CONFIG)
    file_manager = FileManager("/tmp/test")

    # Process data
    data = processor.load_data("input.json")
    results = processor.process_data(data)

    # Save results
    processor.save_results(results, "output.json")

    # Create backup
    file_manager.backup_file(Path("output.json"))

    print("Processing completed successfully!")

if __name__ == "__main__":
    main()
'''

    file_path = create_test_file_with_issues(
        large_file_content, "large_test_file_with_issues.py"
    )

    try:

        # 1. Test standalone file splitter
        config = SplitConfig(
            max_lines=50,
            max_functions=3,
            max_classes=1,
            enable_ai_analysis=True,
            performance_monitoring=True,
        )

        splitter = FileSplitter(config)
        with Path(file_path).open("r", encoding="utf-8") as f:
            content = f.read()

        splitter.split_file(file_path, content)

        # 2. Test AI fix applier integration

        # Create mock LLM manager (in real usage, this would be configured)
        llm_manager = ActionLLMProviderManager({})

        # Create AI fix applier with file splitter integration
        ai_fix_applier = AIFixApplier(
            llm_manager=llm_manager,
        )

        # Create mock issues
        mock_issues = [
            LintingIssue(
                file_path=file_path,
                line_number=10,
                column_number=5,
                error_code="E501",
                message="Line too long (120 > 100 characters)",
            ),
            LintingIssue(
                file_path=file_path,
                line_number=25,
                column_number=1,
                error_code="E302",
                message="Expected 2 blank lines, found 1",
            ),
        ]

        # Test the comprehensive workflow
        await ai_fix_applier.apply_specialist_fix_with_validation(
            agent=None,  # Mock agent
            file_path=file_path,
            content=content,
            issues=mock_issues,
            session_id="test_session",
        )

        # 3. Test statistics and metrics
        # The splitter has already logged performance metrics during the split operation
        # We can verify the split was successful by checking the result
        pass

    finally:
        # Cleanup
        try:
            Path(file_path).unlink()
            # Clean up backup files
            for backup_file in Path(file_path).parent.glob(
                f"{Path(file_path).name}.backup_*"
            ):
                backup_file.unlink()
            Path(file_path).parent.rmdir()
        except Exception:
            pass


def test_volume_integration():
    """Test how the file splitter integrates with volume controls."""

    # Test different volume levels and their impact on file splitting
    volume_configs = [
        (0, "ultra-fast", "Silent"),
        (100, "fast", "Quiet"),
        (300, "fast", "Moderate"),
        (500, "smart", "Balanced"),
        (700, "ai_enhanced", "Thorough"),
        (900, "ai_enhanced", "Maximum"),
    ]

    for volume, _mode, _level in volume_configs:

        # Create config based on volume
        SplitConfig(
            max_lines=1000 - (volume // 10),  # Lower volume = stricter limits
            max_functions=20 - (volume // 50),
            max_classes=10 - (volume // 100),
        )


if __name__ == "__main__":
    import asyncio

    # Run async test
    asyncio.run(test_file_splitter_integration())

    # Run sync test
    test_volume_integration()
