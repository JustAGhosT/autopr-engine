import * as vscode from 'vscode';
import { spawn } from 'child_process';
import * as path from 'path';
import { AutoPRResult, AutoPRMetrics, PerformanceHistory } from '../types';
import { DataService } from './dataService';

export class CommandService {
    private dataService: DataService;

    constructor() {
        this.dataService = DataService.getInstance();
    }

    // Quality Check Commands
    public async runQualityCheck(): Promise<void> {
        const config = vscode.workspace.getConfiguration('autopr');
        const mode = config.get<string>('qualityMode', 'fast');
        
        try {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active file to check');
                return;
            }

            const filePath = editor.document.fileName;
            const startTime = Date.now();
            
            const result = await this.executeAutoPRCommand(['check', '--mode', mode, '--files', filePath]);
            
            if (result.success) {
                this.processQualityResults(result, 'quality_check', startTime);
                this.displayQualityResults(result);
            } else {
                vscode.window.showErrorMessage('Quality check failed');
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Quality check error: ${error}`);
        }
    }

    public async runQualityCheckFile(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active file to check');
            return;
        }

        const filePath = editor.document.fileName;
        const config = vscode.workspace.getConfiguration('autopr');
        const mode = config.get<string>('qualityMode', 'fast');

        try {
            const startTime = Date.now();
            const result = await this.executeAutoPRCommand(['check', '--mode', mode, '--files', filePath]);
            
            if (result.success) {
                this.processQualityResults(result, 'file_quality_check', startTime);
                this.displayQualityResults(result);
            } else {
                vscode.window.showErrorMessage('File quality check failed');
            }
        } catch (error) {
            vscode.window.showErrorMessage(`File quality check error: ${error}`);
        }
    }

    public async runQualityCheckWorkspace(): Promise<void> {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            vscode.window.showErrorMessage('No workspace folder found');
            return;
        }

        const config = vscode.workspace.getConfiguration('autopr');
        const mode = config.get<string>('qualityMode', 'fast');

        try {
            const startTime = Date.now();
            const result = await this.executeAutoPRCommand(['check', '--mode', mode, '--directory', workspaceFolders[0].uri.fsPath]);
            
            if (result.success) {
                this.processQualityResults(result, 'workspace_quality_check', startTime);
                this.displayQualityResults(result);
            } else {
                vscode.window.showErrorMessage('Workspace quality check failed');
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Workspace quality check error: ${error}`);
        }
    }

    // File Splitter Commands
    public async runFileSplit(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active file to split');
            return;
        }

        const filePath = editor.document.fileName;
        const config = vscode.workspace.getConfiguration('autopr');
        const splitConfig = config.get<any>('fileSplitter', {});
        
        const maxLines = await vscode.window.showInputBox({
            prompt: 'Maximum lines per component',
            value: splitConfig.maxLinesPerFile?.toString() || '100',
            validateInput: (value: string) => {
                const num = parseInt(value);
                return isNaN(num) || num <= 0 ? 'Please enter a positive number' : null;
            }
        });

        if (!maxLines) return;

        try {
            const startTime = Date.now();
            const result = await this.executeAutoPRCommand(['split', filePath, '--max-lines', maxLines, '--dry-run']);
            
            if (result.success) {
                this.processQualityResults(result, 'file_split_analysis', startTime);
                vscode.window.showInformationMessage(`File split analysis complete. Would create ${result.components?.length || 0} components.`);
                
                const proceed = await vscode.window.showQuickPick(['Yes', 'No'], {
                    placeHolder: 'Proceed with actual file split?'
                });

                if (proceed === 'Yes') {
                    const outputDir = await vscode.window.showInputBox({
                        prompt: 'Output directory for split files',
                        value: path.dirname(filePath) + '/split'
                    });

                    if (outputDir) {
                        const splitStartTime = Date.now();
                        const splitResult = await this.executeAutoPRCommand(['split', filePath, '--max-lines', maxLines, '--output-dir', outputDir]);
                        if (splitResult.success) {
                            this.processQualityResults(splitResult, 'file_split_execution', splitStartTime);
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

    // Auto-Fix Commands
    public async runAutoFix(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active file to fix');
            return;
        }

        const filePath = editor.document.fileName;
        const config = vscode.workspace.getConfiguration('autopr');
        const mode = config.get<string>('qualityMode', 'fast');

        try {
            const startTime = Date.now();
            const result = await this.executeAutoPRCommand(['check', '--mode', mode, '--files', filePath, '--auto-fix']);
            
            if (result.success) {
                this.processQualityResults(result, 'auto_fix', startTime);
                vscode.window.showInformationMessage('Auto-fix completed successfully!');
                await editor.document.save();
            } else {
                vscode.window.showErrorMessage('Auto-fix failed');
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Auto-fix error: ${error}`);
        }
    }

    // Specialized Analysis Commands
    public async runPerformanceCheck(): Promise<void> {
        try {
            const startTime = Date.now();
            const result = await this.executeAutoPRCommand(['check', '--mode', 'comprehensive', '--tools', 'performance_analyzer']);
            if (result.success) {
                this.processQualityResults(result, 'performance_analysis', startTime);
                vscode.window.showInformationMessage('Performance analysis completed');
                this.displayQualityResults(result);
            } else {
                vscode.window.showErrorMessage('Performance analysis failed');
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Performance analysis error: ${error}`);
        }
    }

    public async runDependencyScan(): Promise<void> {
        try {
            const startTime = Date.now();
            const result = await this.executeAutoPRCommand(['check', '--mode', 'comprehensive', '--tools', 'dependency_scanner']);
            if (result.success) {
                this.processQualityResults(result, 'dependency_scan', startTime);
                vscode.window.showInformationMessage('Dependency scan completed');
                this.displayQualityResults(result);
            } else {
                vscode.window.showErrorMessage('Dependency scan failed');
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Dependency scan error: ${error}`);
        }
    }

    public async runSecurityScan(): Promise<void> {
        try {
            const startTime = Date.now();
            const result = await this.executeAutoPRCommand(['check', '--mode', 'comprehensive', '--tools', 'bandit,codeql']);
            if (result.success) {
                this.processQualityResults(result, 'security_scan', startTime);
                vscode.window.showInformationMessage('Security scan completed');
                this.displayQualityResults(result);
            } else {
                vscode.window.showErrorMessage('Security scan failed');
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Security scan error: ${error}`);
        }
    }

    public async runComplexityAnalysis(): Promise<void> {
        try {
            const startTime = Date.now();
            const result = await this.executeAutoPRCommand(['check', '--mode', 'comprehensive', '--tools', 'radon']);
            if (result.success) {
                this.processQualityResults(result, 'complexity_analysis', startTime);
                vscode.window.showInformationMessage('Complexity analysis completed');
                this.displayQualityResults(result);
            } else {
                vscode.window.showErrorMessage('Complexity analysis failed');
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Complexity analysis error: ${error}`);
        }
    }

    public async runDocumentationCheck(): Promise<void> {
        try {
            const startTime = Date.now();
            const result = await this.executeAutoPRCommand(['check', '--mode', 'comprehensive', '--tools', 'interrogate']);
            if (result.success) {
                this.processQualityResults(result, 'documentation_check', startTime);
                vscode.window.showInformationMessage('Documentation check completed');
                this.displayQualityResults(result);
            } else {
                vscode.window.showErrorMessage('Documentation check failed');
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Documentation check error: ${error}`);
        }
    }

    // Utility Commands
    public async clearCache(): Promise<void> {
        try {
            await this.executeAutoPRCommand(['cache', '--clear']);
            this.dataService.clearCache();
            vscode.window.showInformationMessage('Cache cleared successfully');
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to clear cache: ${error}`);
        }
    }

    // Configuration Commands
    public async setVolumeLevel(): Promise<void> {
        const config = vscode.workspace.getConfiguration('autopr');
        const currentVolume = config.get<number>('volume', 500);
        
        const volume = await vscode.window.showInputBox({
            prompt: 'Set volume level (0-1000)',
            value: currentVolume.toString(),
            validateInput: (value: string) => {
                const num = parseInt(value);
                return isNaN(num) || num < 0 || num > 1000 ? 'Please enter a number between 0 and 1000' : null;
            }
        });

        if (volume) {
            await config.update('volume', parseInt(volume), vscode.ConfigurationTarget.Workspace);
            this.dataService.updateUserPreference('volume_level', parseInt(volume));
            vscode.window.showInformationMessage(`Volume level set to ${volume}`);
        }
    }

    public async toggleTool(): Promise<void> {
        const config = vscode.workspace.getConfiguration('autopr');
        const tools = config.get<any>('tools', {});
        
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

    // Private helper methods
    private async executeAutoPRCommand(args: string[]): Promise<AutoPRResult> {
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

    private processQualityResults(result: AutoPRResult, operation: string, startTime: number): void {
        const duration = Date.now() - startTime;
        
        // Update issues
        const allIssues: any[] = [];
        if (result.issues_by_tool) {
            Object.entries(result.issues_by_tool).forEach(([tool, issues]) => {
                allIssues.push(...issues);
            });
        }
        this.dataService.setIssues(allIssues);

        // Update metrics
        if (result.metrics) {
            this.dataService.setMetrics(result.metrics);
        }

        // Record performance
        const performanceRecord: PerformanceHistory = {
            timestamp: new Date().toISOString(),
            operation,
            duration,
            success: result.success,
            issues_found: result.total_issues,
            issues_fixed: result.metrics?.issues_fixed || 0
        };
        this.dataService.addPerformanceRecord(performanceRecord);

        // Update learning memory
        this.dataService.updatePatternSuccessRate(`${operation}-success`, result.success);
    }

    private displayQualityResults(result: AutoPRResult): void {
        const config = vscode.workspace.getConfiguration('autopr');
        const showNotifications = config.get<boolean>('showNotifications', true);

        if (showNotifications) {
            const message = `Quality check completed: ${result.total_issues} issues found in ${result.processing_time.toFixed(2)}s`;
            vscode.window.showInformationMessage(message);
        }

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



    public async runQuickFix(): Promise<void> {
        try {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active file to fix');
                return;
            }

            const filePath = editor.document.fileName;
            const startTime = Date.now();
            
            const result = await this.executeAutoPRCommand(['fix', '--quick', '--files', filePath]);
            
            if (result.success) {
                this.processQualityResults(result, 'quick_fix', startTime);
                vscode.window.showInformationMessage('Quick fixes applied successfully');
            } else {
                vscode.window.showErrorMessage('Quick fix failed');
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Quick fix error: ${error}`);
        }
    }

    public async runWorkspaceAnalysis(): Promise<void> {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            vscode.window.showErrorMessage('No workspace folder found');
            return;
        }

        try {
            const startTime = Date.now();
            const result = await this.executeAutoPRCommand(['analyze', '--workspace', workspaceFolders[0].uri.fsPath]);
            
            if (result.success) {
                this.processQualityResults(result, 'workspace_analysis', startTime);
                vscode.window.showInformationMessage('Workspace analysis completed');
            } else {
                vscode.window.showErrorMessage('Workspace analysis failed');
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Workspace analysis error: ${error}`);
        }
    }
}
