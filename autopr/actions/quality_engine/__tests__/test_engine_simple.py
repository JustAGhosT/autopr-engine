"""
Simplified tests for Quality Engine core functionality.
"""

import pytest

from autopr.actions.quality_engine.models import QualityMode, QualityOutputs


class TestQualityEngineSimple:
    """Simplified test for Quality Engine core functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_files = ["test1.py", "test2.py"]

    def test_quality_mode_enum(self):
        """Test Quality Mode enumeration."""
        assert QualityMode.FAST.value == "fast"
        assert QualityMode.COMPREHENSIVE.value == "comprehensive"
        assert QualityMode.AI_ENHANCED.value == "ai_enhanced"
        assert QualityMode.SMART.value == "smart"

    def test_quality_outputs_model(self):
        """Test QualityOutputs model creation."""
        result = QualityOutputs(
            success=True,
            total_issues_found=5,
            total_issues_fixed=2,
            files_modified=["test.py"],
            issues_by_tool={"ruff": [{"issue": "test"}]},
            files_by_tool={"ruff": ["test.py"]},
            summary="Test summary",
        )

        assert result.success is True
        assert result.total_issues_found == 5
        assert result.total_issues_fixed == 2
        assert "test.py" in result.files_modified
        assert "ruff" in result.issues_by_tool

    def test_quality_inputs_model(self):
        """Test QualityInputs model creation."""
        from autopr.actions.quality_engine.models import QualityInputs

        inputs = QualityInputs(
            mode=QualityMode.FAST,
            files=self.test_files,
            max_fixes=10,
            enable_ai_agents=True,
            verbose=True,
        )

        assert inputs.mode == QualityMode.FAST
        assert inputs.files == self.test_files
        assert inputs.max_fixes == 10
        assert inputs.enable_ai_agents is True
        assert inputs.verbose is True

    @pytest.mark.asyncio()
    async def test_engine_import(self):
        """Test that Quality Engine can be imported."""
        try:
            from autopr.actions.quality_engine.engine import QualityEngine

            engine = QualityEngine()
            assert engine is not None
        except ImportError as e:
            pytest.fail(f"Failed to import QualityEngine: {e}")

    @pytest.mark.asyncio()
    async def test_tool_result_model(self):
        """Test ToolResult model creation."""
        from autopr.actions.quality_engine.models import ToolResult

        tool_result = ToolResult(
            issues=[{"issue": "test"}],
            files_with_issues=["test.py"],
            summary="Test summary",
            execution_time=1.5,
        )

        assert len(tool_result.issues) == 1
        assert "test.py" in tool_result.files_with_issues
        assert tool_result.summary == "Test summary"
        assert tool_result.execution_time == 1.5


class TestQualityEngineIntegration:
    """Integration tests for Quality Engine."""

    @pytest.mark.asyncio()
    async def test_engine_initialization(self):
        """Test Quality Engine initialization."""
        try:
            from autopr.actions.quality_engine.engine import QualityEngine

            engine = QualityEngine()

            # Test basic attributes
            assert hasattr(engine, "execute")
            assert hasattr(engine, "_run_tools")

        except Exception as e:
            pytest.fail(f"Failed to initialize QualityEngine: {e}")

    @pytest.mark.asyncio()
    async def test_platform_detector(self):
        """Test platform detector functionality."""
        try:
            from autopr.actions.quality_engine.platform_detector import PlatformDetector

            detector = PlatformDetector()

            # Test basic functionality
            assert hasattr(detector, "is_windows")
            assert hasattr(detector, "is_linux")
            assert hasattr(detector, "is_macos")

        except Exception as e:
            pytest.fail(f"Failed to test PlatformDetector: {e}")

    @pytest.mark.asyncio()
    async def test_tool_registry(self):
        """Test tool registry functionality."""
        try:
            from autopr.actions.quality_engine.tools.registry import ToolRegistry

            registry = ToolRegistry()

            # Test basic functionality
            assert hasattr(registry, "get_tools")
            assert hasattr(registry, "register_tool")

        except Exception as e:
            pytest.fail(f"Failed to test ToolRegistry: {e}")


if __name__ == "__main__":
    pytest.main([__file__])
