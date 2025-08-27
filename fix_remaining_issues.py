#!/usr/bin/env python3
"""
Comprehensive script to fix all remaining issues and identify incomplete tests.
"""

import os
import re
from pathlib import Path


def fix_remaining_unicode_issues():
    """Fix all remaining unicode escape issues in test files."""
    tests_dir = Path("tests")
    
    fixed_files = []
    
    for test_file in tests_dir.rglob("*.py"):
        if test_file.is_file():
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Fix all Windows path patterns in docstrings - comprehensive patterns
                patterns = [
                    # Pattern 1: Single backslashes
                    (r'"""\s*Generated tests for C:\\Users\\smitj\\repos\\autopr\\autopr-engine\\(.+)"""',
                     r'"""Generated tests for \1 module."""'),
                    
                    # Pattern 2: Double backslashes
                    (r'"""\s*Generated tests for C:\\\\Users\\\\smitj\\\\repos\\\\autopr\\\\autopr-engine\\(.+)"""',
                     r'"""Generated tests for \1 module."""'),
                    
                    # Pattern 3: Basic tests
                    (r'"""\s*Basic tests for C:\\Users\\smitj\\repos\\autopr\\autopr-engine\\(.+)"""',
                     r'"""Basic tests for \1 module."""'),
                    
                    # Pattern 4: Basic tests with double backslashes
                    (r'"""\s*Basic tests for C:\\\\Users\\\\smitj\\\\repos\\\\autopr\\\\autopr-engine\\(.+)"""',
                     r'"""Basic tests for \1 module."""'),
                ]
                
                for pattern, replacement in patterns:
                    content = re.sub(pattern, replacement, content)
                
                # If content changed, write it back
                if content != original_content:
                    with open(test_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    fixed_files.append(test_file)
                    print(f"Fixed unicode issue: {test_file}")
                    
            except Exception as e:
                print(f"Error processing {test_file}: {e}")
    
    print(f"\nFixed unicode issues in {len(fixed_files)} files")
    return fixed_files

def analyze_incomplete_tests():
    """Analyze and categorize incomplete tests."""
    tests_dir = Path("tests")
    
    incomplete_files = {
        'assert_true': [],
        'todo_implement': [],
        'pass_statements': [],
        'minimal_tests': []
    }
    
    for test_file in tests_dir.rglob("*.py"):
        if test_file.is_file():
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Count different types of incomplete tests
                assert_true_count = len(re.findall(r'assert True', content))
                todo_count = len(re.findall(r'TODO.*Implement.*test', content))
                pass_count = len(re.findall(r'^\s*pass\s*$', content, re.MULTILINE))
                
                # Categorize files
                if assert_true_count > 0:
                    incomplete_files['assert_true'].append((test_file, assert_true_count))
                
                if todo_count > 0:
                    incomplete_files['todo_implement'].append((test_file, todo_count))
                
                if pass_count > 0:
                    incomplete_files['pass_statements'].append((test_file, pass_count))
                
                # Check if it's a minimal test file
                if test_file.name in ['minimal_test.py', 'test_minimal.py'] or 'minimal' in test_file.name.lower():
                    incomplete_files['minimal_tests'].append(test_file)
                    
            except Exception as e:
                print(f"Error analyzing {test_file}: {e}")
    
    return incomplete_files

def main():
    """Main function to fix issues and analyze incomplete tests."""
    print("🔧 Fixing remaining unicode escape issues...")
    fixed_files = fix_remaining_unicode_issues()
    
    print("\n📊 Analyzing incomplete tests...")
    incomplete_tests = analyze_incomplete_tests()
    
    print("\n" + "="*60)
    print("📋 COMPREHENSIVE INCOMPLETE TEST ANALYSIS")
    print("="*60)
    
    # Summary statistics
    total_assert_true = sum(count for _, count in incomplete_tests['assert_true'])
    total_todo = sum(count for _, count in incomplete_tests['todo_implement'])
    total_pass = sum(count for _, count in incomplete_tests['pass_statements'])
    
    print(f"\n📈 SUMMARY STATISTICS:")
    print(f"   • Files with 'assert True': {len(incomplete_tests['assert_true'])} files ({total_assert_true} instances)")
    print(f"   • Files with 'TODO Implement': {len(incomplete_tests['todo_implement'])} files ({total_todo} instances)")
    print(f"   • Files with 'pass' statements: {len(incomplete_tests['pass_statements'])} files ({total_pass} instances)")
    print(f"   • Minimal test files: {len(incomplete_tests['minimal_tests'])} files")
    
    print(f"\n🔍 DETAILED BREAKDOWN:")
    
    # Files with assert True
    if incomplete_tests['assert_true']:
        print(f"\n📝 FILES WITH 'assert True' ({len(incomplete_tests['assert_true'])} files):")
        for file_path, count in sorted(incomplete_tests['assert_true'], key=lambda x: x[1], reverse=True):
            print(f"   • {file_path.name}: {count} instances")
    
    # Files with TODO Implement
    if incomplete_tests['todo_implement']:
        print(f"\n📝 FILES WITH 'TODO Implement' ({len(incomplete_tests['todo_implement'])} files):")
        for file_path, count in sorted(incomplete_tests['todo_implement'], key=lambda x: x[1], reverse=True):
            print(f"   • {file_path.name}: {count} instances")
    
    # Minimal test files
    if incomplete_tests['minimal_tests']:
        print(f"\n📝 MINIMAL TEST FILES ({len(incomplete_tests['minimal_tests'])} files):")
        for file_path in incomplete_tests['minimal_tests']:
            print(f"   • {file_path}")
    
    print(f"\n🎯 RECOMMENDATIONS:")
    print(f"   1. Priority: Fix {len(incomplete_tests['assert_true'])} files with 'assert True'")
    print(f"   2. Priority: Implement {len(incomplete_tests['todo_implement'])} files with 'TODO Implement'")
    print(f"   3. Optional: Review {len(incomplete_tests['minimal_tests'])} minimal test files")
    
    return incomplete_tests

if __name__ == "__main__":
    main()
