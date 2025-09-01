# AI Enhanced File Splitter

## Overview

The AI Enhanced File Splitter is a sophisticated tool that intelligently splits large files for AI processing while maintaining code context and structure.

## Features

- **Intelligent Splitting**: AI-powered analysis for optimal file division
- **Context Preservation**: Maintains imports and dependencies
- **Performance Optimization**: Caching, parallel processing, and memory optimization
- **Quality Assurance**: Syntax validation and error handling
- **Flexible Configuration**: Customizable splitting parameters

## Installation

The file splitter is included with the AutoPR system. No additional installation is required.

## Quick Start

```python
from autopr.actions.ai_linting_fixer.file_splitter import FileSplitter, SplitConfig
from autopr.ai.core.providers.manager import LLMProviderManager

# Initialize the file splitter
splitter = FileSplitter(
    llm_manager=LLMProviderManager(config),
    split_config=SplitConfig()
)

# Split a file
chunks = await splitter.split_file("large_file.py")
```

## Configuration

```python
from autopr.actions.ai_linting_fixer.file_splitter import SplitConfig

config = SplitConfig(
    max_chunk_size=1000,
    overlap_lines=10,
    preserve_context=True
)
```

## Advanced Usage

```python
from autopr.actions.ai_linting_fixer.file_splitter import FileSplitter, SplitConfig
from autopr.ai.core.providers.manager import LLMProviderManager

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

## Integration

The file splitter integrates seamlessly with the AutoPR quality engine:

```python
from autopr.actions.quality_engine.engine import QualityEngine
from autopr.actions.ai_linting_fixer.file_splitter import FileSplitter

# Use in quality analysis
quality_engine = QualityEngine()
splitter = FileSplitter(llm_manager, config)

# Analyze split files
results = await quality_engine.analyze_files(chunks)
```

## Documentation

For detailed usage instructions, see the [User Guide](USER_GUIDE.md).

## Contributing

Contributions are welcome! Please see the main AutoPR contributing guidelines.
