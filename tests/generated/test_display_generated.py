"""
Generated tests for autopr/actions/ai_linting_fixer/display.py
"""

import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add the parent directory to sys.path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from autopr.actions.ai_linting_fixer.display import (DisplayConfig,
                                                         DisplayFormatter,
                                                         DisplayTheme,
                                                         OutputMode,
                                                         SystemStatusDisplay)
except ImportError:
    # If direct import fails, try alternative approaches
    pass


class TestDisplayConfig:
    """Test DisplayConfig class."""

    def test_display_config_initialization(self):
        """Test DisplayConfig initialization with default values."""
        config = DisplayConfig()
        assert config.mode == OutputMode.NORMAL
        assert config.theme == DisplayTheme.DEFAULT
        assert config.use_colors is True
        assert config.use_emojis is True
        assert config.output_stream == sys.stdout
        assert config.error_stream == sys.stderr
        assert config.line_width == 80

    def test_display_config_custom_initialization(self):
        """Test DisplayConfig initialization with custom values."""
        config = DisplayConfig(
            mode=OutputMode.QUIET,
            theme=DisplayTheme.MINIMAL,
            use_colors=False,
            use_emojis=False,
            line_width=120
        )
        assert config.mode == OutputMode.QUIET
        assert config.theme == DisplayTheme.MINIMAL
        assert config.use_colors is False
        assert config.use_emojis is False
        assert config.line_width == 120

    def test_is_quiet(self):
        """Test is_quiet method."""
        config = DisplayConfig(mode=OutputMode.QUIET)
        assert config.is_quiet() is True
        
        config = DisplayConfig(mode=OutputMode.NORMAL)
        assert config.is_quiet() is False

    def test_is_verbose(self):
        """Test is_verbose method."""
        config = DisplayConfig(mode=OutputMode.VERBOSE)
        assert config.is_verbose() is True
        
        config = DisplayConfig(mode=OutputMode.DEBUG)
        assert config.is_verbose() is True
        
        config = DisplayConfig(mode=OutputMode.NORMAL)
        assert config.is_verbose() is False


class TestDisplayFormatter:
    """Test DisplayFormatter class."""

    @pytest.fixture
    def formatter(self):
        """Create a DisplayFormatter instance for testing."""
        config = DisplayConfig()
        return DisplayFormatter(config)

    def test_emoji_default_theme(self, formatter):
        """Test emoji method with default theme."""
        # Test with emojis enabled
        assert "✅" in formatter.emoji("success")
        assert "❌" in formatter.emoji("error")
        assert "⚠️" in formatter.emoji("warning")
        
        # Test with unknown emoji
        assert formatter.emoji("unknown") == ""

    def test_emoji_disabled(self):
        """Test emoji method when emojis are disabled."""
        config = DisplayConfig(use_emojis=False)
        formatter = DisplayFormatter(config)
        assert formatter.emoji("success") == ""

    def test_emoji_minimal_theme(self):
        """Test emoji method with minimal theme."""
        config = DisplayConfig(theme=DisplayTheme.MINIMAL)
        formatter = DisplayFormatter(config)
        assert formatter.emoji("success") == ""

    def test_header_level_1(self, formatter):
        """Test header formatting with level 1."""
        result = formatter.header("Test Header", 1)
        assert "Test Header" in result
        assert "=" * len("Test Header") in result

    def test_header_level_2(self, formatter):
        """Test header formatting with level 2."""
        result = formatter.header("Test Header", 2)
        assert "Test Header" in result
        assert "-" * len("Test Header") in result

    def test_header_default_level(self, formatter):
        """Test header formatting with default level."""
        result = formatter.header("Test Header")
        assert "Test Header:" in result

    def test_section(self, formatter):
        """Test section formatting."""
        result = formatter.section("Test Section", "info")
        assert "Test Section" in result
        assert formatter.emoji("info") in result

    def test_item(self, formatter):
        """Test item formatting."""
        result = formatter.item("Test Item")
        assert "Test Item" in result
        assert "• " in result

    def test_item_with_indent(self, formatter):
        """Test item formatting with custom indent."""
        result = formatter.item("Test Item", indent=2)
        assert "Test Item" in result
        assert "      • " in result  # 6 spaces + bullet

    def test_metric(self, formatter):
        """Test metric formatting."""
        result = formatter.metric("Test Metric", "100", "info")
        assert "Test Metric" in result
        assert "100" in result
        assert formatter.emoji("info") in result

    def test_separator_default(self, formatter):
        """Test separator with default parameters."""
        result = formatter.separator()
        assert len(result) == formatter.config.line_width
        assert all(char == "=" for char in result)

    def test_separator_custom(self, formatter):
        """Test separator with custom parameters."""
        result = formatter.separator(char="-", length=10)
        assert len(result) == 10
        assert all(char == "-" for char in result)

    def test_progress_bar_zero_total(self, formatter):
        """Test progress bar with zero total."""
        result = formatter.progress_bar(0, 0, width=10)
        assert "0.0%" in result
        assert "(0/0)" in result

    def test_progress_bar_half_complete(self, formatter):
        """Test progress bar with half completion."""
        result = formatter.progress_bar(5, 10, width=10)
        assert "50.0%" in result
        assert "(5/10)" in result

    def test_progress_bar_complete(self, formatter):
        """Test progress bar with full completion."""
        result = formatter.progress_bar(10, 10, width=10)
        assert "100.0%" in result
        assert "(10/10)" in result

    def test_progress_bar_over_complete(self, formatter):
        """Test progress bar with over completion."""
        result = formatter.progress_bar(15, 10, width=10)
        assert "100.0%" in result  # Should cap at 100%
        assert "(15/10)" in result


class TestSystemStatusDisplay:
    """Test SystemStatusDisplay class."""

    @pytest.fixture
    def status_display(self):
        """Create a SystemStatusDisplay instance for testing."""
        config = DisplayConfig(output_stream=StringIO())
        formatter = DisplayFormatter(config)
        return SystemStatusDisplay(formatter)

    def test_show_system_status_quiet_mode(self):
        """Test show_system_status in quiet mode."""
        config = DisplayConfig(mode=OutputMode.QUIET, output_stream=StringIO())
        formatter = DisplayFormatter(config)
        status_display = SystemStatusDisplay(formatter)
        
        # Should not output anything in quiet mode
        status_display.show_system_status({"version": "1.0.0"})
        assert config.output_stream.getvalue() == ""

    def test_show_system_status_normal_mode(self):
        """Test show_system_status in normal mode."""
        output_stream = StringIO()
        config = DisplayConfig(output_stream=output_stream)
        formatter = DisplayFormatter(config)
        status_display = SystemStatusDisplay(formatter)
        
        status = {
            "version": "1.0.0",
            "components": {
                "ai_provider": True,
                "backup_system": False
            }
        }
        
        status_display.show_system_status(status)
        output = output_stream.getvalue()
        
        assert "AI Linting Fixer - System Status" in output
        assert "Version: 1.0.0" in output
        assert "Components Status" in output

    def test_show_system_status_verbose_mode(self):
        """Test show_system_status in verbose mode."""
        output_stream = StringIO()
        config = DisplayConfig(mode=OutputMode.VERBOSE, output_stream=output_stream)
        formatter = DisplayFormatter(config)
        status_display = SystemStatusDisplay(formatter)
        
        status = {
            "version": "1.0.0",
            "components": {"ai_provider": True},
            "agent_stats": {
                "test_agent": {
                    "success_rate": 0.8,
                    "attempts": 10,
                    "successes": 8
                }
            }
        }
        
        status_display.show_system_status(status)
        output = output_stream.getvalue()
        
        assert "Agent Performance" in output
        assert "test_agent" in output
        assert "8/10 (80.0%)" in output


class TestOutputMode:
    """Test OutputMode enum."""

    def test_output_mode_values(self):
        """Test OutputMode enum values."""
        assert OutputMode.QUIET.value == "quiet"
        assert OutputMode.NORMAL.value == "normal"
        assert OutputMode.VERBOSE.value == "verbose"
        assert OutputMode.DEBUG.value == "debug"


class TestDisplayTheme:
    """Test DisplayTheme enum."""

    def test_display_theme_values(self):
        """Test DisplayTheme enum values."""
        assert DisplayTheme.DEFAULT.value == "default"
        assert DisplayTheme.MINIMAL.value == "minimal"
        assert DisplayTheme.ENTERPRISE.value == "enterprise"
        assert DisplayTheme.DEV.value == "dev"
