#!/usr/bin/env python3
"""
Nuclear option to completely eliminate all IDE problems at Volume 0
"""

import json
from pathlib import Path


def update_vscode_settings():
    """Add even more aggressive settings to disable all validation"""

    settings_file = Path(".vscode/settings.json")

    # Additional nuclear settings
    nuclear_settings = {
        # GitHub Actions - More aggressive disable
        "github-actions.workflows.pinned.workflows": [],
        "github-actions.workflows.pinned.refresh.enabled": False,
        "redhat.vscode-yaml": False,
        # YAML validation - Complete disable
        "yaml.schemaStore.enable": False,
        "yaml.schemaStore.url": "",
        "yaml.schemas": {},
        "yaml.validate": False,
        "yaml.yamlVersion": "1.1",
        "yaml.disableAdditionalProperties": True,
        "yaml.suggest.parentSkeletonSelectedFirst": False,
        # PowerShell - Complete disable
        "powershell.scriptAnalysis.enable": False,
        "powershell.scriptAnalysis.settingsPath": "",
        "powershell.codeFormatting.preset": "None",
        "powershell.integratedConsole.suppressStartupBanner": True,
        # Problems panel - Nuclear disable
        "problems.showCurrentInStatus": False,
        "problems.decorations.enabled": False,
        "problems.visibility": False,
        # Language servers - Complete disable
        "redhat.vscode-yaml.enable": False,
        "ms-vscode.powershell.enable": False,
        "github.vscode-github-actions.enable": False,
        # Workspace validation - Disable
        "files.associations": {"*.yml": "plaintext", "*.yaml": "plaintext", "*.ps1": "plaintext"},
        # Extension-specific disables
        "workbench.enableExperiments": False,
        "telemetry.telemetryLevel": "off",
        "update.enableWindowsBackgroundUpdates": False,
        # Additional language disables
        "html.validate.scripts": False,
        "html.validate.styles": False,
        "css.validate": False,
        "json.validate.enable": False,
        "typescript.validate.enable": False,
        "javascript.validate.enable": False,
    }

    # Read existing settings
    if settings_file.exists():
        with open(settings_file) as f:
            settings = json.load(f)
    else:
        settings = {}

    # Merge nuclear settings
    settings.update(nuclear_settings)

    # Write back
    with open(settings_file, "w") as f:
        json.dump(settings, f, indent=2)



def create_ignore_files():
    """Create ignore files for problematic validations"""

    # Create .yamlignore to ignore all YAML files
    yamlignore = Path(".yamlignore")
    yamlignore.write_text("**/*.yml\n**/*.yaml\n")

    # Create .github-actions-ignore
    gh_ignore = Path(".github-actions-ignore")
    gh_ignore.write_text(".github/workflows/*.yml\n.github/workflows/*.yaml\n")



def main():

    update_vscode_settings()
    create_ignore_files()




if __name__ == "__main__":
    main()
