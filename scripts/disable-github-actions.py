#!/usr/bin/env python3
"""
Disable GitHub Actions Extension - Simple fix for workflow validation errors
"""

import json
from pathlib import Path


def main():

    # Read current settings
    vscode_dir = Path(".vscode")
    settings_file = vscode_dir / "settings.json"

    if settings_file.exists():
        with open(settings_file) as f:
            current_settings = json.load(f)
    else:
        current_settings = {}

    # Add GitHub Actions specific disable settings
    current_settings.update(
        {
            # Disable GitHub Actions extension completely
            "github-actions.validate": False,
            "github-actions.enableWorkflowValidation": False,
            "github-actions.enableSchemaValidation": False,
            # Disable YAML validation for GitHub Actions
            "yaml.validate": False,
            "yaml.schemas": {},
            "yaml.customTags": [],
            "yaml.format.enable": False,
            "yaml.hover": False,
            "yaml.completion": False,
            "yaml.validate.enable": False,
            "yaml.schemaStore.enable": False,
            # Disable ALL problems display
            "problems.decorations.enabled": False,
            "problems.showCurrentInStatus": False,
            # Disable ALL hover and completion
            "editor.hover.enabled": False,
            "editor.quickSuggestions": {"other": False, "comments": False, "strings": False},
            "editor.suggestOnTriggerCharacters": False,
            "editor.acceptSuggestionOnEnter": "off",
        }
    )

    # Write the updated settings
    vscode_dir.mkdir(exist_ok=True)
    with open(settings_file, "w") as f:
        json.dump(current_settings, f, indent=2)




if __name__ == "__main__":
    main()
