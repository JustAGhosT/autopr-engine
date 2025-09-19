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
exports.AutoPRHistoryProvider = exports.AutoPRMetricsProvider = exports.AutoPRIssuesProvider = exports.AutoPRHistoryItem = exports.AutoPRMetricsItem = exports.AutoPRIssueItem = void 0;
const vscode = __importStar(require("vscode"));
const dataService_1 = require("../services/dataService");
// Tree Items
class AutoPRIssueItem extends vscode.TreeItem {
    constructor(label, collapsibleState, issue) {
        super(label, collapsibleState);
        this.label = label;
        this.collapsibleState = collapsibleState;
        this.issue = issue;
        if (issue) {
            this.tooltip = `${issue.file}:${issue.line}:${issue.column} - ${issue.message}`;
            this.description = `${issue.tool} - ${issue.severity}`;
            // Set icon based on severity
            switch (issue.severity) {
                case 'error':
                    this.iconPath = new vscode.ThemeIcon('error');
                    break;
                case 'warning':
                    this.iconPath = new vscode.ThemeIcon('warning');
                    break;
                case 'info':
                    this.iconPath = new vscode.ThemeIcon('info');
                    break;
            }
        }
    }
}
exports.AutoPRIssueItem = AutoPRIssueItem;
class AutoPRMetricsItem extends vscode.TreeItem {
    constructor(label, collapsibleState, value, unit) {
        super(label, collapsibleState);
        this.label = label;
        this.collapsibleState = collapsibleState;
        this.value = value;
        this.unit = unit;
        if (value !== undefined) {
            this.description = unit ? `${value}${unit}` : value.toString();
        }
    }
}
exports.AutoPRMetricsItem = AutoPRMetricsItem;
class AutoPRHistoryItem extends vscode.TreeItem {
    constructor(label, collapsibleState, record) {
        super(label, collapsibleState);
        this.label = label;
        this.collapsibleState = collapsibleState;
        this.record = record;
        if (record) {
            this.tooltip = `Duration: ${record.duration}ms, Issues: ${record.issues_found}, Fixed: ${record.issues_fixed}`;
            this.description = record.success ? '✅ Success' : '❌ Failed';
            this.iconPath = new vscode.ThemeIcon(record.success ? 'check' : 'error');
        }
    }
}
exports.AutoPRHistoryItem = AutoPRHistoryItem;
// Tree Data Providers
class AutoPRIssuesProvider {
    constructor() {
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this.dataService = dataService_1.DataService.getInstance();
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (element) {
            // Return child issues for grouped items
            return this.getChildIssues(element);
        }
        else {
            // Return root level items
            return this.getRootIssues();
        }
    }
    async getRootIssues() {
        const issues = this.dataService.getIssues();
        const counts = this.dataService.getIssueCounts();
        const toolCounts = this.dataService.getToolIssueCounts();
        const items = [];
        // Add summary items
        if (counts.errors > 0) {
            items.push(new AutoPRIssueItem(`❌ ${counts.errors} Errors`, vscode.TreeItemCollapsibleState.Collapsed));
        }
        if (counts.warnings > 0) {
            items.push(new AutoPRIssueItem(`⚠️ ${counts.warnings} Warnings`, vscode.TreeItemCollapsibleState.Collapsed));
        }
        if (counts.info > 0) {
            items.push(new AutoPRIssueItem(`ℹ️ ${counts.info} Info`, vscode.TreeItemCollapsibleState.Collapsed));
        }
        // Add tool-specific groups
        Object.entries(toolCounts).forEach(([tool, count]) => {
            if (count > 0) {
                items.push(new AutoPRIssueItem(`🔧 ${tool}: ${count} issues`, vscode.TreeItemCollapsibleState.Collapsed));
            }
        });
        if (items.length === 0) {
            items.push(new AutoPRIssueItem('✅ No issues found', vscode.TreeItemCollapsibleState.None));
        }
        return items;
    }
    async getChildIssues(element) {
        const issues = this.dataService.getIssues();
        const label = element.label;
        if (label.includes('Errors')) {
            return this.dataService.getIssuesBySeverity('error').map(issue => new AutoPRIssueItem(`${issue.file}:${issue.line} - ${issue.message}`, vscode.TreeItemCollapsibleState.None, issue));
        }
        else if (label.includes('Warnings')) {
            return this.dataService.getIssuesBySeverity('warning').map(issue => new AutoPRIssueItem(`${issue.file}:${issue.line} - ${issue.message}`, vscode.TreeItemCollapsibleState.None, issue));
        }
        else if (label.includes('Info')) {
            return this.dataService.getIssuesBySeverity('info').map(issue => new AutoPRIssueItem(`${issue.file}:${issue.line} - ${issue.message}`, vscode.TreeItemCollapsibleState.None, issue));
        }
        else if (label.includes(':')) {
            // Tool-specific issues
            const tool = label.split(':')[0].replace('🔧 ', '');
            return this.dataService.getIssuesByTool(tool).map(issue => new AutoPRIssueItem(`${issue.file}:${issue.line} - ${issue.message}`, vscode.TreeItemCollapsibleState.None, issue));
        }
        return [];
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
}
exports.AutoPRIssuesProvider = AutoPRIssuesProvider;
class AutoPRMetricsProvider {
    constructor() {
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this.dataService = dataService_1.DataService.getInstance();
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        const metrics = this.dataService.getMetrics();
        const performanceHistory = this.dataService.getPerformanceHistory();
        if (!metrics) {
            return Promise.resolve([
                new AutoPRMetricsItem('No metrics available', vscode.TreeItemCollapsibleState.None)
            ]);
        }
        const items = [
            new AutoPRMetricsItem('Code Quality Score', vscode.TreeItemCollapsibleState.None, metrics.code_quality_score, '/100'),
            new AutoPRMetricsItem('Issues Fixed', vscode.TreeItemCollapsibleState.None, metrics.issues_fixed),
            new AutoPRMetricsItem('Files Analyzed', vscode.TreeItemCollapsibleState.None, metrics.files_analyzed),
            new AutoPRMetricsItem('Average Performance', vscode.TreeItemCollapsibleState.None, metrics.performance_avg, 'ms'),
            new AutoPRMetricsItem('Complexity Score', vscode.TreeItemCollapsibleState.None, metrics.complexity_score, '/10'),
            new AutoPRMetricsItem('Documentation Coverage', vscode.TreeItemCollapsibleState.None, metrics.documentation_coverage, '%'),
            new AutoPRMetricsItem('Security Score', vscode.TreeItemCollapsibleState.None, metrics.security_score, '/100')
        ];
        // Add performance averages for different operations
        const operations = ['quality_check', 'auto_fix', 'file_split_analysis', 'security_scan'];
        operations.forEach(operation => {
            const avg = this.dataService.getAveragePerformance(operation);
            if (avg > 0) {
                items.push(new AutoPRMetricsItem(`${operation.replace('_', ' ').toUpperCase()} Avg`, vscode.TreeItemCollapsibleState.None, Math.round(avg), 'ms'));
            }
        });
        return Promise.resolve(items);
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
}
exports.AutoPRMetricsProvider = AutoPRMetricsProvider;
class AutoPRHistoryProvider {
    constructor() {
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this.dataService = dataService_1.DataService.getInstance();
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        const recentActivity = this.dataService.getRecentActivity(20);
        const learningMemory = this.dataService.getLearningMemory();
        if (recentActivity.length === 0) {
            return Promise.resolve([
                new AutoPRHistoryItem('No recent activity', vscode.TreeItemCollapsibleState.None)
            ]);
        }
        const items = [];
        // Add recent activity
        recentActivity.forEach(record => {
            const date = new Date(record.timestamp).toLocaleDateString();
            const time = new Date(record.timestamp).toLocaleTimeString();
            const label = `${date} ${time}: ${record.operation.replace('_', ' ')}`;
            items.push(new AutoPRHistoryItem(label, vscode.TreeItemCollapsibleState.None, record));
        });
        // Add learning memory patterns
        learningMemory.patterns.forEach(pattern => {
            const date = new Date(pattern.last_used).toLocaleDateString();
            const successRate = Math.round(pattern.success_rate * 100);
            const label = `${date}: ${pattern.type.replace('_', ' ')} (${successRate}% success)`;
            items.push(new AutoPRHistoryItem(label, vscode.TreeItemCollapsibleState.None));
        });
        return Promise.resolve(items);
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
}
exports.AutoPRHistoryProvider = AutoPRHistoryProvider;
//# sourceMappingURL=treeProviders.js.map