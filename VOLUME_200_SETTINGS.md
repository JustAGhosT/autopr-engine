# Volume 200 Settings Documentation

This document describes the tool configurations that are active when the AutoPR Engine volume control is set to level 200.

## Volume Control System Overview

The AutoPR Engine uses a HiFi-style volume control system with a 0-1000 scale in ticks of 5. Volume level 200 corresponds to a "LOW" setting that enables basic linting and quality checks while maintaining a relatively permissive development environment.

## Active Tools at Volume 200

The following tools are enabled at volume level 200:
- git
- github-actions
- json
- powershell
- problems
- python
- typescript
- yaml

## Tool Configurations at Volume 200

### Python (strict type checking with linting)
- python.enabled: true
- python.languageServer: "Pylance"
- python.analysis.enabled: true
- python.analysis.typeCheckingMode: "strict"
- python.analysis.diagnosticMode: "workspace"
- python.linting.enabled: true
- python.linting.flake8Enabled: true
- python.formatting.enabled: false
- python.analysis.autoImportCompletions: true

### Git
- git.enabled: true
- git.autorefresh: true
- git.decorations.enabled: true
- git.showPushSuccessNotification: true
- git.confirmSync: false
- git.autofetch: true
- git.enableSmartCommit: true

### JSON
- json.enabled: true
- json.validate.enable: true
- json.schemas: [] (default schemas)
- json.format.enable: true

### TypeScript
- typescript.enabled: true
- typescript.preferences.includePackageJsonAutoImports: "auto"
- typescript.suggest.enabled: true
- typescript.suggest.autoImports: true
- typescript.format.semicolons: "ignore"
- typescript.format.insertSpaceAfterOpeningAndBeforeClosingNonemptyBraces: true

### YAML
- yaml.enabled: true
- yaml.validate: false
- yaml.completion: true
- yaml.hover: true
- yaml.format.enable: false
- yaml.trace.server: "off"
- redhat.vscode-yaml.enabled: true

### Problems
- problems.decorations.enabled: true
- problems.showCurrentInStatus: true
- problems.sortOrder: "position"
- problems.showPlaceholders: true
- problems.visibility: true

### PowerShell
- powershell.scriptAnalysis.enable: true
- powershell.integratedConsole.showOnStartup: true
- powershell.codeFormatting.enabled: true
- powershell.helpCompletion: "BlockComment"
- powershell.integratedConsole.focusConsoleOnExecute: true

### GitHub Actions
- github-actions.validate: true
- github-actions.enableWorkflowValidation: true
- github-actions.enableSchemaValidation: true
- github-actions.logLevel: "info"
- github-actions.telemetry.enabled: false

## Inactive Tools at Volume 200

The following tools do not have specific configurations at volume level 200 and remain inactive:
- pre_commit
- pyright
- ruff
- vscode

## Verification

All tests pass successfully at volume level 200, confirming that the configuration is stable and functional.
