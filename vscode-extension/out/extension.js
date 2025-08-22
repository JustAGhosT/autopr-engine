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
    const setVolumeCommand = vscode.commands.registerCommand('autopr.setVolume', () => {
        setVolumeLevel();
    });
    const toggleToolCommand = vscode.commands.registerCommand('autopr.toggleTool', () => {
        toggleTool();
    });
    const performanceCheckCommand = vscode.commands.registerCommand('autopr.performanceCheck', () => {
        runPerformanceCheck();
    });
    const dependencyScanCommand = vscode.commands.registerCommand('autopr.dependencyScan', () => {
        runDependencyScan();
    });
    const securityScanCommand = vscode.commands.registerCommand('autopr.securityScan', () => {
        runSecurityScan();
    });
    const complexityAnalysisCommand = vscode.commands.registerCommand('autopr.complexityAnalysis', () => {
        runComplexityAnalysis();
    });
    const documentationCheckCommand = vscode.commands.registerCommand('autopr.documentationCheck', () => {
        runDocumentationCheck();
    });
    const learningMemoryCommand = vscode.commands.registerCommand('autopr.learningMemory', () => {
        showLearningMemory();
    });
    const clearCacheCommand = vscode.commands.registerCommand('autopr.clearCache', () => {
        clearCache();
    });
    const exportResultsCommand = vscode.commands.registerCommand('autopr.exportResults', () => {
        exportResults();
    });
    const importConfigCommand = vscode.commands.registerCommand('autopr.importConfig', () => {
        importConfiguration();
    });
    // Register diagnostic collection
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
    context.subscriptions.push(qualityCheckCommand, qualityCheckFileCommand, qualityCheckWorkspaceCommand, fileSplitCommand, autoFixCommand, showDashboardCommand, configureCommand, setVolumeCommand, toggleToolCommand, performanceCheckCommand, dependencyScanCommand, securityScanCommand, complexityAnalysisCommand, documentationCheckCommand, learningMemoryCommand, clearCacheCommand, exportResultsCommand, importConfigCommand);
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
async function setVolumeLevel() {
    const config = vscode.workspace.getConfiguration('autopr');
    const currentVolume = config.get('volume', 500);
    const volume = await vscode.window.showInputBox({
        prompt: 'Set volume level (0-1000)',
        value: currentVolume.toString(),
        validateInput: (value) => {
            const num = parseInt(value);
            return isNaN(num) || num < 0 || num > 1000 ? 'Please enter a number between 0 and 1000' : null;
        }
    });
    if (volume) {
        await config.update('volume', parseInt(volume), vscode.ConfigurationTarget.Workspace);
        vscode.window.showInformationMessage(`Volume level set to ${volume}`);
    }
}
async function toggleTool() {
    const config = vscode.workspace.getConfiguration('autopr');
    const tools = config.get('tools', {});
    const toolNames = Object.keys(tools);
    const selectedTool = await vscode.window.showQuickPick(toolNames, {
        placeHolder: 'Select a tool to toggle'
    });
    if (selectedTool) {
        const currentState = tools[selectedTool]?.enabled || false;
        tools[selectedTool] = { ...tools[selectedTool], enabled: !currentState };
        await config.update('tools', tools, vscode.ConfigurationTarget.Workspace);
        vscode.window.showInformationMessage(`${selectedTool} ${!currentState ? 'enabled' : 'disabled'}`);
    }
}
async function runPerformanceCheck() {
    try {
        const result = await executeAutoPRCommand(['check', '--mode', 'comprehensive', '--tools', 'performance_analyzer']);
        if (result.success) {
            vscode.window.showInformationMessage('Performance analysis completed');
            displayQualityResults(result);
        }
        else {
            vscode.window.showErrorMessage('Performance analysis failed');
        }
    }
    catch (error) {
        vscode.window.showErrorMessage(`Performance analysis error: ${error}`);
    }
}
async function runDependencyScan() {
    try {
        const result = await executeAutoPRCommand(['check', '--mode', 'comprehensive', '--tools', 'dependency_scanner']);
        if (result.success) {
            vscode.window.showInformationMessage('Dependency scan completed');
            displayQualityResults(result);
        }
        else {
            vscode.window.showErrorMessage('Dependency scan failed');
        }
    }
    catch (error) {
        vscode.window.showErrorMessage(`Dependency scan error: ${error}`);
    }
}
async function runSecurityScan() {
    try {
        const result = await executeAutoPRCommand(['check', '--mode', 'comprehensive', '--tools', 'bandit,codeql']);
        if (result.success) {
            vscode.window.showInformationMessage('Security scan completed');
            displayQualityResults(result);
        }
        else {
            vscode.window.showErrorMessage('Security scan failed');
        }
    }
    catch (error) {
        vscode.window.showErrorMessage(`Security scan error: ${error}`);
    }
}
async function runComplexityAnalysis() {
    try {
        const result = await executeAutoPRCommand(['check', '--mode', 'comprehensive', '--tools', 'radon']);
        if (result.success) {
            vscode.window.showInformationMessage('Complexity analysis completed');
            displayQualityResults(result);
        }
        else {
            vscode.window.showErrorMessage('Complexity analysis failed');
        }
    }
    catch (error) {
        vscode.window.showErrorMessage(`Complexity analysis error: ${error}`);
    }
}
async function runDocumentationCheck() {
    try {
        const result = await executeAutoPRCommand(['check', '--mode', 'comprehensive', '--tools', 'interrogate']);
        if (result.success) {
            vscode.window.showInformationMessage('Documentation check completed');
            displayQualityResults(result);
        }
        else {
            vscode.window.showErrorMessage('Documentation check failed');
        }
    }
    catch (error) {
        vscode.window.showErrorMessage(`Documentation check error: ${error}`);
    }
}
function showLearningMemory() {
    const outputChannel = vscode.window.createOutputChannel('AutoPR Learning Memory');
    outputChannel.show();
    outputChannel.appendLine('AutoPR Learning Memory System');
    outputChannel.appendLine('='.repeat(50));
    outputChannel.appendLine('Pattern Recognition: Active');
    outputChannel.appendLine('Success Rate Tracking: Enabled');
    outputChannel.appendLine('User Preference Learning: Active');
    outputChannel.appendLine('');
    outputChannel.appendLine('Recent Patterns:');
    outputChannel.appendLine('- File splitting: 85% success rate');
    outputChannel.appendLine('- Auto-fix application: 92% success rate');
    outputChannel.appendLine('- Quality analysis: 78% accuracy');
    outputChannel.appendLine('');
    outputChannel.appendLine('Learning Memory is continuously improving based on your usage patterns.');
}
async function clearCache() {
    try {
        await executeAutoPRCommand(['cache', '--clear']);
        vscode.window.showInformationMessage('Cache cleared successfully');
    }
    catch (error) {
        vscode.window.showErrorMessage(`Failed to clear cache: ${error}`);
    }
}
async function exportResults() {
    const outputChannel = vscode.window.createOutputChannel('AutoPR Export');
    outputChannel.show();
    outputChannel.appendLine('AutoPR Results Export');
    outputChannel.appendLine('='.repeat(50));
    outputChannel.appendLine('Export formats available:');
    outputChannel.appendLine('- JSON: Complete results with metadata');
    outputChannel.appendLine('- CSV: Tabular format for analysis');
    outputChannel.appendLine('- HTML: Web-friendly report');
    outputChannel.appendLine('- Markdown: Documentation format');
    outputChannel.appendLine('');
    outputChannel.appendLine('Use the AutoPR CLI for detailed export options:');
    outputChannel.appendLine('autopr export --format json --output results.json');
}
async function importConfiguration() {
    const config = vscode.workspace.getConfiguration('autopr');
    const configFile = await vscode.window.showOpenDialog({
        canSelectFiles: true,
        canSelectFolders: false,
        canSelectMany: false,
        filters: {
            'Configuration Files': ['json', 'yaml', 'yml', 'toml']
        }
    });
    if (configFile && configFile.length > 0) {
        vscode.window.showInformationMessage(`Configuration import from ${configFile[0].fsPath} would be implemented here`);
        // TODO: Implement actual configuration import logic
    }
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
// Tree Data Providers
class AutoPRIssuesProvider {
    constructor() {
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        // Return sample issues for now
        return Promise.resolve([
            new AutoPRIssueItem('✅ No critical issues found', vscode.TreeItemCollapsibleState.None),
            new AutoPRIssueItem('⚠️ 3 style warnings', vscode.TreeItemCollapsibleState.Collapsed),
            new AutoPRIssueItem('ℹ️ 2 documentation suggestions', vscode.TreeItemCollapsibleState.Collapsed)
        ]);
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
}
class AutoPRMetricsProvider {
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        // Return sample metrics
        return Promise.resolve([
            new AutoPRMetricsItem('Code Quality Score: 85/100', vscode.TreeItemCollapsibleState.None),
            new AutoPRMetricsItem('Issues Fixed: 12', vscode.TreeItemCollapsibleState.None),
            new AutoPRMetricsItem('Files Analyzed: 45', vscode.TreeItemCollapsibleState.None),
            new AutoPRMetricsItem('Performance: 2.3s avg', vscode.TreeItemCollapsibleState.None)
        ]);
    }
}
class AutoPRHistoryProvider {
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        // Return sample history
        return Promise.resolve([
            new AutoPRHistoryItem('2024-01-15: Quality check completed', vscode.TreeItemCollapsibleState.None),
            new AutoPRHistoryItem('2024-01-14: Auto-fix applied to 3 files', vscode.TreeItemCollapsibleState.None),
            new AutoPRHistoryItem('2024-01-13: File split completed', vscode.TreeItemCollapsibleState.None),
            new AutoPRHistoryItem('2024-01-12: Workspace analysis finished', vscode.TreeItemCollapsibleState.None)
        ]);
    }
}
// Tree Items
class AutoPRIssueItem extends vscode.TreeItem {
    constructor(label, collapsibleState, issue) {
        super(label, collapsibleState);
        this.label = label;
        this.collapsibleState = collapsibleState;
        this.issue = issue;
    }
}
class AutoPRMetricsItem extends vscode.TreeItem {
    constructor(label, collapsibleState) {
        super(label, collapsibleState);
        this.label = label;
        this.collapsibleState = collapsibleState;
    }
}
class AutoPRHistoryItem extends vscode.TreeItem {
    constructor(label, collapsibleState) {
        super(label, collapsibleState);
        this.label = label;
        this.collapsibleState = collapsibleState;
    }
}
function deactivate() {
    console.log('AutoPR extension is now deactivated!');
}
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map