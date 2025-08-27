#!/usr/bin/env python3
"""
Comprehensive script to fix all unicode escape issues in test files.
"""

import os
import re
from pathlib import Path


def fix_all_paths():
    """Fix all unicode escape issues in test files."""
    tests_dir = Path("tests")
    
    fixed_files = []
    
    for test_file in tests_dir.rglob("*.py"):
        if test_file.is_file():
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Fix all Windows path patterns in docstrings
                # Pattern 1: Single backslashes
                content = re.sub(
                    r'"""\s*Generated tests for C:\\Users\\smitj\\repos\\autopr\\autopr-engine\\(.+)"""',
                    r'"""Generated tests for \1 module."""',
                    content
                )
                
                content = re.sub(
                    r'"""\s*Basic tests for C:\\Users\\smitj\\repos\\autopr\\autopr-engine\\(.+)"""',
                    r'"""Basic tests for \1 module."""',
                    content
                )
                
                # Pattern 2: Double backslashes
                content = re.sub(
                    r'"""\s*Generated tests for C:\\\\Users\\\\smitj\\\\repos\\\\autopr\\\\autopr-engine\\(.+)"""',
                    r'"""Generated tests for \1 module."""',
                    content
                )
                
                content = re.sub(
                    r'"""\s*Basic tests for C:\\\\Users\\\\smitj\\\\repos\\\\autopr\\\\autopr-engine\\(.+)"""',
                    r'"""Basic tests for \1 module."""',
                    content
                )
                
                # Fix import statements
                content = re.sub(
                    r'module = __import__\(f"autopr\.C:\\Users\\smitj\\repos\\autopr\\autopr-engine\\(.+)", fromlist=\[\'\*\'\]\)',
                    r'module = __import__(f"autopr.\1", fromlist=[\'*\'])',
                    content
                )
                
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
    fix_all_paths()
