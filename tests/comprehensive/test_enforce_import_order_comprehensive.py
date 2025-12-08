#!/usr/bin/env python3
"""
Comprehensive tests for enforce import order module.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Import the modules we're testing
try:
    from codeflow_engine.actions.enforce_import_order import (ImportAnalyzer,
                                                     ImportConfig,
                                                     ImportFormatter,
                                                     ImportOrderEnforcer,
                                                     ImportValidator)
except ImportError as e:
    pytest.skip(f"Could not import required modules: {e}", allow_module_level=True)


class TestImportConfig:
    """Test ImportConfig class."""

    def test_import_config_initialization(self):
        """Test ImportConfig initialization."""
        config = ImportConfig(
            enforce_order=True,
            group_imports=True,
            sort_within_groups=True,
            max_line_length=88,
            ignore_comments=True
        )
        
        assert config.enforce_order is True
        assert config.group_imports is True
        assert config.sort_within_groups is True
        assert config.max_line_length == 88
        assert config.ignore_comments is True

    def test_import_config_defaults(self):
        """Test ImportConfig with default values."""
        config = ImportConfig()
        
        assert config.enforce_order is True
        assert config.group_imports is True
        assert config.sort_within_groups is True
        assert config.max_line_length == 79
        assert config.ignore_comments is True

    def test_import_config_to_dict(self):
        """Test ImportConfig to_dict method."""
        config = ImportConfig(
            enforce_order=False,
            max_line_length=100
        )
        
        result = config.to_dict()
        assert result["enforce_order"] is False
        assert result["max_line_length"] == 100

    def test_import_config_from_dict(self):
        """Test ImportConfig from_dict method."""
        data = {
            "enforce_order": True,
            "group_imports": False,
            "sort_within_groups": True,
            "max_line_length": 120,
            "ignore_comments": False
        }
        
        config = ImportConfig.from_dict(data)
        assert config.enforce_order is True
        assert config.group_imports is False
        assert config.sort_within_groups is True
        assert config.max_line_length == 120
        assert config.ignore_comments is False


class TestImportAnalyzer:
    """Test ImportAnalyzer class."""

    @pytest.fixture
    def import_analyzer(self):
        """Create an ImportAnalyzer instance for testing."""
        return ImportAnalyzer()

    def test_import_analyzer_initialization(self, import_analyzer):
        """Test ImportAnalyzer initialization."""
        assert import_analyzer.import_patterns == []
        assert import_analyzer.analysis_cache == {}

    def test_analyze_imports(self, import_analyzer):
        """Test analyzing imports in code."""
        code = """
import os
import sys
from pathlib import Path
import tempfile
from unittest.mock import Mock, patch
"""
        
        result = import_analyzer.analyze_imports(code)
        
        assert "imports" in result
        assert "groups" in result
        assert "violations" in result
        assert len(result["imports"]) > 0

    def test_analyze_imports_no_imports(self, import_analyzer):
        """Test analyzing code with no imports."""
        code = """
def test_function():
    return True

class TestClass:
    pass
"""
        
        result = import_analyzer.analyze_imports(code)
        
        assert result["imports"] == []
        assert result["groups"] == []
        assert result["violations"] == []

    def test_analyze_imports_with_comments(self, import_analyzer):
        """Test analyzing imports with comments."""
        code = """
# Standard library imports
import os
import sys

# Third-party imports
import pytest
from unittest.mock import Mock

# Local imports
from . import local_module
"""
        
        result = import_analyzer.analyze_imports(code)
        
        assert len(result["imports"]) > 0
        assert "groups" in result

    def test_get_import_groups(self, import_analyzer):
        """Test getting import groups."""
        imports = [
            "import os",
            "import sys",
            "import pytest",
            "from unittest.mock import Mock",
            "from . import local_module"
        ]
        
        groups = import_analyzer.get_import_groups(imports)
        
        assert "standard_library" in groups
        assert "third_party" in groups
        assert "local" in groups


class TestImportFormatter:
    """Test ImportFormatter class."""

    @pytest.fixture
    def import_formatter(self):
        """Create an ImportFormatter instance for testing."""
        config = ImportConfig()
        return ImportFormatter(config)

    def test_import_formatter_initialization(self, import_formatter):
        """Test ImportFormatter initialization."""
        assert import_formatter.config is not None
        assert import_formatter.formatters == {}

    def test_format_imports(self, import_formatter):
        """Test formatting imports."""
        imports = [
            "import sys",
            "import os",
            "import pytest",
            "from unittest.mock import Mock"
        ]
        
        result = import_formatter.format_imports(imports)
        
        assert isinstance(result, str)
        assert "import os" in result
        assert "import sys" in result
        assert "import pytest" in result

    def test_format_imports_with_groups(self, import_formatter):
        """Test formatting imports with grouping."""
        imports = [
            "import os",
            "import sys",
            "import pytest",
            "from unittest.mock import Mock",
            "from . import local_module"
        ]
        
        result = import_formatter.format_imports_with_groups(imports)
        
        assert isinstance(result, str)
        assert "import os" in result
        assert "import sys" in result
        assert "import pytest" in result

    def test_sort_imports(self, import_formatter):
        """Test sorting imports."""
        imports = [
            "import sys",
            "import os",
            "import pytest"
        ]
        
        sorted_imports = import_formatter.sort_imports(imports)
        
        assert len(sorted_imports) == 3
        assert sorted_imports[0] == "import os"
        assert sorted_imports[1] == "import pytest"
        assert sorted_imports[2] == "import sys"

    def test_format_import_line(self, import_formatter):
        """Test formatting a single import line."""
        import_line = "from unittest.mock import Mock, patch, MagicMock"
        
        result = import_formatter.format_import_line(import_line)
        
        assert isinstance(result, str)
        assert "Mock" in result
        assert "patch" in result
        assert "MagicMock" in result


class TestImportValidator:
    """Test ImportValidator class."""

    @pytest.fixture
    def import_validator(self):
        """Create an ImportValidator instance for testing."""
        config = ImportConfig()
        return ImportValidator(config)

    def test_import_validator_initialization(self, import_validator):
        """Test ImportValidator initialization."""
        assert import_validator.config is not None
        assert import_validator.validation_rules == []

    def test_validate_import_order(self, import_validator):
        """Test validating import order."""
        imports = [
            "import os",
            "import sys",
            "import pytest",
            "from unittest.mock import Mock"
        ]
        
        result = import_validator.validate_import_order(imports)
        
        assert result.is_valid is True
        assert "violations" in result

    def test_validate_import_order_violations(self, import_validator):
        """Test validating import order with violations."""
        imports = [
            "import pytest",
            "import os",  # Should come before pytest
            "import sys"
        ]
        
        result = import_validator.validate_import_order(imports)
        
        assert result.is_valid is False
        assert len(result.violations) > 0

    def test_validate_import_grouping(self, import_validator):
        """Test validating import grouping."""
        imports = [
            "import os",
            "import sys",
            "import pytest",
            "from unittest.mock import Mock"
        ]
        
        result = import_validator.validate_import_grouping(imports)
        
        assert result.is_valid is True
        assert "groups" in result

    def test_validate_import_formatting(self, import_validator):
        """Test validating import formatting."""
        imports = [
            "import os",
            "import sys",
            "from unittest.mock import Mock, patch, MagicMock"
        ]
        
        result = import_validator.validate_import_formatting(imports)
        
        assert result.is_valid is True
        assert "formatting_issues" in result


class TestImportOrderEnforcer:
    """Test ImportOrderEnforcer class."""

    @pytest.fixture
    def import_order_enforcer(self):
        """Create an ImportOrderEnforcer instance for testing."""
        config = ImportConfig()
        return ImportOrderEnforcer(config)

    def test_import_order_enforcer_initialization(self, import_order_enforcer):
        """Test ImportOrderEnforcer initialization."""
        assert import_order_enforcer.config is not None
        assert import_order_enforcer.analyzer is not None
        assert import_order_enforcer.formatter is not None
        assert import_order_enforcer.validator is not None

    def test_enforce_import_order(self, import_order_enforcer):
        """Test enforcing import order."""
        code = """
import sys
import os
import pytest
from unittest.mock import Mock

def test_function():
    return True
"""
        
        result = import_order_enforcer.enforce_import_order(code)
        
        assert result.success is True
        assert "formatted_code" in result
        assert "import os" in result.formatted_code
        assert "import sys" in result.formatted_code

    def test_enforce_import_order_file(self, import_order_enforcer):
        """Test enforcing import order on a file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
            f.write("""
import sys
import os
import pytest
from unittest.mock import Mock

def test_function():
    return True
""")
            temp_file = f.name
        
        try:
            result = import_order_enforcer.enforce_import_order_file(temp_file)
            
            assert result.success is True
            assert "formatted_code" in result
            
            # Check that file was updated
            with open(temp_file, 'r') as f:
                content = f.read()
                assert "import os" in content
                assert "import sys" in content
                
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_validate_imports(self, import_order_enforcer):
        """Test validating imports."""
        code = """
import os
import sys
import pytest
from unittest.mock import Mock
"""
        
        result = import_order_enforcer.validate_imports(code)
        
        assert result.is_valid is True
        assert "violations" in result
        assert "suggestions" in result

    def test_get_import_statistics(self, import_order_enforcer):
        """Test getting import statistics."""
        code = """
import os
import sys
import pytest
from unittest.mock import Mock
"""
        
        stats = import_order_enforcer.get_import_statistics(code)
        
        assert "total_imports" in stats
        assert "import_groups" in stats
        assert "violations" in stats
        assert stats["total_imports"] == 4
