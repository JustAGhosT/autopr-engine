"""Debug script to test imports and environment."""
import sys
import os
import importlib
from pathlib import Path
import inspect

def print_header(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, '='))
    print("=" * 80)

# Print environment information
print_header("ENVIRONMENT INFORMATION")
print(f"Python {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Python executable: {sys.executable}")

# Print Python path
print_header("PYTHON PATH")
for i, path in enumerate(sys.path, 1):
    print(f"{i:2d}. {path}")

# Function to test importing a module
def test_import(module_name):
    """Test importing a module and print information about it."""
    print_header(f"TESTING IMPORT: {module_name}")
    
    try:
        # Check if module is already imported
        if module_name in sys.modules:
            print(f"Module {module_name} is already in sys.modules")
            module = sys.modules[module_name]
            print(f"  File: {getattr(module, '__file__', 'unknown')}")
            print(f"  Package: {getattr(module, '__package__', 'unknown')}")
            return module
            
        # Try to find the module spec
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            print(f"❌ Module {module_name} not found")
            print("Searching for module in sys.path:")
            parts = module_name.split('.')
            for i in range(1, len(parts) + 1):
                partial = '.'.join(parts[:i])
                partial_path = os.path.join(*parts[:i])
                for path in sys.path:
                    if not path:
                        continue
                    # Check for package directory
                    package_dir = os.path.join(path, partial_path)
                    if os.path.isdir(package_dir) and os.path.isfile(os.path.join(package_dir, '__init__.py')):
                        print(f"  ✅ Found package directory: {package_dir}")
                    # Check for module file
                    module_file = os.path.join(path, *parts) + '.py'
                    if os.path.isfile(module_file):
                        print(f"  ✅ Found module file: {module_file}")
            return None
            
        print(f"✅ Found module spec: {spec.origin}")
        print(f"  Package: {spec.parent}")
        print(f"  Loader: {spec.loader}")
        
        # Try to import the module
        module = importlib.import_module(module_name)
        print(f"✅ Successfully imported {module_name}")
        print(f"  File: {getattr(module, '__file__', 'unknown')}")
        print(f"  Package: {getattr(module, '__package__', 'unknown')}")
        
        return module
        
    except Exception as e:
        print(f"❌ Error importing {module_name}: {e}")
        import traceback
        traceback.print_exc()
        return None

# Test importing autopr package
autopr = test_import('autopr')

# Test importing autopr.agents package
agents = test_import('autopr.agents')

# Test importing autopr.agents.crew module
crew = test_import('autopr.agents.crew')

# If crew module was imported successfully, try to access AutoPRCrew
if crew is not None:
    print_header("TESTING AUTOPRCREW CLASS")
    try:
        AutoPRCrew = getattr(crew, 'AutoPRCrew', None)
        if AutoPRCrew is not None:
            print(f"✅ Found AutoPRCrew class: {AutoPRCrew}")
            print(f"  Module: {AutoPRCrew.__module__}")
            print(f"  File: {inspect.getfile(AutoPRCrew) if hasattr(inspect, 'getfile') else 'unknown'}")
        else:
            print("❌ AutoPRCrew class not found in autopr.agents.crew")
            print(f"Available attributes: {[a for a in dir(crew) if not a.startswith('_')]}")
    except Exception as e:
        print(f"❌ Error accessing AutoPRCrew: {e}")
        import traceback
        traceback.print_exc()

# Test importing volume_mapping module
volume_mapping = test_import('autopr.actions.quality_engine.volume_mapping')

# If volume_mapping was imported successfully, test the function
if volume_mapping is not None:
    print_header("TESTING VOLUME MAPPING FUNCTION")
    try:
        get_volume_level_name = getattr(volume_mapping, 'get_volume_level_name', None)
        if callable(get_volume_level_name):
            result = get_volume_level_name(500)
            print(f"✅ get_volume_level_name(500) = {result}")
        else:
            print("❌ get_volume_level_name function not found")
    except Exception as e:
        print(f"❌ Error calling get_volume_level_name: {e}")
        import traceback
        traceback.print_exc()

print_header("TEST COMPLETE")
