#!/usr/bin/env python3
"""
Test File Splitter

Tests for file splitting functionality.
"""

from pathlib import Path
import tempfile

import pytest

from autopr.actions.ai_linting_fixer.analyzers.complexity_analyzer import FileComplexityAnalyzer
from autopr.actions.ai_linting_fixer.file_splitter import FileSplitter, SplitConfig


def create_test_file(content: str, filename: str = "test_file.py") -> str:
    """Create a temporary test file with the given content."""
    temp_dir = tempfile.mkdtemp()
    file_path = Path(temp_dir) / filename

    with file_path.open("w", encoding="utf-8") as f:
        f.write(content)

    return str(file_path)


def test_complexity_analysis():
    """Test the complexity analysis functionality."""
    # Create a test file with known complexity
    test_content = '''
"""
Test module with various complexity levels.
"""

import os
import sys
from typing import List, Dict, Optional

class TestClass:
    """A test class with multiple methods."""

    def __init__(self, name: str):
        self.name = name
        self.data = []

    def add_data(self, item: str) -> None:
        """Add an item to the data list."""
        self.data.append(item)

    def get_data(self) -> List[str]:
        """Get all data items."""
        return self.data.copy()

    def process_data(self) -> Dict[str, int]:
        """Process the data and return statistics."""
        result = {}
        for item in self.data:
            result[item] = len(item)
        return result

def simple_function():
    """A simple function."""
    return "Hello, World!"

def complex_function(data: List[str]) -> Dict[str, int]:
    """A more complex function."""
    result = {}
    for item in data:
        if item not in result:
            result[item] = 0
        result[item] += 1
    return result

def another_function():
    """Another function for testing."""
    return 42

if __name__ == "__main__":
    # Test the functionality
    test_obj = TestClass("test")
    test_obj.add_data("item1")
    test_obj.add_data("item2")
    print(test_obj.get_data())
    print(test_obj.process_data())
    print(simple_function())
    print(complex_function(["a", "b", "a", "c"]))
    print(another_function())
'''

    file_path = create_test_file(test_content)

    try:
        # Test complexity analysis
        analyzer = FileComplexityAnalyzer()
        with Path(file_path).open("r", encoding="utf-8") as f:
            content = f.read()
        complexity = analyzer.analyze_file_complexity(file_path, content)

        # Verify the analysis
        assert complexity["total_lines"] > 0
        assert complexity["total_functions"] > 0
        assert complexity["total_classes"] > 0
        assert complexity["file_size_bytes"] > 0
        assert complexity["cyclomatic_complexity"] >= 0

    finally:
        # Cleanup
        Path(file_path).unlink()
        Path(file_path).parent.rmdir()


@pytest.mark.asyncio
async def test_file_splitting():
    """Test the file splitting functionality."""
    # Create a large test file that should be split
    large_content = '''
"""
Large test module that should be split.
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

class NetworkManager:
    """Manages network operations."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    def download_file(self, url: str, local_path: str) -> bool:
        """Download a file from a URL."""
        try:
            # Simulate download
            self.logger.info(f"Downloading {url} to {local_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error downloading file: {e}")
            return False

    def upload_file(self, local_path: str, url: str) -> bool:
        """Upload a file to a URL."""
        try:
            # Simulate upload
            self.logger.info(f"Uploading {local_path} to {url}")
            return True
        except Exception as e:
            self.logger.error(f"Error uploading file: {e}")
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
    network_manager = NetworkManager()

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

    file_path = create_test_file(large_content, "large_test_file.py")
    result = None

    try:
        # Test file splitting
        config = SplitConfig(
            max_lines=50,
            max_functions=3,
            max_classes=1,
        )

        # Create a mock LLM manager for testing
        from autopr.ai.core.providers.manager import LLMProviderManager

        llm_config = {
            "providers": {
                "openai": {
                    "api_key": "test_key",
                    "default_model": "gpt-4",
                    "max_tokens": 1000,
                    "temperature": 0.1,
                }
            },
            "fallback_order": ["openai"],
            "default_provider": "openai",
        }
        llm_manager = LLMProviderManager(llm_config)

        splitter = FileSplitter(llm_manager)
        with Path(file_path).open("r", encoding="utf-8") as f:
            content = f.read()
        result = await splitter.split_file(file_path, content, config)

        if result.success:
            for _i, component in enumerate(result.components):
                pass

        # Verify the splitting
        assert result.success
        assert len(result.components) > 0
        assert result.processing_time > 0

    finally:
        # Cleanup
        try:
            Path(file_path).unlink()
            # Also clean up backup files
            Path(file_path).parent / f"{Path(file_path).name}.backup_*"
            for backup_file in Path(file_path).parent.glob(
                f"{Path(file_path).name}.backup_*"
            ):
                backup_file.unlink()
            # Clean up split components
            if result is not None:
                for component in result.components:
                    if (
                        hasattr(component, "file_path")
                        and Path(component.file_path).exists()
                    ):
                        Path(component.file_path).unlink()
            Path(file_path).parent.rmdir()
        except Exception:
            pass


@pytest.mark.asyncio
async def test_integration():
    """Test the complete integration of the file splitter."""
    # Create a test file
    test_content = '''
"""
Integration test module.
"""

import os
from typing import List

class TestClass:
    def method1(self):
        return "method1"

    def method2(self):
        return "method2"

def function1():
    return "function1"

def function2():
    return "function2"

def function3():
    return "function3"
'''

    file_path = create_test_file(test_content, "integration_test.py")

    try:
        # Create a mock LLM manager for testing
        from autopr.ai.core.providers.manager import LLMProviderManager

        llm_config = {
            "providers": {
                "openai": {
                    "api_key": "test_key",
                    "default_model": "gpt-4",
                    "max_tokens": 1000,
                    "temperature": 0.1,
                }
            },
            "fallback_order": ["openai"],
            "default_provider": "openai",
        }
        llm_manager = LLMProviderManager(llm_config)

        # Test with different configurations
        configs = [
            SplitConfig(max_lines=10, max_functions=1),
            SplitConfig(max_lines=20, max_functions=2),
            SplitConfig(max_lines=50, max_functions=5),
        ]

        for _i, config in enumerate(configs):

            splitter = FileSplitter(llm_manager)
            with Path(file_path).open("r", encoding="utf-8") as f:
                content = f.read()
            await splitter.split_file(file_path, content, config)

    finally:
        # Cleanup
        Path(file_path).unlink()
        Path(file_path).parent.rmdir()


if __name__ == "__main__":
    import asyncio

    # Run sync test
    test_complexity_analysis()

    # Run async tests
    asyncio.run(test_file_splitting())
    asyncio.run(test_integration())
