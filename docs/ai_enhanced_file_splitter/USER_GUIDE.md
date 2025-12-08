# AI Enhanced File Splitter - User Guide

## Overview

The AI Enhanced File Splitter is a sophisticated tool that intelligently splits large files for AI processing while maintaining code context and structure.

## Usage Examples

### Basic Usage

```python
from codeflow_engine.actions.ai_linting_fixer.file_splitter import FileSplitter, SplitConfig
from codeflow_engine.ai.core.providers.manager import LLMProviderManager

# Initialize the file splitter
splitter = FileSplitter(
    llm_manager=LLMProviderManager(config),
    split_config=SplitConfig()
)

# Split a file
chunks = await splitter.split_file("large_file.py")
```

### Advanced Usage

```python
from codeflow_engine.actions.ai_linting_fixer.file_splitter import FileSplitter, SplitConfig
from codeflow_engine.ai.core.providers.manager import LLMProviderManager

# Configure splitting parameters
config = SplitConfig(
    max_chunk_size=1000,
    overlap_lines=10,
    preserve_context=True
)

# Initialize with custom configuration
splitter = FileSplitter(
    llm_manager=LLMProviderManager(config),
    split_config=config
)

# Process multiple files
results = await splitter.process_files(["file1.py", "file2.py"])
```

## Configuration

The `SplitConfig` class allows you to customize the splitting behavior:

- `max_chunk_size`: Maximum lines per chunk
- `overlap_lines`: Number of overlapping lines between chunks
- `preserve_context`: Whether to preserve import and context information

## Performance Optimization

The file splitter includes several performance optimizations:

1. **Intelligent Caching**: Caches analysis results to avoid re-processing
2. **Parallel Processing**: Processes multiple files concurrently
3. **Memory Optimization**: Efficient memory usage for large files
4. **Performance Monitoring**: Tracks and reports performance metrics

## Error Handling

The splitter provides comprehensive error handling:

```python
try:
    chunks = await splitter.split_file("file.py")
except FileNotFoundError:
    print("File not found")
except ProcessingError as e:
    print(f"Processing failed: {e}")
```

## Integration

The file splitter integrates seamlessly with the AutoPR quality engine:

```python
from codeflow_engine.actions.quality_engine.engine import QualityEngine
from codeflow_engine.actions.ai_linting_fixer.file_splitter import FileSplitter

# Use in quality analysis
quality_engine = QualityEngine()
splitter = FileSplitter(llm_manager, config)

# Analyze split files
results = await quality_engine.analyze_files(chunks)
```
