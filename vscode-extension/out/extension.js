"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = void 0;
const vscode = __importStar(require("vscode"));
const child_process_1 = require("child_process");
const path = __importStar(require("path"));
function activate(context) {
    console.log('AutoPR extension is now active!');
    // Register commands
    const qualityCheckCommand = vscode.commands.registerCommand('autopr.qualityCheck', () => {
        runQualityCheck();
    });
    const qualityCheckFileCommand = vscode.commands.registerCommand('autopr.qualityCheckFile', () => {
        runQualityCheckFile();
    });
    const qualityCheckWorkspaceCommand = vscode.commands.registerCommand('autopr.qualityCheckWorkspace', () => {
        runQualityCheckWorkspace();
    });
    const fileSplitCommand = vscode.commands.registerCommand('autopr.fileSplit', () => {
        runFileSplit();
    });
    const autoFixCommand = vscode.commands.registerCommand('autopr.autoFix', () => {
        runAutoFix();
    });
    const showDashboardCommand = vscode.commands.registerCommand('autopr.showDashboard', () => {
        showDashboard();
    });
    const configureCommand = vscode.commands.registerCommand('autopr.configure', () => {
        showConfiguration();
    });
    // Register diagnostic collection
    const diagnosticCollection = vscode.languages.createDiagnosticCollection('autopr');
    context.subscriptions.push(diagnosticCollection);
    // Add commands to subscriptions
    context.subscriptions.push(qualityCheckCommand, qualityCheckFileCommand, qualityCheckWorkspaceCommand, fileSplitCommand, autoFixCommand, showDashboardCommand, configureCommand);
}
exports.activate = activate;
async function runQualityCheck() {
    const config = vscode.workspace.getConfiguration('autopr');
    const mode = config.get('qualityMode', 'fast');
    try {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active file to check');
            return;
        }
        const filePath = editor.document.fileName;
        const result = await executeAutoPRCommand(['check', '--mode', mode, '--files', filePath]);
        if (result.success) {
            displayQualityResults(result);
        }
        else {
            vscode.window.showErrorMessage('Quality check failed');
        }
    }
    catch (error) {
        vscode.window.showErrorMessage(`Quality check error: ${error}`);
    }
}
async function runQualityCheckFile() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No active file to check');
        return;
    }
    const filePath = editor.document.fileName;
    const config = vscode.workspace.getConfiguration('autopr');
    const mode = config.get('qualityMode', 'fast');
    try {
        const result = await executeAutoPRCommand(['check', '--mode', mode, '--files', filePath]);
        if (result.success) {
            displayQualityResults(result);
        }
        else {
            vscode.window.showErrorMessage('File quality check failed');
        }
    }
    catch (error) {
        vscode.window.showErrorMessage(`File quality check error: ${error}`);
    }
}
async function runQualityCheckWorkspace() {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders) {
        vscode.window.showErrorMessage('No workspace folder found');
        return;
    }
    const config = vscode.workspace.getConfiguration('autopr');
    const mode = config.get('qualityMode', 'fast');
    try {
        const result = await executeAutoPRCommand(['check', '--mode', mode, '--directory', workspaceFolders[0].uri.fsPath]);
        if (result.success) {
            displayQualityResults(result);
        }
        else {
            vscode.window.showErrorMessage('Workspace quality check failed');
        }
    }
    catch (error) {
        vscode.window.showErrorMessage(`Workspace quality check error: ${error}`);
    }
}
async function runFileSplit() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No active file to split');
        return;
    }
    const filePath = editor.document.fileName;
    // Show input dialog for split options
    const maxLines = await vscode.window.showInputBox({
        prompt: 'Maximum lines per component',
        value: '100',
        validateInput: (value) => {
            const num = parseInt(value);
            return isNaN(num) || num <= 0 ? 'Please enter a positive number' : null;
        }
    });
    if (!maxLines)
        return;
    try {
        const result = await executeAutoPRCommand(['split', filePath, '--max-lines', maxLines, '--dry-run']);
        if (result.success) {
            vscode.window.showInformationMessage(`File split analysis complete. Would create ${result.components?.length || 0} components.`);
            // Ask if user wants to proceed with actual split
            const proceed = await vscode.window.showQuickPick(['Yes', 'No'], {
                placeHolder: 'Proceed with actual file split?'
            });
            if (proceed === 'Yes') {
                const outputDir = await vscode.window.showInputBox({
                    prompt: 'Output directory for split files',
                    value: path.dirname(filePath) + '/split'
                });
                if (outputDir) {
                    const splitResult = await executeAutoPRCommand(['split', filePath, '--max-lines', maxLines, '--output-dir', outputDir]);
                    if (splitResult.success) {
                        vscode.window.showInformationMessage('File split completed successfully!');
                    }
                }
            }
        }
        else {
            vscode.window.showErrorMessage('File split failed');
        }
    }
    catch (error) {
        vscode.window.showErrorMessage(`File split error: ${error}`);
    }
}
async function runAutoFix() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No active file to fix');
        return;
    }
    const filePath = editor.document.fileName;
    const config = vscode.workspace.getConfiguration('autopr');
    const mode = config.get('qualityMode', 'fast');
    try {
        const result = await executeAutoPRCommand(['check', '--mode', mode, '--files', filePath, '--auto-fix']);
        if (result.success) {
            vscode.window.showInformationMessage('Auto-fix completed successfully!');
            // Refresh the document to show changes
            await editor.document.save();
        }
        else {
            vscode.window.showErrorMessage('Auto-fix failed');
        }
    }
    catch (error) {
        vscode.window.showErrorMessage(`Auto-fix error: ${error}`);
    }
}
function showDashboard() {
    const config = vscode.workspace.getConfiguration('autopr');
    const port = 8080;
    const host = 'localhost';
    vscode.window.showInformationMessage(`AutoPR Dashboard would start on http://${host}:${port}`);
    // TODO: Implement actual dashboard launch
}
function showConfiguration() {
    vscode.commands.executeCommand('workbench.action.openSettings', 'autopr');
}
async function executeAutoPRCommand(args) {
    return new Promise((resolve, reject) => {
        const config = vscode.workspace.getConfiguration('autopr');
        const pythonPath = config.get('pythonPath', 'python');
        const process = (0, child_process_1.spawn)(pythonPath, ['-m', 'autopr.cli.main', ...args], {
            cwd: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath
        });
        let stdout = '';
        let stderr = '';
        process.stdout.on('data', (data) => {
            stdout += data.toString();
        });
        process.stderr.on('data', (data) => {
            stderr += data.toString();
        });
        process.on('close', (code) => {
            if (code === 0) {
                try {
                    const result = JSON.parse(stdout);
                    resolve(result);
                }
                catch (error) {
                    reject(new Error('Failed to parse AutoPR output'));
                }
            }
            else {
                reject(new Error(`AutoPR command failed: ${stderr}`));
            }
        });
        process.on('error', (error) => {
            reject(new Error(`Failed to execute AutoPR: ${error.message}`));
        });
    });
}
function displayQualityResults(result) {
    const config = vscode.workspace.getConfiguration('autopr');
    const showNotifications = config.get('showNotifications', true);
    if (showNotifications) {
        const message = `Quality check completed: ${result.total_issues} issues found in ${result.processing_time.toFixed(2)}s`;
        vscode.window.showInformationMessage(message);
    }
    // Create output channel for detailed results
    const outputChannel = vscode.window.createOutputChannel('AutoPR');
    outputChannel.show();
    outputChannel.appendLine('AutoPR Quality Check Results');
    outputChannel.appendLine('='.repeat(50));
    outputChannel.appendLine(`Total Issues: ${result.total_issues}`);
    outputChannel.appendLine(`Processing Time: ${result.processing_time.toFixed(2)}s`);
    outputChannel.appendLine('');
    if (result.issues_by_tool) {
        for (const [tool, issues] of Object.entries(result.issues_by_tool)) {
            outputChannel.appendLine(`${tool}: ${issues.length} issues`);
            for (const issue of issues) {
                outputChannel.appendLine(`  ${issue.file}:${issue.line}:${issue.column} - ${issue.message}`);
            }
            outputChannel.appendLine('');
        }
    }
}
function deactivate() {
    console.log('AutoPR extension is now deactivated!');
}
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map