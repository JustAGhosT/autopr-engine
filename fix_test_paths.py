#!/usr/bin/env python3
"""
Script to fix malformed Windows paths in test files.
"""

import os
import re
from pathlib import Path


def fix_test_paths():
    """Fix malformed Windows paths in test files."""
    tests_dir = Path("tests")
    
    # Patterns to fix
    patterns = [
        # Fix docstring paths - more comprehensive patterns
        (r'"""\s*Generated tests for C:\\Users\\smitj\\repos\\autopr\\autopr-engine\\(.+)"""', 
         r'"""Generated tests for \1 module."""'),
        (r'"""\s*Basic tests for C:\\Users\\smitj\\repos\\autopr\\autopr-engine\\(.+)"""', 
         r'"""Basic tests for \1 module."""'),
        
        # Fix import statements with malformed paths
        (r'module = __import__\(f"autopr\.C:\\Users\\smitj\\repos\\autopr\\autopr-engine\\(.+)", fromlist=\[\'\*\'\]\)', 
         r'module = __import__(f"autopr.\1", fromlist=[\'*\'])'),
        
        # Fix any remaining Windows paths in docstrings
        (r'"""\s*Generated tests for C:\\\\Users\\\\smitj\\\\repos\\\\autopr\\\\autopr-engine\\(.+)"""', 
         r'"""Generated tests for \1 module."""'),
        (r'"""\s*Basic tests for C:\\\\Users\\\\smitj\\\\repos\\\\autopr\\\\autopr-engine\\(.+)"""', 
         r'"""Basic tests for \1 module."""'),
    ]
    
    fixed_files = []
    
    for test_file in tests_dir.rglob("*.py"):
        if test_file.is_file():
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Apply fixes
                for pattern, replacement in patterns:
                    content = re.sub(pattern, replacement, content)
                
                # If content changed, write it back
                if content != original_content:
                    with open(test_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    fixed_files.append(test_file)
                    print(f"Fixed: {test_file}")
                    
            except Exception as e:
                print(f"Error processing {test_file}: {e}")
    
    print(f"\nFixed {len(fixed_files)} files")
    return fixed_files

if __name__ == "__main__":
    fix_test_paths()
