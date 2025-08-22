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
const commandService_1 = require("./services/commandService");
const uiService_1 = require("./services/uiService");
const dataService_1 = require("./services/dataService");
const treeProviders_1 = require("./providers/treeProviders");
function activate(context) {
    console.log('AutoPR extension is now active!');
    // Set global extension context for data service
    global.extensionContext = context;
    // Initialize services
    const commandService = new commandService_1.CommandService();
    const uiService = new uiService_1.UIService();
    const dataService = dataService_1.DataService.getInstance();
    // Register diagnostic collection
    const diagnosticCollection = vscode.languages.createDiagnosticCollection('autopr');
    context.subscriptions.push(diagnosticCollection);
    // Register tree data providers
    const issuesProvider = new treeProviders_1.AutoPRIssuesProvider();
    vscode.window.registerTreeDataProvider('autoprIssues', issuesProvider);
    const metricsProvider = new treeProviders_1.AutoPRMetricsProvider();
    vscode.window.registerTreeDataProvider('autoprMetrics', metricsProvider);
    const historyProvider = new treeProviders_1.AutoPRHistoryProvider();
    vscode.window.registerTreeDataProvider('autoprHistory', historyProvider);
    // Register commands
    const commands = [
        // Quality Check Commands
        vscode.commands.registerCommand('autopr.qualityCheck', () => {
            commandService.runQualityCheck().then(() => {
                issuesProvider.refresh();
                metricsProvider.refresh();
            });
        }),
        vscode.commands.registerCommand('autopr.qualityCheckFile', () => {
            commandService.runQualityCheckFile().then(() => {
                issuesProvider.refresh();
                metricsProvider.refresh();
            });
        }),
        vscode.commands.registerCommand('autopr.qualityCheckWorkspace', () => {
            commandService.runQualityCheckWorkspace().then(() => {
                issuesProvider.refresh();
                metricsProvider.refresh();
            });
        }),
        // File Splitter Commands
        vscode.commands.registerCommand('autopr.fileSplit', () => {
            commandService.runFileSplit().then(() => {
                issuesProvider.refresh();
                metricsProvider.refresh();
            });
        }),
        // Auto-Fix Commands
        vscode.commands.registerCommand('autopr.autoFix', () => {
            commandService.runAutoFix().then(() => {
                issuesProvider.refresh();
                metricsProvider.refresh();
            });
        }),
        // Specialized Analysis Commands
        vscode.commands.registerCommand('autopr.performanceCheck', () => {
            commandService.runPerformanceCheck().then(() => {
                issuesProvider.refresh();
                metricsProvider.refresh();
            });
        }),
        vscode.commands.registerCommand('autopr.dependencyScan', () => {
            commandService.runDependencyScan().then(() => {
                issuesProvider.refresh();
                metricsProvider.refresh();
            });
        }),
        vscode.commands.registerCommand('autopr.securityScan', () => {
            commandService.runSecurityScan().then(() => {
                issuesProvider.refresh();
                metricsProvider.refresh();
            });
        }),
        vscode.commands.registerCommand('autopr.complexityAnalysis', () => {
            commandService.runComplexityAnalysis().then(() => {
                issuesProvider.refresh();
                metricsProvider.refresh();
            });
        }),
        vscode.commands.registerCommand('autopr.documentationCheck', () => {
            commandService.runDocumentationCheck().then(() => {
                issuesProvider.refresh();
                metricsProvider.refresh();
            });
        }),
        // Configuration Commands
        vscode.commands.registerCommand('autopr.setVolume', () => {
            uiService.showVolumeSettings();
        }),
        vscode.commands.registerCommand('autopr.toggleTool', () => {
            uiService.showToolToggle();
        }),
        vscode.commands.registerCommand('autopr.configure', () => {
            uiService.showConfiguration();
        }),
        // Utility Commands
        vscode.commands.registerCommand('autopr.clearCache', () => {
            commandService.clearCache();
        }),
        vscode.commands.registerCommand('autopr.exportResults', () => {
            uiService.exportResults();
        }),
        vscode.commands.registerCommand('autopr.importConfig', () => {
            uiService.importConfiguration();
        }),
        // UI Commands
        vscode.commands.registerCommand('autopr.showDashboard', () => {
            uiService.showDashboard();
        }),
        vscode.commands.registerCommand('autopr.learningMemory', () => {
            uiService.showLearningMemory();
        }),
        // Refresh commands for tree views
        vscode.commands.registerCommand('autopr.refreshIssues', () => {
            issuesProvider.refresh();
        }),
        vscode.commands.registerCommand('autopr.refreshMetrics', () => {
            metricsProvider.refresh();
        }),
        vscode.commands.registerCommand('autopr.refreshHistory', () => {
            historyProvider.refresh();
        })
    ];
    // Add all commands to subscriptions
    context.subscriptions.push(...commands);
    // Initialize with sample data for demonstration
    initializeSampleData(dataService);
    console.log('AutoPR extension activated with modular architecture');
}
exports.activate = activate;
function initializeSampleData(dataService) {
    // Add some sample issues for demonstration
    const sampleIssues = [
        {
            file: 'src/example.py',
            line: 15,
            column: 5,
            message: 'Unused import "os"',
            severity: 'warning',
            tool: 'ruff',
            code: 'F401',
            fixable: true,
            confidence: 0.95
        },
        {
            file: 'src/example.py',
            line: 25,
            column: 10,
            message: 'Variable "x" is assigned but never used',
            severity: 'warning',
            tool: 'ruff',
            code: 'F841',
            fixable: true,
            confidence: 0.98
        },
        {
            file: 'src/security.py',
            line: 42,
            column: 8,
            message: 'Possible SQL injection vulnerability',
            severity: 'error',
            tool: 'bandit',
            code: 'B608',
            fixable: false,
            confidence: 0.85
        },
        {
            file: 'src/complexity.py',
            line: 78,
            column: 12,
            message: 'Function has high cyclomatic complexity (15)',
            severity: 'info',
            tool: 'radon',
            code: 'C901',
            fixable: false,
            confidence: 0.75
        }
    ];
    dataService.setIssues(sampleIssues);
    // Add sample metrics
    const sampleMetrics = {
        code_quality_score: 85,
        issues_fixed: 12,
        files_analyzed: 45,
        performance_avg: 2300,
        complexity_score: 7.2,
        documentation_coverage: 78,
        security_score: 92
    };
    dataService.setMetrics(sampleMetrics);
    // Add sample performance history
    const sampleHistory = [
        {
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            operation: 'quality_check',
            duration: 2500,
            success: true,
            issues_found: 8,
            issues_fixed: 3
        },
        {
            timestamp: new Date(Date.now() - 7200000).toISOString(),
            operation: 'auto_fix',
            duration: 1800,
            success: true,
            issues_found: 5,
            issues_fixed: 5
        },
        {
            timestamp: new Date(Date.now() - 10800000).toISOString(),
            operation: 'file_split_analysis',
            duration: 3200,
            success: true,
            issues_found: 0,
            issues_fixed: 0
        }
    ];
    sampleHistory.forEach(record => {
        dataService.addPerformanceRecord(record);
    });
}
function deactivate() {
    console.log('AutoPR extension is now deactivated!');
}
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map