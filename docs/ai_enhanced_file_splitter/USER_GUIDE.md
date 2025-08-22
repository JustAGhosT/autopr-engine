# AI Enhanced File Splitter - User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Operations](#basic-operations)
3. [Advanced Usage](#advanced-usage)
4. [Integration Examples](#integration-examples)
5. [Troubleshooting](#troubleshooting)
6. [Best Practices](#best-practices)
7. [Performance Tips](#performance-tips)
8. [Common Use Cases](#common-use-cases)

## Getting Started

### Prerequisites

Before using the AI Enhanced File Splitter, ensure you have:

1. **Python 3.8+** installed
2. **AutoPR system** properly configured
3. **LLM provider** configured (for AI analysis features)
4. **Sufficient disk space** for backups and split files

### Installation

The file splitter is included with the AutoPR system. No additional installation is required.

### Basic Setup

```python
# Import the required components
from autopr.actions.ai_linting_fixer.file_splitter import FileSplitter, SplitConfig
from pathlib import Path

# Create a basic configuration
config = SplitConfig(
    max_lines_per_file=500,
    max_functions_per_file=10,
    max_classes_per_file=5,
    create_backup=True,
    validate_syntax=True
)

# Initialize the file splitter
splitter = FileSplitter(config)
```

## Basic Operations

### Step 1: Prepare Your File

```python
# Read the file you want to split
file_path = "large_module.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

print(f"Original file: {file_path}")
print(f"Lines: {len(content.splitlines())}")
print(f"Size: {len(content)} bytes")
```

### Step 2: Split the File

```python
# Perform the split
result = splitter.split_file(file_path, content)

# Check the results
if result.success:
    print(f"✅ Split successful!")
    print(f"   Components created: {len(result.components)}")
    print(f"   Strategy used: {result.split_strategy}")
    print(f"   Processing time: {result.processing_time:.3f}s")
    print(f"   Backup created: {result.backup_created}")
    print(f"   Validation passed: {result.validation_passed}")
else:
    print(f"❌ Split failed: {result.error_message}")
```

### Step 3: Review Split Components

```python
# Examine the created components
for i, component in enumerate(result.components, 1):
    print(f"\nComponent {i}: {component.name}")
    print(f"   Type: {component.component_type}")
    print(f"   Lines: {component.end_line - component.start_line + 1}")
    print(f"   Complexity: {component.complexity_score}")
    print(f"   File: {component.file_path}")
```

### Complete Basic Example

```python
#!/usr/bin/env python3
"""
Basic file splitting example
"""

from autopr.actions.ai_linting_fixer.file_splitter import FileSplitter, SplitConfig
from pathlib import Path

def split_large_file(file_path: str):
    """Split a large file into smaller components."""
    
    # Configuration
    config = SplitConfig(
        max_lines_per_file=200,
        max_functions_per_file=5,
        max_classes_per_file=2,
        create_backup=True,
        validate_syntax=True
    )
    
    # Initialize splitter
    splitter = FileSplitter(config)
    
    # Read file
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Perform split
    result = splitter.split_file(file_path, content)
    
    # Display results
    if result.success:
        print(f"✅ Successfully split {file_path}")
        print(f"   Created {len(result.components)} components")
        print(f"   Used strategy: {result.split_strategy}")
        print(f"   Processing time: {result.processing_time:.3f}s")
        
        # List components
        for i, component in enumerate(result.components, 1):
            print(f"   Component {i}: {component.name} ({component.component_type})")
    else:
        print(f"❌ Failed to split {file_path}: {result.error_message}")
    
    return result

# Usage
if __name__ == "__main__":
    result = split_large_file("large_module.py")
```

## Advanced Usage

### AI-Enhanced Splitting

```python
# Enable AI analysis for optimal splitting decisions
ai_config = SplitConfig(
    max_lines_per_file=300,
    max_functions_per_file=8,
    max_classes_per_file=3,
    use_ai_analysis=True,        # Enable AI analysis
    confidence_threshold=0.7,    # Minimum confidence for AI decisions
    enable_learning=True,        # Enable learning from patterns
    create_backup=True,
    validate_syntax=True
)

ai_splitter = FileSplitter(ai_config)
result = ai_splitter.split_file(file_path, content)
```

### Volume-Based Configuration

```python
def create_adaptive_config(volume: int) -> SplitConfig:
    """Create configuration that adapts to volume level."""
    
    # Base configuration
    config = SplitConfig()
    
    # Adjust limits based on volume
    config.max_lines_per_file = 1000 - (volume // 10)
    config.max_functions_per_file = 20 - (volume // 50)
    config.max_classes_per_file = 10 - (volume // 100)
    
    # AI settings based on volume
    config.use_ai_analysis = volume >= 600
    config.confidence_threshold = 0.5 + (volume / 2000)
    config.enable_learning = volume >= 500
    
    # Safety settings
    config.create_backup = volume >= 400
    config.validate_syntax = volume >= 200
    
    return config

# Use with different volume levels
volume_configs = {
    100: create_adaptive_config(100),  # Fast mode
    500: create_adaptive_config(500),  # Smart mode
    800: create_adaptive_config(800),  # AI-enhanced mode
}

for volume, config in volume_configs.items():
    print(f"Volume {volume}: max_lines={config.max_lines_per_file}, "
          f"ai_analysis={config.use_ai_analysis}")
```

### Batch Processing

```python
def process_multiple_files(file_paths: list[str], config: SplitConfig):
    """Process multiple files with the same configuration."""
    
    splitter = FileSplitter(config)
    results = []
    
    for file_path in file_paths:
        print(f"Processing {file_path}...")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            result = splitter.split_file(file_path, content)
            results.append((file_path, result))
            
            if result.success:
                print(f"  ✅ Success: {len(result.components)} components")
            else:
                print(f"  ❌ Failed: {result.error_message}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append((file_path, None))
    
    return results

# Usage
files_to_split = ["module1.py", "module2.py", "module3.py"]
config = SplitConfig(max_lines_per_file=300, max_functions_per_file=8)
results = process_multiple_files(files_to_split, config)
```

## Integration Examples

### Integration with AI Fixer

```python
from autopr.actions.ai_linting_fixer.ai_fix_applier import AIFixApplier
from autopr.actions.llm.manager import LLMProviderManager
from autopr.actions.ai_linting_fixer.models import LintingIssue

def process_with_ai_fixer(file_path: str, content: str, issues: list[LintingIssue]):
    """Process file with AI fixer and automatic splitting."""
    
    # Configure LLM manager
    llm_config = {
        "providers": {"openai": {"api_key_env": "OPENAI_API_KEY"}},
        "fallback_order": ["openai"],
        "default_provider": "openai"
    }
    llm_manager = LLMProviderManager(llm_config)
    
    # Create split configuration
    split_config = SplitConfig(
        max_lines_per_file=400,
        max_functions_per_file=10,
        max_classes_per_file=5,
        use_ai_analysis=True,
        confidence_threshold=0.7,
        create_backup=True,
        validate_syntax=True
    )
    
    # Create AI fix applier with file splitter
    ai_fix_applier = AIFixApplier(
        llm_manager=llm_manager,
        split_config=split_config
    )
    
    # Process with comprehensive workflow
    result = ai_fix_applier.apply_specialist_fix_with_comprehensive_workflow(
        agent=None,  # Will be provided by the system
        file_path=file_path,
        content=content,
        issues=issues,
        session_id="session_123"
    )
    
    return result

# Usage example
issues = [
    LintingIssue(
        file_path="large_file.py",
        line_number=10,
        column_number=5,
        error_code="E501",
        message="Line too long"
    )
]

result = process_with_ai_fixer("large_file.py", content, issues)
print(f"Workflow success: {result.get('success', False)}")
```

### Custom Integration

```python
class CustomFileProcessor:
    """Custom file processor with integrated splitting."""
    
    def __init__(self, split_config: SplitConfig):
        self.splitter = FileSplitter(split_config)
        self.stats = {"processed": 0, "successful": 0, "failed": 0}
    
    def process_file(self, file_path: str, content: str):
        """Process a single file with splitting."""
        
        self.stats["processed"] += 1
        
        try:
            # Perform split
            result = self.splitter.split_file(file_path, content)
            
            if result.success:
                self.stats["successful"] += 1
                self._handle_successful_split(result)
            else:
                self.stats["failed"] += 1
                self._handle_failed_split(result)
            
            return result
            
        except Exception as e:
            self.stats["failed"] += 1
            print(f"Error processing {file_path}: {e}")
            return None
    
    def _handle_successful_split(self, result):
        """Handle successful split results."""
        print(f"✅ Split successful: {len(result.components)} components")
        
        # Process each component
        for component in result.components:
            print(f"  - {component.name}: {component.component_type}")
    
    def _handle_failed_split(self, result):
        """Handle failed split results."""
        print(f"❌ Split failed: {result.error_message}")
    
    def get_statistics(self):
        """Get processing statistics."""
        return {
            **self.stats,
            "success_rate": self.stats["successful"] / max(self.stats["processed"], 1),
            "splitter_stats": self.splitter.get_split_statistics()
        }

# Usage
processor = CustomFileProcessor(SplitConfig(max_lines_per_file=300))
result = processor.process_file("large_file.py", content)
stats = processor.get_statistics()
print(f"Success rate: {stats['success_rate']:.2%}")
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Split Fails with Syntax Error

**Problem**: File splitting fails due to syntax errors in the original file.

**Solution**:
```python
# Check if the original file has syntax issues
import ast

def validate_file_syntax(file_path: str) -> bool:
    try:
        with open(file_path, "r") as f:
            content = f.read()
        ast.parse(content)
        return True
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return False

# Fix syntax issues before splitting
if not validate_file_syntax("large_file.py"):
    print("Fix syntax errors before splitting")
    # ... fix syntax issues ...
```

#### 2. AI Analysis Not Working

**Problem**: AI analysis features are not functioning properly.

**Solution**:
```python
# Check LLM configuration
def check_llm_config():
    import os
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return False
    
    # Test LLM connection
    try:
        llm_config = {
            "providers": {"openai": {"api_key_env": "OPENAI_API_KEY"}},
            "fallback_order": ["openai"],
            "default_provider": "openai"
        }
        llm_manager = LLMProviderManager(llm_config)
        print("✅ LLM configuration valid")
        return True
    except Exception as e:
        print(f"❌ LLM configuration error: {e}")
        return False

# Use fallback configuration if AI fails
if not check_llm_config():
    config = SplitConfig(
        use_ai_analysis=False,  # Disable AI analysis
        create_backup=True,
        validate_syntax=True
    )
```

#### 3. Performance Issues

**Problem**: File splitting is too slow or uses too much memory.

**Solution**:
```python
# Performance-optimized configuration
performance_config = SplitConfig(
    max_lines_per_file=1000,     # Larger files = fewer splits
    max_functions_per_file=20,   # More functions per file
    max_classes_per_file=10,     # More classes per file
    use_ai_analysis=False,       # Disable AI for speed
    create_backup=False,         # Disable backup for speed
    validate_syntax=True         # Keep validation for safety
)

# Monitor performance
import time
import psutil

def monitor_performance(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        print(f"Time: {end_time - start_time:.3f}s")
        print(f"Memory: {(end_memory - start_memory) / 1024 / 1024:.1f}MB")
        
        return result
    return wrapper

# Usage
@monitor_performance
def split_with_monitoring(file_path, content):
    splitter = FileSplitter(performance_config)
    return splitter.split_file(file_path, content)
```

#### 4. Backup Creation Fails

**Problem**: Backup files cannot be created.

**Solution**:
```python
# Check backup directory permissions
def check_backup_permissions():
    import tempfile
    import os
    
    # Test backup directory
    test_dir = tempfile.mkdtemp()
    test_file = os.path.join(test_dir, "test.txt")
    
    try:
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        os.rmdir(test_dir)
        print("✅ Backup permissions OK")
        return True
    except Exception as e:
        print(f"❌ Backup permission error: {e}")
        return False

# Use alternative backup location if needed
if not check_backup_permissions():
    import tempfile
    backup_dir = tempfile.mkdtemp(prefix="autopr_backup_")
    print(f"Using alternative backup directory: {backup_dir}")
```

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# This will show detailed information about the split process
splitter = FileSplitter(config)
result = splitter.split_file(file_path, content)
```

## Best Practices

### 1. Configuration Guidelines

```python
# Start with conservative settings
def get_recommended_config(file_size: int) -> SplitConfig:
    """Get recommended configuration based on file size."""
    
    if file_size < 1000:  # Small files
        return SplitConfig(
            max_lines_per_file=200,
            max_functions_per_file=5,
            max_classes_per_file=2,
            use_ai_analysis=False,  # Not needed for small files
            create_backup=True,
            validate_syntax=True
        )
    elif file_size < 5000:  # Medium files
        return SplitConfig(
            max_lines_per_file=400,
            max_functions_per_file=10,
            max_classes_per_file=5,
            use_ai_analysis=True,
            confidence_threshold=0.7,
            create_backup=True,
            validate_syntax=True
        )
    else:  # Large files
        return SplitConfig(
            max_lines_per_file=600,
            max_functions_per_file=15,
            max_classes_per_file=8,
            use_ai_analysis=True,
            confidence_threshold=0.8,
            create_backup=True,
            validate_syntax=True
        )
```

### 2. Error Handling

```python
def safe_split_file(file_path: str, content: str, config: SplitConfig):
    """Safely split a file with comprehensive error handling."""
    
    try:
        splitter = FileSplitter(config)
        result = splitter.split_file(file_path, content)
        
        if result.success:
            return {"status": "success", "result": result}
        else:
            return {"status": "failed", "error": result.error_message}
            
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Usage with error handling
result = safe_split_file("large_file.py", content, config)
if result["status"] == "success":
    print(f"Split successful: {len(result['result'].components)} components")
else:
    print(f"Split failed: {result['error']}")
```

### 3. Validation and Testing

```python
def validate_split_result(result, original_content: str):
    """Validate that the split result is correct."""
    
    if not result.success:
        return False, "Split was not successful"
    
    # Check that all components exist
    for component in result.components:
        if not Path(component.file_path).exists():
            return False, f"Component file missing: {component.file_path}"
    
    # Check that total content is preserved
    total_split_content = ""
    for component in result.components:
        with open(component.file_path, "r") as f:
            total_split_content += f.read()
    
    # Simple content validation (you might want more sophisticated checks)
    if len(total_split_content) < len(original_content) * 0.8:
        return False, "Significant content loss detected"
    
    return True, "Split validation passed"

# Usage
is_valid, message = validate_split_result(result, original_content)
print(f"Validation: {message}")
```

## Performance Tips

### 1. Optimize for Speed

```python
# Speed-optimized configuration
speed_config = SplitConfig(
    max_lines_per_file=1000,     # Larger files = fewer splits
    max_functions_per_file=25,   # More functions per file
    max_classes_per_file=15,     # More classes per file
    use_ai_analysis=False,       # Disable AI for speed
    create_backup=False,         # Disable backup for speed
    validate_syntax=False        # Disable validation for speed
)
```

### 2. Optimize for Memory

```python
# Memory-optimized configuration
memory_config = SplitConfig(
    max_lines_per_file=200,      # Smaller files = less memory
    max_functions_per_file=5,    # Fewer functions per file
    max_classes_per_file=2,      # Fewer classes per file
    use_ai_analysis=False,       # Disable AI to save memory
    create_backup=False,         # Disable backup to save space
    validate_syntax=True         # Keep validation for safety
)
```

### 3. Batch Processing

```python
def process_files_in_batches(file_paths: list[str], batch_size: int = 5):
    """Process files in batches to manage memory usage."""
    
    config = SplitConfig(max_lines_per_file=300, max_functions_per_file=8)
    
    for i in range(0, len(file_paths), batch_size):
        batch = file_paths[i:i + batch_size]
        print(f"Processing batch {i//batch_size + 1}: {len(batch)} files")
        
        for file_path in batch:
            try:
                with open(file_path, "r") as f:
                    content = f.read()
                
                splitter = FileSplitter(config)
                result = splitter.split_file(file_path, content)
                
                if result.success:
                    print(f"  ✅ {file_path}: {len(result.components)} components")
                else:
                    print(f"  ❌ {file_path}: {result.error_message}")
                    
            except Exception as e:
                print(f"  ❌ {file_path}: {e}")
        
        # Optional: Add delay between batches
        import time
        time.sleep(1)
```

## Common Use Cases

### 1. Legacy Code Refactoring

```python
def refactor_legacy_file(file_path: str):
    """Refactor a legacy monolithic file into smaller modules."""
    
    config = SplitConfig(
        max_lines_per_file=300,
        max_functions_per_file=8,
        max_classes_per_file=3,
        use_ai_analysis=True,
        confidence_threshold=0.6,  # Lower threshold for complex legacy code
        create_backup=True,
        validate_syntax=True
    )
    
    with open(file_path, "r") as f:
        content = f.read()
    
    splitter = FileSplitter(config)
    result = splitter.split_file(file_path, content)
    
    if result.success:
        print(f"Legacy file refactored into {len(result.components)} modules:")
        for component in result.components:
            print(f"  - {component.name}: {component.component_type}")
    
    return result
```

### 2. Microservices Preparation

```python
def prepare_for_microservices(file_path: str):
    """Split a monolithic file for microservices architecture."""
    
    config = SplitConfig(
        max_lines_per_file=200,
        max_functions_per_file=5,
        max_classes_per_file=2,
        use_ai_analysis=True,
        confidence_threshold=0.8,  # High confidence for microservices
        create_backup=True,
        validate_syntax=True
    )
    
    with open(file_path, "r") as f:
        content = f.read()
    
    splitter = FileSplitter(config)
    result = splitter.split_file(file_path, content)
    
    if result.success:
        print(f"File prepared for microservices: {len(result.components)} services")
        for component in result.components:
            print(f"  - Service: {component.name}")
    
    return result
```

### 3. Code Review Preparation

```python
def prepare_for_code_review(file_path: str):
    """Split large files to make them more reviewable."""
    
    config = SplitConfig(
        max_lines_per_file=150,  # Small files for easy review
        max_functions_per_file=3,
        max_classes_per_file=1,
        use_ai_analysis=True,
        confidence_threshold=0.7,
        create_backup=True,
        validate_syntax=True
    )
    
    with open(file_path, "r") as f:
        content = f.read()
    
    splitter = FileSplitter(config)
    result = splitter.split_file(file_path, content)
    
    if result.success:
        print(f"File prepared for review: {len(result.components)} reviewable chunks")
        for component in result.components:
            print(f"  - Review chunk: {component.name} ({component.end_line - component.start_line + 1} lines)")
    
    return result
```

This comprehensive user guide provides everything needed to effectively use the AI Enhanced File Splitter, from basic operations to advanced integration patterns and troubleshooting.
