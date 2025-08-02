# Platform Detection Configuration

This document describes the configuration structure for platform detection in AutoPR Engine.

## Overview

The platform detection system identifies development platforms and tools used in a codebase. It
supports three main categories of platforms:

1. **Core Platforms**: General development platforms and frameworks
2. **AI Platforms**: AI development tools and services
3. **Cloud Platforms**: Cloud service providers and platforms

## Configuration Structure

### Category Configuration File (`*_platforms.json`)

Each category (core, AI, cloud) has a main configuration file that lists all platforms in that
category:

```json
{
  "version": "1.0",
  "last_updated": "YYYY-MM-DD",
  "description": "Description of the platform category",
  "platforms": [
    {
      "id": "platform_id",
      "name": "Platform Name",
      "category": "platform_category",
      "description": "Platform description",
      "config_file": "path/to/platform_config.json",
      "is_active": true,
      "priority": 10
    }
  ],
  "metadata": {
    "default_confidence_weights": {
      "files": 0.4,
      "dependencies": 0.3,
      "folder_patterns": 0.15,
      "commit_patterns": 0.1,
      "content_patterns": 0.05
    },
    "categories": ["category_name"],
    "last_updated_by": "AutoPR Engine",
    "schema_version": "1.1.0"
  }
}
```

### Platform Configuration File (`platform_id.json`)

Each platform has its own configuration file with detailed detection rules:

```json
{
  "id": "platform_id",
  "name": "Platform Name",
  "description": "Detailed platform description",
  "category": "platform_category",
  "detection": {
    "files": [".platform_file", "config/platform_config.json"],
    "dependencies": ["@platform/package", "platform-package"],
    "folder_patterns": ["platform-*", "*-platform"],
    "commit_patterns": ["platform", "platform:setup"],
    "content_patterns": ["platform.config", "platform_setting"]
  },
  "project_config": {
    "features": ["feature1", "feature2"],
    "configuration_files": ["platform.config", ".platform/settings.json"],
    "documentation": "https://platform.example.com/docs"
  },
  "metadata": {
    "vendor": "Vendor Name",
    "website": "https://platform.example.com",
    "pricing_model": "freemium",
    "supported_languages": ["python", "javascript", "typescript"],
    "last_updated": "YYYY-MM-DD",
    "version": "1.0.0"
  }
}
```

## Detection Logic

The platform detector uses a weighted scoring system based on multiple factors:

1. **File Detection** (40% weight):
   - Looks for specific files or directories that indicate the platform
   - Example: `.cursor` directory for Cursor IDE

1. **Dependency Detection** (30% weight):
   - Checks for platform-specific packages in dependency files
   - Example: `@githubnext/github-copilot-cli` for GitHub Copilot

1. **Folder Pattern Matching** (15% weight):
   - Matches directory names against known patterns
   - Example: `*-copilot` for GitHub Copilot related directories

1. **Commit Message Patterns** (10% weight):
   - Looks for platform-related terms in commit messages
   - Example: "Add Copilot configuration"

1. **Content Patterns** (5% weight):
   - Searches for platform-specific strings in files
   - Example: "github-copilot" in configuration files

## Adding a New Platform

1. Create a new JSON file in the appropriate category directory (`core/`, `ai/`, or `cloud/`)
2. Define the platform's detection rules and metadata
3. Add a reference to the new platform in the category's `*_platforms.json` file
4. Update tests to include the new platform

## Example: Adding a New AI Platform

1. Create `configs/platforms/ai/new_platform.json`:

   ```json
   {
     "id": "new_platform",
     "name": "New AI Platform",
     "description": "Description of the new AI platform",
     "category": "ai_development",
     "detection": {
       "files": [".newplatform", "newplatform.config"],
       "dependencies": ["@newplatform/sdk"],
       "folder_patterns": ["newplatform-*"],
       "commit_patterns": ["newplatform", "add newplatform"],
       "content_patterns": ["newplatform.config"]
     },
     "project_config": {
       "features": ["ai_completion", "code_generation"],
       "configuration_files": ["newplatform.config"],
       "documentation": "<https://newplatform.ai/docs">
     },
     "metadata": {
       "vendor": "New AI Inc.",
       "website": "<https://newplatform.ai",>
       "pricing_model": "freemium",
       "supported_languages": ["python", "javascript", "typescript"],
       "last_updated": "2025-07-27",
       "version": "1.0.0"
     }
   }
   ```

1. Add the platform to `configs/platforms/ai_platforms.json`:

   ```json
   {
     "platforms": [
       // ... existing platforms ...
       {
         "id": "new_platform",
         "name": "New AI Platform",
         "category": "ai_development",
         "description": "Description of the new AI platform",
         "config_file": "ai/new_platform.json",
         "is_active": true,
         "priority": 5
       }
     ]
   }
   ```

## Testing Platform Detection

To test if a platform is detected correctly:

1. Create a test directory with files that match the detection patterns
2. Run the platform detector against the test directory
3. Verify that the platform is detected with the expected confidence score

Example test:

```python
from autopr.actions.platform_detection import detect_platforms

def test_platform_detection():
    test_dir = Path("path/to/test/directory")
    results = detect_platforms(test_dir)

    # Check if our platform was detected
    assert "new_platform" in results.detected_platforms
    assert results.get_confidence("new_platform") > 0.5
```

## Best Practices

1. **Be Specific**: Use unique file patterns to avoid false positives
2. **Document**: Add clear descriptions and documentation links
3. **Test**: Create test cases for each platform
4. **Version**: Update the version when making changes to the configuration
5. **Prioritize**: Set appropriate priority levels for platforms (higher numbers are checked first)

## Troubleshooting

### Platform Not Detected

1. Check if the platform is active in its category file (`is_active: true`)
2. Verify file patterns match actual files in the project
3. Check if dependency names match those in package.json/requirements.txt
4. Ensure the platform's priority is set appropriately

### False Positives

1. Make file patterns more specific
2. Add negative patterns if needed
3. Adjust confidence weights in the category configuration
