import * as vscode from 'vscode';
import { spawn } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

interface AutoPRIssue {
    file: string;
    line: number;
    column: number;
    message: string;
    severity: 'error' | 'warning' | 'info';
    tool: string;
    code?: string;
}

interface AutoPRResult {
    success: boolean;
    total_issues: number;
    issues_by_tool: Record<string, AutoPRIssue[]>;
    processing_time: number;
}

export function activate(context: vscode.ExtensionContext) {
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

    // Register providers
    const diagnosticCollection = vscode.languages.createDiagnosticCollection('autopr');
    context.subscriptions.push(diagnosticCollection);

    // Register tree data providers
    const issuesProvider = new AutoPRIssuesProvider();
    vscode.window.registerTreeDataProvider('autoprIssues', issuesProvider);

    const metricsProvider = new AutoPRMetricsProvider();
    vscode.window.registerTreeDataProvider('autoprMetrics', metricsProvider);

    const historyProvider = new AutoPRHistoryProvider();
    vscode.window.registerTreeDataProvider('autoprHistory', historyProvider);

    // Add commands to subscriptions
    context.subscriptions.push(
        qualityCheckCommand,
        qualityCheckFileCommand,
        qualityCheckWorkspaceCommand,
        fileSplitCommand,
        autoFixCommand,
        showDashboardCommand,
        configureCommand
    );

    // Set up file watchers for automatic quality checks
    setupFileWatchers(context, diagnosticCollection);
}

async function runQualityCheck() {
    const config = vscode.workspace.getConfiguration('autopr');
    const mode = config.get<string>('qualityMode', 'fast');
    
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
        } else {
            vscode.window.showErrorMessage('Quality check failed');
        }
    } catch (error) {
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
    const mode = config.get<string>('qualityMode', 'fast');

    try {
        const result = await executeAutoPRCommand(['check', '--mode', mode, '--files', filePath]);
        
        if (result.success) {
            displayQualityResults(result);
            updateDiagnostics(result, filePath);
        } else {
            vscode.window.showErrorMessage('File quality check failed');
        }
    } catch (error) {
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
    const mode = config.get<string>('qualityMode', 'fast');

    try {
        const result = await executeAutoPRCommand(['check', '--mode', mode, '--directory', workspaceFolders[0].uri.fsPath]);
        
        if (result.success) {
            displayQualityResults(result);
            updateWorkspaceDiagnostics(result);
        } else {
            vscode.window.showErrorMessage('Workspace quality check failed');
        }
    } catch (error) {
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

    if (!maxLines) return;

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
        } else {
            vscode.window.showErrorMessage('File split failed');
        }
    } catch (error) {
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
    const mode = config.get<string>('qualityMode', 'fast');

    try {
        const result = await executeAutoPRCommand(['check', '--mode', mode, '--files', filePath, '--auto-fix']);
        
        if (result.success) {
            vscode.window.showInformationMessage('Auto-fix completed successfully!');
            // Refresh the document to show changes
            await editor.document.save();
        } else {
            vscode.window.showErrorMessage('Auto-fix failed');
        }
    } catch (error) {
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

async function executeAutoPRCommand(args: string[]): Promise<AutoPRResult> {
    return new Promise((resolve, reject) => {
        const config = vscode.workspace.getConfiguration('autopr');
        const pythonPath = config.get<string>('pythonPath', 'python');
        
        const process = spawn(pythonPath, ['-m', 'autopr.cli.main', ...args], {
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
                } catch (error) {
                    reject(new Error('Failed to parse AutoPR output'));
                }
            } else {
                reject(new Error(`AutoPR command failed: ${stderr}`));
            }
        });

        process.on('error', (error) => {
            reject(new Error(`Failed to execute AutoPR: ${error.message}`));
        });
    });
}

function displayQualityResults(result: AutoPRResult) {
    const config = vscode.workspace.getConfiguration('autopr');
    const showNotifications = config.get<boolean>('showNotifications', true);

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

function updateDiagnostics(result: AutoPRResult, filePath: string) {
    const diagnosticCollection = vscode.languages.getDiagnostics().get('autopr');
    if (!diagnosticCollection) return;

    const diagnostics: vscode.Diagnostic[] = [];

    if (result.issues_by_tool) {
        for (const issues of Object.values(result.issues_by_tool)) {
            for (const issue of issues) {
                if (issue.file === filePath) {
                    const range = new vscode.Range(
                        issue.line - 1,
                        issue.column - 1,
                        issue.line - 1,
                        issue.column
                    );

                    const diagnostic = new vscode.Diagnostic(
                        range,
                        issue.message,
                        getDiagnosticSeverity(issue.severity)
                    );

                    diagnostic.source = 'AutoPR';
                    diagnostic.code = issue.code;
                    diagnostics.push(diagnostic);
                }
            }
        }
    }

    diagnosticCollection.set(vscode.Uri.file(filePath), diagnostics);
}

function updateWorkspaceDiagnostics(result: AutoPRResult) {
    const diagnosticCollection = vscode.languages.getDiagnostics().get('autopr');
    if (!diagnosticCollection) return;

    // Clear existing diagnostics
    diagnosticCollection.clear();

    if (result.issues_by_tool) {
        const fileIssues: Record<string, vscode.Diagnostic[]> = {};

        for (const issues of Object.values(result.issues_by_tool)) {
            for (const issue of issues) {
                if (!fileIssues[issue.file]) {
                    fileIssues[issue.file] = [];
                }

                const range = new vscode.Range(
                    issue.line - 1,
                    issue.column - 1,
                    issue.line - 1,
                    issue.column
                );

                const diagnostic = new vscode.Diagnostic(
                    range,
                    issue.message,
                    getDiagnosticSeverity(issue.severity)
                );

                diagnostic.source = 'AutoPR';
                diagnostic.code = issue.code;
                fileIssues[issue.file].push(diagnostic);
            }
        }

        // Set diagnostics for each file
        for (const [file, diagnostics] of Object.entries(fileIssues)) {
            diagnosticCollection.set(vscode.Uri.file(file), diagnostics);
        }
    }
}

function getDiagnosticSeverity(severity: string): vscode.DiagnosticSeverity {
    switch (severity) {
        case 'error':
            return vscode.DiagnosticSeverity.Error;
        case 'warning':
            return vscode.DiagnosticSeverity.Warning;
        case 'info':
            return vscode.DiagnosticSeverity.Information;
        default:
            return vscode.DiagnosticSeverity.Warning;
    }
}

function setupFileWatchers(context: vscode.ExtensionContext, diagnosticCollection: vscode.DiagnosticCollection) {
    const config = vscode.workspace.getConfiguration('autopr');
    const autoFixEnabled = config.get<boolean>('autoFixEnabled', false);

    if (autoFixEnabled) {
        const fileSystemWatcher = vscode.workspace.createFileSystemWatcher('**/*.{py,js,ts}');
        
        fileSystemWatcher.onDidChange(async (uri) => {
            // Debounced auto-fix on file changes
            setTimeout(async () => {
                try {
                    const result = await executeAutoPRCommand(['check', '--mode', 'fast', '--files', uri.fsPath, '--auto-fix']);
                    if (result.success) {
                        updateDiagnostics(result, uri.fsPath);
                    }
                } catch (error) {
                    // Silent fail for auto-fix
                }
            }, 1000);
        });

        context.subscriptions.push(fileSystemWatcher);
    }
}

// Tree Data Providers
class AutoPRIssuesProvider implements vscode.TreeDataProvider<AutoPRIssueItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<AutoPRIssueItem | undefined | null | void> = new vscode.EventEmitter<AutoPRIssueItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<AutoPRIssueItem | undefined | null | void> = this._onDidChangeTreeData.event;

    getTreeItem(element: AutoPRIssueItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: AutoPRIssueItem): Thenable<AutoPRIssueItem[]> {
        // TODO: Implement actual issues loading
        return Promise.resolve([]);
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }
}

class AutoPRMetricsProvider implements vscode.TreeDataProvider<AutoPRMetricsItem> {
    getTreeItem(element: AutoPRMetricsItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: AutoPRMetricsItem): Thenable<AutoPRMetricsItem[]> {
        // TODO: Implement metrics loading
        return Promise.resolve([]);
    }
}

class AutoPRHistoryProvider implements vscode.TreeDataProvider<AutoPRHistoryItem> {
    getTreeItem(element: AutoPRHistoryItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: AutoPRHistoryItem): Thenable<AutoPRHistoryItem[]> {
        // TODO: Implement history loading
        return Promise.resolve([]);
    }
}

// Tree Items
class AutoPRIssueItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly issue?: AutoPRIssue
    ) {
        super(label, collapsibleState);
    }
}

class AutoPRMetricsItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState
    ) {
        super(label, collapsibleState);
    }
}

class AutoPRHistoryItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState
    ) {
        super(label, collapsibleState);
    }
}

export function deactivate() {
    console.log('AutoPR extension is now deactivated!');
}
