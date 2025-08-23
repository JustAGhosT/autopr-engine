# AI Enhanced File Splitter

## Overview

The AI Enhanced File Splitter is a sophisticated component of the AutoPR system that intelligently splits large code files into smaller, more manageable components. It uses AI-powered analysis to make optimal splitting decisions based on code complexity, structure, and historical patterns.

## Key Features

### 🧠 **AI-Powered Intelligence**

- **Learning Memory System**: Remembers successful splitting patterns
- **Complexity Analysis**: AST-based parsing for accurate code structure analysis
- **Confidence Scoring**: AI-driven decision making with confidence thresholds
- **Pattern Recognition**: Learns from historical split success rates

### 🔧 **Multiple Splitting Strategies**

- **Function-Based**: Splits by individual functions and methods
- **Class-Based**: Separates classes into individual files
- **Section-Based**: Splits by logical code sections
- **Module-Based**: Creates separate modules for different concerns

### 🛡️ **Safety & Reliability**

- **Automatic Backups**: Creates backups before any file modifications
- **Syntax Validation**: Ensures split files maintain valid syntax
- **Rollback Capability**: Automatic restoration if validation fails
- **Error Recovery**: Graceful handling of edge cases and failures

### 📊 **Performance & Monitoring**

- **Real-time Metrics**: Tracks split success rates and performance
- **Processing Statistics**: Detailed analytics on split operations
- **Volume Control Integration**: Adapts behavior based on volume settings
- **Resource Management**: Efficient memory and CPU usage

## Quick Start

### Basic Usage

```python
from autopr.actions.ai_linting_fixer.file_splitter import FileSplitter, SplitConfig

# Create configuration
config = SplitConfig(
    max_lines_per_file=100,
    max_functions_per_file=5,
    max_classes_per_file=2,
    create_backup=True,
    validate_syntax=True
)

# Initialize splitter
splitter = FileSplitter(config)

# Split a file
with open("large_file.py", "r") as f:
    content = f.read()

result = splitter.split_file("large_file.py", content)

if result.success:
    print(f"Split into {len(result.components)} components")
    print(f"Strategy used: {result.split_strategy}")
    print(f"Processing time: {result.processing_time:.3f}s")
```

### Integration with AI Fixer

```python
from autopr.actions.ai_linting_fixer.ai_fix_applier import AIFixApplier
from autopr.actions.llm.manager import LLMProviderManager

# Configure LLM manager
llm_config = {
    "providers": {"openai": {"api_key_env": "OPENAI_API_KEY"}},
    "fallback_order": ["openai"],
    "default_provider": "openai"
}
llm_manager = LLMProviderManager(llm_config)

# Create AI fix applier with file splitter
ai_fix_applier = AIFixApplier(
    llm_manager=llm_manager,
    split_config=config
)

# Apply fixes with automatic file splitting
result = ai_fix_applier.apply_specialist_fix_with_comprehensive_workflow(
    agent=agent,
    file_path="large_file.py",
    content=content,
    issues=linting_issues,
    session_id="session_123"
)
```

## Configuration Options

### SplitConfig Parameters

| Parameter                | Type  | Default | Description                         |
| ------------------------ | ----- | ------- | ----------------------------------- |
| `max_lines_per_file`     | int   | 500     | Maximum lines per split file        |
| `max_functions_per_file` | int   | 10      | Maximum functions per split file    |
| `max_classes_per_file`   | int   | 5       | Maximum classes per split file      |
| `use_ai_analysis`        | bool  | True    | Enable AI-powered analysis          |
| `confidence_threshold`   | float | 0.7     | Minimum confidence for AI decisions |
| `create_backup`          | bool  | True    | Create backup before splitting      |
| `validate_syntax`        | bool  | True    | Validate syntax after splitting     |
| `enable_learning`        | bool  | True    | Enable learning memory system       |

### Volume Control Integration

The file splitter automatically adapts its behavior based on volume settings:

- **Volume 0-200**: Fast mode with basic splitting
- **Volume 200-500**: Smart mode with validation
- **Volume 500-800**: AI-enhanced mode with learning
- **Volume 800-1000**: Maximum mode with full AI analysis

## File Structure

```text
autopr/actions/
├── learning_memory_system.py # AI learning and pattern recognition

autopr/actions/ai_linting_fixer/
├── file_splitter.py          # Main file splitter implementation
├── models.py                 # Data models and types
├── ai_fix_applier.py         # Integration with AI fixer
├── backup_manager.py         # Backup and rollback functionality
└── validation_manager.py     # Syntax validation
```

## Examples

### Example 1: Basic File Splitting

```python
# Split a large Python file
config = SplitConfig(max_lines_per_file=50, max_functions_per_file=3)
splitter = FileSplitter(config)

result = splitter.split_file("large_module.py", content)
print(f"Created {len(result.components)} components")
```

### Example 2: AI-Enhanced Splitting

```python
# Use AI analysis for optimal splitting
config = SplitConfig(
    max_lines_per_file=100,
    use_ai_analysis=True,
    confidence_threshold=0.8,
    create_backup=True
)
splitter = FileSplitter(config)

result = splitter.split_file("complex_file.py", content)
if result.success:
    for component in result.components:
        print(f"Component: {component.name} ({component.component_type})")
```

### Example 3: Volume-Based Configuration

```python
# Configure based on volume level
def get_split_config(volume: int) -> SplitConfig:
    return SplitConfig(
        max_lines_per_file=1000 - (volume // 10),
        max_functions_per_file=20 - (volume // 50),
        use_ai_analysis=volume >= 600,
        confidence_threshold=0.5 + (volume / 2000),
        create_backup=volume >= 400,
        validate_syntax=volume >= 200
    )

# Use with different volume levels
config = get_split_config(700)  # AI-enhanced mode
splitter = FileSplitter(config)
```

## Best Practices

### 1. **Configuration Guidelines**

- Start with conservative limits and adjust based on results
- Enable AI analysis for complex codebases
- Always use backup and validation in production
- Monitor success rates and adjust confidence thresholds

### 2. **Performance Optimization**

- Use appropriate volume levels for your use case
- Monitor processing times and adjust limits
- Enable learning for repeated operations
- Use batch processing for multiple files

### 3. **Safety Considerations**

- Always test splitting on non-critical files first
- Review generated components before committing
- Keep backups for critical files
- Monitor validation results

### 4. **Integration Tips**

- Use with AI fixer for comprehensive code processing
- Integrate with volume controls for adaptive behavior
- Monitor metrics for continuous improvement
- Use session IDs for tracking related operations

## Troubleshooting

### Common Issues

1. **Split Fails with Syntax Error**

   - Check if `validate_syntax=True` is enabled
   - Review the original file for syntax issues
   - Try different splitting strategies

2. **AI Analysis Not Working**

   - Verify `use_ai_analysis=True` is set
   - Check LLM provider configuration
   - Ensure confidence threshold is appropriate

3. **Performance Issues**

   - Reduce `max_lines_per_file` limit
   - Disable AI analysis for simple files
   - Use lower volume settings

4. **Backup Creation Fails**

   - Check file permissions
   - Verify backup directory exists
   - Ensure sufficient disk space

### Debug Mode

Enable debug logging for detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed split process information
splitter = FileSplitter(config)
result = splitter.split_file(file_path, content)
```

## API Reference

### FileSplitter Class

```python
class FileSplitter:
    def __init__(self, config: SplitConfig)
    def split_file(self, file_path: str, content: str) -> SplitResult
    def get_split_statistics(self) -> Dict[str, Any]
    def reset_statistics(self) -> None
```

### SplitConfig Class

```python
@dataclass
class SplitConfig:
    max_lines_per_file: int = 500
    max_functions_per_file: int = 10
    max_classes_per_file: int = 5
    use_ai_analysis: bool = True
    confidence_threshold: float = 0.7
    create_backup: bool = True
    validate_syntax: bool = True
    enable_learning: bool = True
```

### SplitResult Class

```python
@dataclass
class SplitResult:
    success: bool
    components: List[SplitComponent]
    split_strategy: str
    processing_time: float
    backup_created: bool
    validation_passed: bool
    error_message: Optional[str] = None
```

## Contributing

To contribute to the AI Enhanced File Splitter:

1. Follow the existing code style and patterns
2. Add comprehensive tests for new features
3. Update documentation for any API changes
4. Ensure all tests pass before submitting
5. Include performance benchmarks for optimizations

## License

This component is part of the AutoPR system and follows the same licensing terms.
