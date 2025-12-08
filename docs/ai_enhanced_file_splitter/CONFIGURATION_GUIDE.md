# AI Enhanced File Splitter - Configuration Guide

## Table of Contents

1. [Basic Configuration](#basic-configuration)
2. [Advanced Configuration](#advanced-configuration)
3. [Volume Control Integration](#volume-control-integration)
4. [AI Analysis Settings](#ai-analysis-settings)
5. [Safety and Validation](#safety-and-validation)
6. [Performance Tuning](#performance-tuning)
7. [Environment-Specific Configurations](#environment-specific-configurations)
8. [Configuration Examples](#configuration-examples)

## Basic Configuration

### Core Parameters

The `SplitConfig` class provides the fundamental configuration options:

```python
from codeflow_engine.actions.ai_linting_fixer.file_splitter import SplitConfig

config = SplitConfig(
    max_lines_per_file=500,        # Maximum lines per split file
    max_functions_per_file=10,     # Maximum functions per split file
    max_classes_per_file=5,        # Maximum classes per split file
    create_backup=True,            # Create backup before splitting
    validate_syntax=True           # Validate syntax after splitting
)
```

### Parameter Descriptions

| Parameter                | Type | Default | Range   | Description                              |
| ------------------------ | ---- | ------- | ------- | ---------------------------------------- |
| `max_lines_per_file`     | int  | 500     | 50-2000 | Maximum lines allowed per split file     |
| `max_functions_per_file` | int  | 10      | 1-50    | Maximum functions allowed per split file |
| `max_classes_per_file`   | int  | 5       | 1-20    | Maximum classes allowed per split file   |
| `create_backup`          | bool | True    | -       | Create backup before splitting           |
| `validate_syntax`        | bool | True    | -       | Validate syntax after splitting          |

### Recommended Starting Values

```python
# Conservative settings (safe for production)
conservative_config = SplitConfig(
    max_lines_per_file=200,
    max_functions_per_file=5,
    max_classes_per_file=2,
    create_backup=True,
    validate_syntax=True
)

# Balanced settings (good for most use cases)
balanced_config = SplitConfig(
    max_lines_per_file=500,
    max_functions_per_file=10,
    max_classes_per_file=5,
    create_backup=True,
    validate_syntax=True
)

# Aggressive settings (for large files)
aggressive_config = SplitConfig(
    max_lines_per_file=1000,
    max_functions_per_file=20,
    max_classes_per_file=10,
    create_backup=True,
    validate_syntax=True
)
```

## Advanced Configuration

### AI Analysis Settings

```python
config = SplitConfig(
    # Basic settings
    max_lines_per_file=500,
    max_functions_per_file=10,
    max_classes_per_file=5,
    
    # AI analysis settings
    use_ai_analysis=True,           # Enable AI-powered analysis
    confidence_threshold=0.7,       # Minimum confidence for AI decisions
    enable_learning=True,           # Enable learning memory system
    
    # Safety settings
    create_backup=True,
    validate_syntax=True
)
```

### Advanced Parameters

| Parameter              | Type  | Default | Description                                   |
| ---------------------- | ----- | ------- | --------------------------------------------- |
| `use_ai_analysis`      | bool  | True    | Enable AI-powered splitting decisions         |
| `confidence_threshold` | float | 0.7     | Minimum confidence (0.0-1.0) for AI decisions |
| `enable_learning`      | bool  | True    | Enable learning from historical patterns      |

## Volume Control Integration

The file splitter automatically adapts its behavior based on volume settings. Here's how to configure it:

### Volume-Based Configuration Function

```python
def create_volume_based_config(volume: int) -> SplitConfig:
    """
    Create configuration based on volume level.
    
    Volume ranges:
    - 0-200: Fast mode (basic splitting)
    - 200-500: Smart mode (with validation)
    - 500-800: AI-enhanced mode (with learning)
    - 800-1000: Maximum mode (full AI analysis)
    """
    
    # Base configuration
    config = SplitConfig()
    
    # Adjust limits based on volume with proper clamping
    config.max_lines_per_file = max(10, 1000 - (volume // 10))  # Minimum 10 lines
    config.max_functions_per_file = max(1, 20 - (volume // 50))  # Minimum 1 function
    config.max_classes_per_file = max(1, 10 - (volume // 100))   # Minimum 1 class
    
    # AI analysis settings
    config.use_ai_analysis = volume >= 600
    config.confidence_threshold = min(1.0, max(0.0, 0.5 + (volume / 2000)))  # Clamp to [0, 1]
    config.enable_learning = volume >= 500
    
    # Safety settings
    config.create_backup = volume >= 400
    config.validate_syntax = volume >= 200
    
    return config

### Configuration Validation

The volume-based configuration automatically validates and clamps values to ensure constraints are always satisfied:

- **Minimum Limits**: `max_lines_per_file` ≥ 10, `max_functions_per_file` ≥ 1, `max_classes_per_file` ≥ 1
- **Confidence Threshold**: Clamped to range [0.0, 1.0]
- **Volume Range**: Validated to be within [0, 1000]

This prevents invalid configurations that could cause the file splitter to fail or behave unexpectedly.

### Volume Level Examples

```python
# Volume 0: Ultra-fast mode
config_0 = create_volume_based_config(0)
# Result: max_lines=1000, max_functions=20, max_classes=10
# AI analysis: False, Backup: False, Validation: False

# Volume 300: Moderate mode
config_300 = create_volume_based_config(300)
# Result: max_lines=970, max_functions=14, max_classes=7
# AI analysis: False, Backup: False, Validation: True

# Volume 600: AI-enhanced mode
config_600 = create_volume_based_config(600)
# Result: max_lines=940, max_functions=8, max_classes=4
# AI analysis: True, Backup: True, Validation: True

# Volume 900: Maximum mode
config_900 = create_volume_based_config(900)
# Result: max_lines=910, max_functions=2, max_classes=1
# AI analysis: True, Backup: True, Validation: True

# Volume 1000: Ultra-maximum mode (with clamping)
config_1000 = create_volume_based_config(1000)
# Result: max_lines=900, max_functions=1, max_classes=1 (clamped to minimums)
# AI analysis: True, Backup: True, Validation: True
```

## AI Analysis Settings

### Confidence Threshold Configuration

The confidence threshold determines how certain the AI must be before making a splitting decision:

```python
# Conservative AI settings
conservative_ai = SplitConfig(
    use_ai_analysis=True,
    confidence_threshold=0.9,  # Very high confidence required
    enable_learning=True
)

# Balanced AI settings
balanced_ai = SplitConfig(
    use_ai_analysis=True,
    confidence_threshold=0.7,  # Standard confidence level
    enable_learning=True
)

# Aggressive AI settings
aggressive_ai = SplitConfig(
    use_ai_analysis=True,
    confidence_threshold=0.5,  # Lower confidence, more aggressive
    enable_learning=True
)
```

### Learning Memory Configuration

```python
# Enable learning with custom settings
learning_config = SplitConfig(
    use_ai_analysis=True,
    confidence_threshold=0.7,
    enable_learning=True,  # Enable pattern learning
    create_backup=True,
    validate_syntax=True
)

# Disable learning for consistent behavior
no_learning_config = SplitConfig(
    use_ai_analysis=True,
    confidence_threshold=0.7,
    enable_learning=False,  # Disable pattern learning
    create_backup=True,
    validate_syntax=True
)
```

## Safety and Validation

### Backup Configuration

```python
# Always create backups
safe_config = SplitConfig(
    create_backup=True,
    validate_syntax=True,
    max_lines_per_file=500
)

# Disable backups for performance (not recommended for production)
fast_config = SplitConfig(
    create_backup=False,
    validate_syntax=True,
    max_lines_per_file=500
)
```

### Validation Settings

```python
# Full validation
full_validation_config = SplitConfig(
    validate_syntax=True,
    create_backup=True,
    use_ai_analysis=True,
    confidence_threshold=0.8
)

# Minimal validation
minimal_validation_config = SplitConfig(
    validate_syntax=False,
    create_backup=False,
    use_ai_analysis=False
)
```

## Performance Tuning

### Memory Optimization

```python
# Memory-efficient configuration
memory_optimized_config = SplitConfig(
    max_lines_per_file=200,      # Smaller files = less memory
    max_functions_per_file=5,    # Fewer functions per file
    max_classes_per_file=2,      # Fewer classes per file
    use_ai_analysis=False,       # Disable AI to save memory
    create_backup=False,         # Disable backup to save space
    validate_syntax=True         # Keep validation for safety
)
```

### Speed Optimization

```python
# Speed-optimized configuration
speed_optimized_config = SplitConfig(
    max_lines_per_file=1000,     # Larger files = fewer splits
    max_functions_per_file=20,   # More functions per file
    max_classes_per_file=10,     # More classes per file
    use_ai_analysis=False,       # Disable AI for speed
    create_backup=False,         # Disable backup for speed
    validate_syntax=False        # Disable validation for speed
)
```

### Balanced Performance

```python
# Balanced performance configuration
balanced_performance_config = SplitConfig(
    max_lines_per_file=500,      # Moderate file size
    max_functions_per_file=10,   # Moderate function count
    max_classes_per_file=5,      # Moderate class count
    use_ai_analysis=True,        # Enable AI for quality
    confidence_threshold=0.6,    # Lower threshold for speed
    create_backup=True,          # Enable backup for safety
    validate_syntax=True         # Enable validation for quality
)
```

## Environment-Specific Configurations

### Development Environment

```python
# Development configuration
dev_config = SplitConfig(
    max_lines_per_file=300,
    max_functions_per_file=8,
    max_classes_per_file=3,
    use_ai_analysis=True,
    confidence_threshold=0.6,
    create_backup=True,
    validate_syntax=True,
    enable_learning=True
)
```

### Testing Environment

```python
# Testing configuration
test_config = SplitConfig(
    max_lines_per_file=200,
    max_functions_per_file=5,
    max_classes_per_file=2,
    use_ai_analysis=False,  # Disable AI for consistent results
    create_backup=False,    # No backups needed in testing
    validate_syntax=True,   # Keep validation for correctness
    enable_learning=False   # Disable learning for consistency
)
```

### Production Environment

```python
# Production configuration
prod_config = SplitConfig(
    max_lines_per_file=500,
    max_functions_per_file=10,
    max_classes_per_file=5,
    use_ai_analysis=True,
    confidence_threshold=0.8,  # High confidence for production
    create_backup=True,
    validate_syntax=True,
    enable_learning=True
)
```

### CI/CD Environment

```python
# CI/CD configuration
cicd_config = SplitConfig(
    max_lines_per_file=400,
    max_functions_per_file=8,
    max_classes_per_file=4,
    use_ai_analysis=True,
    confidence_threshold=0.7,
    create_backup=False,    # No backups in CI/CD
    validate_syntax=True,   # Validation is critical
    enable_learning=False   # Disable learning in CI/CD
)
```

## Configuration Examples

### Example 1: Large Codebase Processing

```python
# For processing large codebases with many files
large_codebase_config = SplitConfig(
    max_lines_per_file=800,
    max_functions_per_file=15,
    max_classes_per_file=8,
    use_ai_analysis=True,
    confidence_threshold=0.75,
    create_backup=True,
    validate_syntax=True,
    enable_learning=True
)
```

### Example 2: Microservices Architecture

```python
# For microservices with small, focused files
microservice_config = SplitConfig(
    max_lines_per_file=200,
    max_functions_per_file=5,
    max_classes_per_file=2,
    use_ai_analysis=True,
    confidence_threshold=0.8,
    create_backup=True,
    validate_syntax=True,
    enable_learning=True
)
```

### Example 3: Legacy Code Migration

```python
# For migrating legacy monolithic code
legacy_migration_config = SplitConfig(
    max_lines_per_file=1000,
    max_functions_per_file=25,
    max_classes_per_file=12,
    use_ai_analysis=True,
    confidence_threshold=0.6,  # Lower threshold for complex legacy code
    create_backup=True,
    validate_syntax=True,
    enable_learning=True
)
```

### Example 4: Real-time Processing

```python
# For real-time file processing
realtime_config = SplitConfig(
    max_lines_per_file=300,
    max_functions_per_file=6,
    max_classes_per_file=3,
    use_ai_analysis=False,  # Disable AI for speed
    create_backup=False,    # Disable backup for speed
    validate_syntax=True,   # Keep validation for safety
    enable_learning=False   # Disable learning for consistency
)
```

### Example 5: Research and Experimentation

```python
# For research and experimentation
research_config = SplitConfig(
    max_lines_per_file=600,
    max_functions_per_file=12,
    max_classes_per_file=6,
    use_ai_analysis=True,
    confidence_threshold=0.5,  # Lower threshold for experimentation
    create_backup=True,
    validate_syntax=True,
    enable_learning=True
)
```

## Configuration Validation

### Validation Function

```python
def validate_config(config: SplitConfig) -> List[str]:
    """Validate configuration and return list of warnings/errors."""
    issues = []
    
    # Check parameter ranges
    if config.max_lines_per_file < 50:
        issues.append("max_lines_per_file is very low (< 50)")
    elif config.max_lines_per_file > 2000:
        issues.append("max_lines_per_file is very high (> 2000)")
    
    if config.max_functions_per_file < 1:
        issues.append("max_functions_per_file must be at least 1")
    elif config.max_functions_per_file > 50:
        issues.append("max_functions_per_file is very high (> 50)")
    
    if config.max_classes_per_file < 1:
        issues.append("max_classes_per_file must be at least 1")
    elif config.max_classes_per_file > 20:
        issues.append("max_classes_per_file is very high (> 20)")
    
    if config.confidence_threshold < 0.0 or config.confidence_threshold > 1.0:
        issues.append("confidence_threshold must be between 0.0 and 1.0")
    
    # Check safety settings
    if not config.create_backup and config.use_ai_analysis:
        issues.append("Warning: AI analysis enabled without backup")
    
    if not config.validate_syntax:
        issues.append("Warning: Syntax validation disabled")
    
    return issues

# Usage
config = SplitConfig(max_lines_per_file=100, max_functions_per_file=2)
issues = validate_config(config)
for issue in issues:
    print(f"Configuration issue: {issue}")
```

## Best Practices Summary

1. **Start Conservative**: Begin with lower limits and increase gradually
2. **Enable Safety Features**: Always use backup and validation in production
3. **Monitor Performance**: Track success rates and processing times
4. **Use Volume Controls**: Leverage volume-based configuration for adaptive behavior
5. **Test Thoroughly**: Validate configurations with your specific codebase
6. **Document Changes**: Keep track of configuration changes and their effects
7. **Environment Awareness**: Use appropriate settings for different environments
8. **Regular Review**: Periodically review and optimize configurations based on usage patterns
