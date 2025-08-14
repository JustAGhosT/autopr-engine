"""Detailed test to diagnose import issues in pytest."""

import importlib
import os
import sys


def print_header(title):
    """Print a section header for better output readability."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)


def test_environment():
    """Test the Python environment and paths."""
    print_header("PYTHON ENVIRONMENT")

    # Print Python version and paths
    print(f"Python {sys.version}")
    print(f"Working directory: {os.getcwd()}")

    # Print Python path
    print("\nPython path (sys.path):")
    for i, path in enumerate(sys.path, 1):
        print(f"{i:2d}. {path}")

    # Check if autopr is importable
    print("\nChecking if autopr is importable:")
    try:
        import autopr

        print(f"✅ autopr imported successfully from: {autopr.__file__}")
    except ImportError as e:
        print(f"❌ Failed to import autopr: {e}")
        raise


def test_import_crew():
    """Test importing the crew module with detailed diagnostics."""
    print_header("TESTING CREW IMPORT")

    # Try to import the module directly
    module_path = "autopr.agents.crew"
    print(f"Attempting to import: {module_path}")

    try:
        # Try to find the module spec
        if module_path in sys.modules:
            print(f"Module {module_path} already in sys.modules")
            module = sys.modules[module_path]
            print(f"  Module file: {getattr(module, '__file__', 'unknown')}")
        else:
            # Try to find the module spec
            spec = importlib.util.find_spec(module_path)
            if spec is None:
                print(f"❌ Module {module_path} not found")
                # Try to find where it might be
                print("\nSearching for module in sys.path:")
                for path in sys.path:
                    full_path = os.path.join(path, module_path.replace(".", os.sep) + ".py")
                    exists = os.path.exists(full_path)
                    print(f"  {full_path} - {'✅' if exists else '❌'}")
                raise ImportError(f"Module {module_path} not found in sys.path")

            print(f"✅ Found module spec: {spec.origin}")

            # Try to import the module
            module = importlib.import_module(module_path)
            print(f"✅ Successfully imported {module_path} from {module.__file__}")

            # Check for AutoPRCrew class
            if hasattr(module, "AutoPRCrew"):
                print("✅ Found AutoPRCrew class")
                return module.AutoPRCrew
            print(f"❌ AutoPRCrew class not found in {module_path}")
            print(f"Available attributes: {[a for a in dir(module) if not a.startswith('_')]}")
            raise AttributeError(f"AutoPRCrew not found in {module_path}")

    except Exception as e:
        print(f"❌ Error importing {module_path}: {e}")
        import traceback

        traceback.print_exc()
        raise


def test_volume_mapping_import():
    """Test importing the volume mapping module with detailed diagnostics."""
    print_header("TESTING VOLUME MAPPING IMPORT")

    module_path = "autopr.actions.quality_engine.volume_mapping"
    print(f"Attempting to import: {module_path}")

    try:
        module = importlib.import_module(module_path)
        print(f"✅ Successfully imported {module_path} from {module.__file__}")

        # Check for get_volume_level_name function
        if hasattr(module, "get_volume_level_name"):
            print("✅ Found get_volume_level_name function")
            result = module.get_volume_level_name(500)
            print(f"✅ get_volume_level_name(500) = {result}")
            assert isinstance(result, str)
            return
        print(f"❌ get_volume_level_name function not found in {module_path}")
        print(f"Available attributes: {[a for a in dir(module) if not a.startswith('_')]}")
        raise AttributeError(f"get_volume_level_name not found in {module_path}")

    except Exception as e:
        print(f"❌ Error importing {module_path}: {e}")
        import traceback

        traceback.print_exc()
        raise
