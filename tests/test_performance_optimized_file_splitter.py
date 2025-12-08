"""
Test Performance Optimized File Splitter

Tests for performance optimized file splitting functionality.
"""

import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest

from codeflow_engine.actions.ai_linting_fixer.analyzers.complexity_analyzer import \
    FileComplexityAnalyzer
from codeflow_engine.actions.ai_linting_fixer.engines.ai_split_decision_engine import \
    AISplitDecisionEngine
from codeflow_engine.actions.ai_linting_fixer.file_splitter import (FileSplitter,
                                                           SplitConfig)
from codeflow_engine.actions.ai_linting_fixer.models import LintingIssue
from codeflow_engine.actions.ai_linting_fixer.performance_optimizer import (
    IntelligentCache, ParallelProcessor)
from codeflow_engine.ai.core.providers.manager import LLMProviderManager
from codeflow_engine.quality.metrics_collector import MetricsCollector


# Create a compatibility class for the tests
class PerformanceOptimizer:
    """Compatibility wrapper for old PerformanceOptimizer interface."""
    
    def __init__(self):
        self.cache = IntelligentCache()
        self.parallel_processor = ParallelProcessor()
        
    def cleanup(self):
        """Cleanup resources."""
        # Clean up cache and parallel processor resources
        if hasattr(self.cache, 'cleanup'):
            self.cache.cleanup()
        if hasattr(self.parallel_processor, 'cleanup'):
            self.parallel_processor.cleanup()


class TestPerformanceOptimizedFileSplitter:
    """Test suite for the performance-optimized file splitter."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def performance_optimizer(self):
        """Create a performance optimizer instance."""
        return PerformanceOptimizer()

    @pytest.fixture
    def llm_manager(self):
        """Create a mock LLM manager."""
        config = {
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
        return LLMProviderManager(config)

    @pytest.fixture
    def metrics_collector(self):
        """Create a metrics collector instance."""
        return MetricsCollector()

    @pytest.fixture
    def file_splitter(self, llm_manager, metrics_collector, performance_optimizer):
        """Create a file splitter instance."""
        return FileSplitter(
            llm_manager=llm_manager,
            metrics_collector=metrics_collector,
            parallel_processor=performance_optimizer.parallel_processor,
        )

    @pytest.fixture
    def large_test_file(self, temp_dir):
        """Create a large test file to trigger splitting."""
        file_path = Path(temp_dir) / "large_test_file.py"
        content = []

        # Add imports
        content.append("import os")
        content.append("import sys")
        content.append("from typing import List, Dict, Any")
        content.append("")

        # Add many functions to trigger splitting
        for i in range(50):
            content.append(f"def function_{i}(param: str) -> str:")
            content.append(f'    """Function {i} with some complexity."""')
            content.append("    if param == 'test':")
            content.append(f"        return f'result_{i}'")
            content.append("    elif param == 'complex':")
            content.append("        for j in range(10):")
            content.append("            if j % 2 == 0:")
            content.append("                continue")
            content.append("        return 'complex_result'")
            content.append("    else:")
            content.append("        return 'default'")
            content.append("")

        # Add a class
        content.append("class TestClass:")
        content.append('    """A test class with methods."""')
        content.append("    def __init__(self):")
        content.append("        self.value = None")
        content.append("    ")
        content.append("    def method1(self):")
        content.append("        return 'method1'")
        content.append("    ")
        content.append("    def method2(self):")
        content.append("        return 'method2'")
        content.append("")

        file_path.write_text("\n".join(content))
        return str(file_path)

    @pytest.fixture
    def small_test_file(self, temp_dir):
        """Create a small test file that shouldn't be split."""
        file_path = Path(temp_dir) / "small_test_file.py"
        content = '''def simple_function():
    """A simple function."""
    return "hello world"

def another_function():
    """Another simple function."""
    return "goodbye world"
'''
        file_path.write_text(content)
        return str(file_path)

    def test_performance_optimizer_initialization(self, performance_optimizer):
        """Test that the performance optimizer initializes correctly."""
        assert performance_optimizer is not None
        assert hasattr(performance_optimizer, "cache")
        assert hasattr(performance_optimizer, "parallel_processor")

    def test_cache_manager_functionality(self, performance_optimizer):
        """Test cache manager functionality."""
        cache_manager = performance_optimizer.cache

        # Test set and get
        cache_manager.set("test_key", "test_value", ttl_seconds=60)
        result = cache_manager.get("test_key")
        assert result == "test_value"

        # Test cache miss
        result = cache_manager.get("nonexistent_key")
        assert result is None

        # Test stats
        stats = cache_manager.get_stats()
        assert "hits" in stats
        assert "misses" in stats

    def test_file_complexity_analyzer_with_caching(self, performance_optimizer):
        """Test file complexity analyzer with caching."""
        analyzer = FileComplexityAnalyzer(performance_optimizer.cache)

        content = """def test_function():
    if True:
        for i in range(10):
            if i % 2 == 0:
                print(i)
    return "done"

class TestClass:
    def method(self):
        return "method"
"""

        # First analysis (cache miss)
        result1 = analyzer.analyze_file_complexity("test.py", content)
        assert "total_lines" in result1
        assert "total_functions" in result1
        assert "total_classes" in result1
        assert "complexity_score" in result1

        # Second analysis (cache hit)
        result2 = analyzer.analyze_file_complexity("test.py", content)
        assert result1 == result2

        # Check cache stats
        cache_stats = performance_optimizer.cache.get_stats()
        assert cache_stats["hits"] > 0

    @pytest.mark.asyncio
    async def test_ai_split_decision_engine_with_caching(
        self, llm_manager, performance_optimizer
    ):
        """Test AI split decision engine with caching."""
        engine = AISplitDecisionEngine(llm_manager, performance_optimizer.cache)

        content = "def test(): pass"
        complexity = {
            "total_lines": 1,
            "total_functions": 1,
            "total_classes": 0,
            "complexity_score": 1.0,
        }

        # First decision (cache miss)
        should_split1, confidence1, reason1 = await engine.should_split_file(
            "test.py", content, complexity
        )
        assert isinstance(should_split1, bool)
        assert isinstance(confidence1, float)
        assert isinstance(reason1, str)

        # Second decision (cache hit)
        should_split2, confidence2, reason2 = await engine.should_split_file(
            "test.py", content, complexity
        )
        assert should_split1 == should_split2
        assert confidence1 == confidence2
        assert reason1 == reason2

    @pytest.mark.asyncio
    async def test_file_splitter_with_small_file(self, file_splitter, small_test_file):
        """Test file splitter with a small file that shouldn't be split."""
        with open(small_test_file) as f:
            content = f.read()

        config = SplitConfig(
            max_lines=50,
            max_functions=5,
            enable_ai_analysis=True,
            enable_caching=True,
            enable_parallel_processing=True,
            enable_memory_optimization=True,
        )

        result = await file_splitter.split_file(small_test_file, content, config)

        assert result.success is True
        assert len(result.components) == 0  # Should not split small file
        assert result.processing_time > 0
        assert result.cache_hits >= 0
        assert result.cache_misses >= 0
        assert result.memory_usage_mb >= 0
        assert isinstance(result.performance_metrics, dict)

    @pytest.mark.asyncio
    async def test_file_splitter_with_large_file(self, file_splitter, large_test_file):
        """Test file splitter with a large file that should be split."""
        with open(large_test_file) as f:
            content = f.read()

        config = SplitConfig(
            max_lines=100,
            max_functions=10,
            enable_ai_analysis=True,
            enable_caching=True,
            enable_parallel_processing=True,
            enable_memory_optimization=True,
            max_parallel_workers=2,
        )

        result = await file_splitter.split_file(large_test_file, content, config)

        assert result.success is True
        assert len(result.components) > 0  # Should split large file
        assert result.processing_time > 0
        assert result.cache_hits >= 0
        assert result.cache_misses >= 0
        assert result.memory_usage_mb >= 0
        assert isinstance(result.performance_metrics, dict)

        # Check component properties
        for component in result.components:
            assert hasattr(component, "name")
            assert hasattr(component, "component_type")
            assert hasattr(component, "start_line")
            assert hasattr(component, "end_line")
            assert hasattr(component, "content")
            assert hasattr(component, "complexity_score")

    @pytest.mark.asyncio
    async def test_parallel_processing_functionality(self, performance_optimizer):
        """Test parallel processing functionality."""
        parallel_processor = performance_optimizer.parallel_processor

        def test_function(x):
            """Test function for parallel processing."""
            time.sleep(0.1)  # Simulate work
            return x * 2

        # Test parallel processing
        inputs = [1, 2, 3, 4, 5]
        results = parallel_processor.process_parallel(inputs, test_function)

        assert len(results) == len(inputs)
        assert results == [2, 4, 6, 8, 10]

    def test_split_config_validation(self):
        """Test split configuration validation."""
        config = SplitConfig(
            max_lines=100,
            max_functions=10,
            max_classes=5,
            max_complexity=10.0,
            enable_ai_analysis=True,
            enable_caching=True,
            enable_parallel_processing=True,
            enable_memory_optimization=True,
            cache_ttl=3600,
            max_parallel_workers=4,
            memory_limit_mb=512,
            performance_monitoring=True,
        )

        assert config.max_lines == 100
        assert config.max_functions == 10
        assert config.enable_caching is True
        assert config.max_parallel_workers == 4

    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self, file_splitter, large_test_file):
        """Test that performance metrics are properly collected."""
        with open(large_test_file) as f:
            content = f.read()

        config = SplitConfig(performance_monitoring=True)

        result = await file_splitter.split_file(large_test_file, content, config)

        # Check performance metrics
        metrics = result.performance_metrics
        assert isinstance(metrics, dict)
        assert "cpu_usage" in metrics
        assert "memory_usage" in metrics
        assert "execution_time" in metrics

        # Check that metrics are reasonable
        assert metrics["execution_time"] > 0
        assert metrics["memory_usage"] >= 0

    def test_cache_ttl_functionality(self, performance_optimizer):
        """Test cache TTL functionality."""
        cache_manager = performance_optimizer.cache

        # Set with short TTL
        cache_manager.set("short_ttl", "value", ttl_seconds=1)

        # Should be available immediately
        result = cache_manager.get("short_ttl")
        assert result == "value"

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        result = cache_manager.get("short_ttl")
        assert result is None

    def test_cleanup_functionality(self, file_splitter):
        """Test cleanup functionality."""
        # The cleanup should not raise any exceptions
        file_splitter.cleanup()

    @pytest.mark.asyncio
    async def test_error_handling(self, file_splitter):
        """Test error handling in file splitter."""
        # Test with invalid content that would cause parsing errors
        invalid_content = "def invalid syntax { this is not valid python"
        result = await file_splitter.split_file(
            "test_file.py", invalid_content, SplitConfig()
        )

        # Should handle gracefully - the current implementation doesn't validate syntax
        # so it should succeed but with empty components
        assert result.success is True
        assert result.processing_time > 0

    def test_performance_optimizer_cleanup(self, performance_optimizer):
        """Test performance optimizer cleanup."""
        # Cleanup should not raise exceptions
        performance_optimizer.cleanup()


if __name__ == "__main__":
    pytest.main([__file__])
