# AutoPR VS Code Extension

AI-Powered Code Quality and Automation for VS Code

## Features

### 🚀 Quality Analysis
- **Multi-mode Analysis**: Ultra-fast, Fast, Smart, Comprehensive, and AI-Enhanced modes
- **Real-time Feedback**: Instant quality checks as you code
- **File & Workspace Analysis**: Check individual files or entire workspaces
- **Intelligent Issue Detection**: AI-powered code quality analysis

### 🔧 Auto-Fix Capabilities
- **Automatic Issue Resolution**: Fix common code quality issues automatically
- **Smart Suggestions**: AI-driven recommendations for code improvements
- **Safe Auto-fix**: Preview changes before applying

### 📁 File Management
- **AI-Enhanced File Splitting**: Intelligently split large files based on complexity
- **Component Analysis**: Understand file structure and complexity
- **Backup & Validation**: Safe file operations with automatic backups

### 📊 Dashboard & Metrics
- **Quality Dashboard**: Web-based interface for detailed analysis
- **Performance Metrics**: Track code quality improvements over time
- **Issue History**: View and manage quality issues

## Installation

### From VSIX Package
1. Download the latest `.vsix` package
2. Open VS Code
3. Go to Extensions (Ctrl+Shift+X)
4. Click the "..." menu and select "Install from VSIX..."
5. Select the downloaded package

### From Source
1. Clone the repository
2. Navigate to the `vscode-extension` directory
3. Run `npm install`
4. Run `npm run compile`
5. Press F5 to launch the extension in a new VS Code window

## Usage

### Quick Start
1. Open a Python, JavaScript, or TypeScript file
2. Right-click in the editor or use Command Palette (Ctrl+Shift+P)
3. Select "AutoPR: Check Current File"
4. View results in the AutoPR output panel

### Commands

#### Quality Analysis
- **AutoPR: Run Quality Check** - Quick quality check with default settings
- **AutoPR: Check Current File** - Analyze the currently open file
- **AutoPR: Check Workspace** - Analyze all files in the workspace

#### File Operations
- **AutoPR: Split Large File** - Split large files into manageable components
- **AutoPR: Auto-Fix Issues** - Automatically fix detected issues

#### Configuration
- **AutoPR: Show Dashboard** - Open the web-based dashboard
- **AutoPR: Configure** - Open extension settings

### Context Menu
Right-click in the editor to access:
- Check Current File
- Auto-Fix Issues

## Configuration

### Extension Settings

| Setting                    | Description                    | Default  |
| -------------------------- | ------------------------------ | -------- |
| `autopr.enabled`           | Enable/disable the extension   | `true`   |
| `autopr.qualityMode`       | Default quality analysis mode  | `fast`   |
| `autopr.autoFixEnabled`    | Enable automatic fixing        | `false`  |
| `autopr.showNotifications` | Show operation notifications   | `true`   |
| `autopr.pythonPath`        | Path to Python executable      | `python` |
| `autopr.maxFileSize`       | Maximum file size for analysis | `10000`  |

### Quality Modes

- **Ultra-Fast**: Basic syntax and style checks
- **Fast**: Standard quality analysis
- **Smart**: Context-aware analysis
- **Comprehensive**: Full code review
- **AI-Enhanced**: AI-powered analysis with suggestions

## Development

### Prerequisites
- Node.js 16+
- TypeScript 4.8+
- VS Code Extension Development Tools

### Build Commands
```bash
npm install          # Install dependencies
npm run compile      # Compile TypeScript
npm run watch        # Watch for changes
npm run lint         # Run ESLint
npm run test         # Run tests
```

### Project Structure
```
vscode-extension/
├── src/
│   └── extension.ts     # Main extension code
├── package.json         # Extension manifest
├── tsconfig.json        # TypeScript configuration
├── .eslintrc.json       # ESLint configuration
└── .vscode/            # VS Code workspace settings
```

### Testing
1. Run `npm run test` to execute unit tests
2. Press F5 to launch extension in debug mode
3. Use the Extension Test configuration for integration tests

## Troubleshooting

### Common Issues

**Extension not activating**
- Check that you have Python installed and accessible
- Verify the `autopr.pythonPath` setting
- Check the AutoPR output panel for error messages

**Quality checks failing**
- Ensure AutoPR CLI is installed: `pip install autopr`
- Check Python environment and dependencies
- Verify file permissions

**Auto-fix not working**
- Enable `autopr.autoFixEnabled` in settings
- Check that the file is saved before running auto-fix
- Review the output panel for specific error messages

### Debug Mode
1. Open the extension in VS Code
2. Press F5 to launch debug mode
3. Check the Debug Console for detailed logs
4. Use the Developer Tools (Help > Toggle Developer Tools)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run `npm run lint` and `npm run test`
6. Submit a pull request

## License

This extension is part of the AutoPR project and follows the same license terms.

## Support

- **Issues**: Report bugs and feature requests on GitHub
- **Documentation**: See the main AutoPR documentation
- **Community**: Join our Discord server for discussions
