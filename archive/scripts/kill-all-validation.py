#!/usr/bin/env python3
"""
Kill All Validation - Completely disable all validation in the IDE
"""

import json
from pathlib import Path


def main():

    # Create the most aggressive VS Code settings possible
    aggressive_settings = {
        # Disable ALL Python features
        "python.enabled": False,
        "python.linting.enabled": False,
        "python.formatting.enabled": False,
        "python.analysis.enabled": False,
        "python.languageServer": "None",
        # Disable ALL linting
        "python.linting.flake8Enabled": False,
        "python.linting.mypyEnabled": False,
        "python.linting.pylintEnabled": False,
        "python.linting.pydocstyleEnabled": False,
        "python.linting.banditEnabled": False,
        "python.linting.ruffEnabled": False,
        # Disable ALL formatting
        "python.formatting.provider": "none",
        "python.formatting.blackEnabled": False,
        "python.formatting.isortEnabled": False,
        "python.formatting.ruffEnabled": False,
        # Disable ALL analysis
        "python.analysis.typeCheckingMode": "off",
        "python.analysis.diagnosticMode": "off",
        "python.analysis.autoImportCompletions": False,
        "python.analysis.useLibraryCodeForTypes": False,
        "python.analysis.autoSearchPaths": False,
        # Disable ALL editor features
        "editor.formatOnSave": False,
        "editor.formatOnPaste": False,
        "editor.formatOnType": False,
        "editor.codeActionsOnSave": {
            "source.organizeImports": "never",
            "source.fixAll": "never",
            "source.fixAll.eslint": "never",
        },
        # Disable ALL problems
        "problems.decorations.enabled": False,
        "problems.showCurrentInStatus": False,
        # Disable ALL YAML validation
        "yaml.validate": False,
        "yaml.schemas": {},
        "yaml.customTags": [],
        "yaml.format.enable": False,
        "yaml.hover": False,
        "yaml.completion": False,
        "yaml.validate.enable": False,
        # Disable ALL PowerShell validation
        "powershell.scriptAnalysis.enable": False,
        "powershell.integratedConsole.showOnStartup": False,
        "powershell.debugging.enabled": False,
        "powershell.codeFormatting.enabled": False,
        "powershell.helpCompletion": "Disabled",
        "powershell.integratedConsole.focusConsoleOnExecute": False,
        # Disable ALL GitHub Actions validation
        "github-actions.validate": False,
        "github-actions.enableWorkflowValidation": False,
        "github-actions.enableSchemaValidation": False,
        # Disable ALL extensions
        "extensions.ignoreRecommendations": True,
        "extensions.autoUpdate": False,
        "extensions.autoCheckUpdates": False,
        # Disable ALL Cursor features
        "cursor.python.linting.enabled": False,
        "cursor.python.formatting.enabled": False,
        "cursor.python.analysis.enabled": False,
        "cursor.linting.enabled": False,
        "cursor.formatting.enabled": False,
        "cursor.diagnostics.enabled": False,
        # Disable ALL spell checking
        "cSpell.enabled": False,
        "cSpell.enableFiletypes": [],
        "cSpell.diagnosticLevel": "Hint",
        "cSpell.showStatus": False,
        # Disable ALL markdown linting
        "markdownlint.enable": False,
        "markdownlint.config": {"default": False},
        "markdownlint.customRules": [],
        "markdownlint.run": "never",
        # Disable ALL TabNine
        "tabnine.enabled": False,
        "tabnine.experimentalAutoImports": False,
        "tabnine.autoComplete": False,
        # Disable ALL Continue/Monica
        "continue.enabled": False,
        "continue.telemetryEnabled": False,
        "continue.enableTabAutocomplete": False,
        "monica.enabled": False,
        "monica.telemetryEnabled": False,
        "monica.autoComplete": False,
        # Disable ALL Ruff
        "ruff.enable": False,
        "ruff.lint.enable": False,
        "ruff.format.enable": False,
        "ruff.organizeImports.enable": False,
        "ruff.server.enable": False,
        # Disable ALL other validators
        "eslint.enable": False,
        "typescript.validate.enable": False,
        "json.validate.enable": False,
        "css.validate": False,
        "html.validate.scripts": False,
        "html.validate.styles": False,
        # Disable ALL hover and completion
        "editor.hover.enabled": False,
        "editor.quickSuggestions": {"other": False, "comments": False, "strings": False},
        "editor.suggestOnTriggerCharacters": False,
        "editor.acceptSuggestionOnEnter": "off",
        # Disable ALL error reporting
        "python.linting.maxNumberOfProblems": 0,
        "python.analysis.include": [],
        "python.analysis.exclude": ["**/*", "*"],
        "python.analysis.ignore": ["**/*", "*"],
        # Disable ALL file watching
        "files.watcherExclude": {
            "**/node_modules/**": True,
            "**/__pycache__/**": True,
            "**/.git/**": True,
            "**/venv/**": True,
            "**/.venv/**": True,
            "**/dist/**": True,
            "**/build/**": True,
            "**/*.pyc": True,
        },
        # Disable ALL search
        "search.exclude": {
            "**/node_modules": True,
            "**/__pycache__": True,
            "**/.git": True,
            "**/venv": True,
            "**/.venv": True,
            "**/dist": True,
            "**/build": True,
            "**/*.pyc": True,
        },
    }

    # Write the aggressive settings
    vscode_dir = Path(".vscode")
    vscode_dir.mkdir(exist_ok=True)

    settings_file = vscode_dir / "settings.json"
    with open(settings_file, "w") as f:
        json.dump(aggressive_settings, f, indent=2)





if __name__ == "__main__":
    main()
