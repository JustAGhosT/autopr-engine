"""Detailed test to diagnose import issues in pytest."""

import importlib
import os
import sys


def print_header(title):
    """Print a section header for better output readability."""


def test_environment():
    """Test the Python environment and paths."""
    print_header("PYTHON ENVIRONMENT")

    # Print Python version and paths

    # Print Python path
    for _i, _path in enumerate(sys.path, 1):
        pass

    # Check if autopr is importable
    try:
        import autopr

    except ImportError:
        raise


def test_import_crew():
    """Test importing the crew module with detailed diagnostics."""
    print_header("TESTING CREW IMPORT")

    # Try to import the module directly
    module_path = "autopr.agents.crew"

    try:
        # Try to find the module spec
        if module_path in sys.modules:
            module = sys.modules[module_path]
        else:
            # Try to find the module spec
            spec = importlib.util.find_spec(module_path)
            if spec is None:
                # Try to find where it might be
                for path in sys.path:
                    full_path = os.path.join(path, module_path.replace(".", os.sep) + ".py")
                    os.path.exists(full_path)
                msg = f"Module {module_path} not found in sys.path"
                raise ImportError(msg)


            # Try to import the module
            module = importlib.import_module(module_path)

            # Check for AutoPRCrew class
            if hasattr(module, "AutoPRCrew"):
                return module.AutoPRCrew
            msg = f"AutoPRCrew not found in {module_path}"
            raise AttributeError(msg)

    except Exception:
        import traceback

        traceback.print_exc()
        raise


def test_volume_mapping_import():
    """Test importing the volume utils module with detailed diagnostics."""
    print_header("TESTING VOLUME UTILS IMPORT")

    module_path = "autopr.utils.volume_utils"

    try:
        module = importlib.import_module(module_path)

        # Check for get_volume_level_name function
        if hasattr(module, "get_volume_level_name"):
            result = module.get_volume_level_name(500)
            assert isinstance(result, str)
            return
        msg = f"get_volume_level_name not found in {module_path}"
        raise AttributeError(msg)

    except Exception:
        import traceback

        traceback.print_exc()
        raise
