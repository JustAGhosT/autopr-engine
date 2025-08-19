# Volume Control in AutoPR Engine

## Overview

Volume control in AutoPR Engine allows you to adjust the depth and strictness of code analysis on a
scale from 0 to 1000. This feature helps balance between thoroughness and performance based on your
needs.

## Volume Levels

| Volume   | Quality Mode  | Analysis Depth | Best For                                 |
| -------- | ------------- | -------------- | ---------------------------------------- |
| 0-299    | Fast          | Quick          | Quick feedback during active development |
| 300-699  | Smart         | Standard       | Regular pull requests and code reviews   |
| 700-899  | Comprehensive | Thorough       | Important merges and releases            |
| 900-1000 | AI-Enhanced   | Exhaustive     | Security audits and critical releases    |

## Key Features

### 1. Dynamic Analysis Depth

- **Low Volume (0-299)**: Surface-level analysis focusing on critical issues
- **Medium Volume (300-699)**: Balanced analysis with reasonable depth
- **High Volume (700-1000)**: In-depth analysis with comprehensive checks

### 2. Quality Mode Adjustment

- Automatically adjusts quality modes based on volume
- Affects tool selection and validation strictness
- Configurable via `QualityInputs`

### 3. Performance Optimization

- Reduces analysis time at lower volumes
- Scales resource usage with volume level
- Smart caching of results

## Usage Examples

### Basic Usage

```python
# Initialize crew with default volume (500)
crew = AutoPRCrew()

# Analyze repository with default volume
report = await crew.analyze_repository("/path/to/repo")

# Analyze with specific volume (0-1000)
detailed_report = await crew.analyze_repository(
    "/path/to/repo",
    volume=800  # More thorough analysis
)
```

### Volume-Aware Task Creation

```python
# Create tasks with volume context
task = crew._create_code_quality_task(
    Path("/repo"),
    {
        "volume": 750,
        "volume_context": crew._get_volume_context(750),
        "quality_inputs": crew._create_quality_inputs(750).dict()
    }
)
```

## Configuration

### Environment Variables

```bash
# Set default volume (0-1000)
AUTOPR_DEFAULT_VOLUME=500

# Set volume-specific timeouts (in seconds)
AUTOPR_VOLUME_LOW_TIMEOUT=60
AUTOPR_VOLUME_MEDIUM_TIMEOUT=120
AUTOPR_VOLUME_HIGH_TIMEOUT=300
```

### Quality Inputs

Volume affects these `QualityInputs` parameters:

- `mode`: QualityMode (FAST, SMART, COMPREHENSIVE, AI_ENHANCED)
- `max_issues`: Maximum number of issues to report
- `timeout_seconds`: Analysis timeout
- `enable_expensive_checks`: Whether to run resource-intensive checks

## Best Practices

1. **Development Workflow**
   - Use lower volumes (200-400) during active development
   - Increase volume (500-700) for pull requests
   - Use highest volumes (800+) for release candidates

2. **Performance Considerations**
   - Higher volumes increase memory and CPU usage
   - Consider server load when running at high volumes
   - Use caching for repeated analyses

3. **Customization**
   - Override default volume mappings in `volume_mapping.py`
   - Create custom quality presets
   - Implement volume-aware plugins

## Troubleshooting

### Common Issues

1. **Analysis Taking Too Long**
   - Reduce volume level
   - Increase timeouts if needed
   - Check for performance bottlenecks

2. **Too Many/Few Issues**
   - Adjust volume level
   - Check quality mode settings
   - Review validation rules

3. **Memory Issues**
   - Lower volume for large repositories
   - Increase system resources if needed
   - Enable memory profiling

## API Reference

### AutoPRCrew

#### analyze_repository

```python
async def analyze_repository(
    self,
    repo_path: Union[str, Path],
    volume: Optional[int] = None,
    **analysis_kwargs
) -> CodeAnalysisReport:
    """Analyze a repository with volume-based quality control.

    Args:
        repo_path: Path to the repository
        volume: Analysis volume (0-1000)
        **analysis_kwargs: Additional analysis parameters

    Returns:
        CodeAnalysisReport: Analysis results
    """
```

#### \_create_quality_inputs

```python
def _create_quality_inputs(self, volume: int) -> QualityInputs:
    """Create QualityInputs based on volume level.

    Args:
        volume: Volume level (0-1000)

    Returns:
        QualityInputs: Configured quality inputs
    """
```

## See Also

- [Quality Engine Documentation](./quality_engine.md)
- [Agent Framework](./agents.md)
- [Performance Tuning](./performance.md)
