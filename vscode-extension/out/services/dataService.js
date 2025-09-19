"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DataService = void 0;
class DataService {
    constructor() {
        this.issues = [];
        this.metrics = null;
        this.performanceHistory = [];
        this.cache = new Map();
        this.learningMemory = this.initializeLearningMemory();
        this.loadStoredData();
    }
    static getInstance() {
        if (!DataService.instance) {
            DataService.instance = new DataService();
        }
        return DataService.instance;
    }
    initializeLearningMemory() {
        return {
            patterns: [
                {
                    id: 'file-split-success',
                    type: 'file_splitting',
                    success_rate: 0.85,
                    usage_count: 23,
                    last_used: new Date().toISOString(),
                    confidence: 0.92
                },
                {
                    id: 'auto-fix-success',
                    type: 'auto_fix',
                    success_rate: 0.92,
                    usage_count: 156,
                    last_used: new Date().toISOString(),
                    confidence: 0.88
                },
                {
                    id: 'quality-analysis',
                    type: 'quality_analysis',
                    success_rate: 0.78,
                    usage_count: 89,
                    last_used: new Date().toISOString(),
                    confidence: 0.85
                }
            ],
            successRates: {
                'file_splitting': 0.85,
                'auto_fix': 0.92,
                'quality_analysis': 0.78,
                'security_scan': 0.91,
                'performance_analysis': 0.83
            },
            userPreferences: {
                'preferred_mode': 'smart',
                'auto_fix_enabled': true,
                'notification_level': 'info',
                'dashboard_theme': 'dark'
            },
            performanceHistory: []
        };
    }
    loadStoredData() {
        // Load data from VS Code storage
        const context = this.getExtensionContext();
        if (context) {
            this.issues = context.globalState.get('autopr.issues', []);
            this.metrics = context.globalState.get('autopr.metrics', null);
            this.learningMemory = context.globalState.get('autopr.learningMemory', this.learningMemory);
            this.performanceHistory = context.globalState.get('autopr.performanceHistory', []);
        }
    }
    saveStoredData() {
        const context = this.getExtensionContext();
        if (context) {
            context.globalState.update('autopr.issues', this.issues);
            context.globalState.update('autopr.metrics', this.metrics);
            context.globalState.update('autopr.learningMemory', this.learningMemory);
            context.globalState.update('autopr.performanceHistory', this.performanceHistory);
        }
    }
    getExtensionContext() {
        // This would be set during extension activation
        return global.extensionContext || null;
    }
    // Issues management
    setIssues(issues) {
        this.issues = issues;
        this.saveStoredData();
    }
    getIssues() {
        return this.issues;
    }
    getIssuesBySeverity(severity) {
        return this.issues.filter(issue => issue.severity === severity);
    }
    getIssuesByTool(tool) {
        return this.issues.filter(issue => issue.tool === tool);
    }
    addIssue(issue) {
        this.issues.push(issue);
        this.saveStoredData();
    }
    clearIssues() {
        this.issues = [];
        this.saveStoredData();
    }
    // Metrics management
    setMetrics(metrics) {
        this.metrics = metrics;
        this.saveStoredData();
    }
    getMetrics() {
        return this.metrics;
    }
    updateMetrics(partialMetrics) {
        if (this.metrics) {
            this.metrics = { ...this.metrics, ...partialMetrics };
        }
        else {
            this.metrics = partialMetrics;
        }
        this.saveStoredData();
    }
    // Learning memory management
    getLearningMemory() {
        return this.learningMemory;
    }
    updatePatternSuccessRate(patternId, success) {
        const pattern = this.learningMemory.patterns.find(p => p.id === patternId);
        if (pattern) {
            pattern.usage_count++;
            pattern.last_used = new Date().toISOString();
            // Update success rate using exponential moving average
            const alpha = 0.1;
            pattern.success_rate = alpha * (success ? 1 : 0) + (1 - alpha) * pattern.success_rate;
        }
        this.saveStoredData();
    }
    getUserPreferences() {
        return this.learningMemory.userPreferences;
    }
    updateUserPreference(key, value) {
        this.learningMemory.userPreferences[key] = value;
        this.saveStoredData();
    }
    // Performance history
    addPerformanceRecord(record) {
        this.performanceHistory.push(record);
        // Keep only last 100 records
        if (this.performanceHistory.length > 100) {
            this.performanceHistory = this.performanceHistory.slice(-100);
        }
        this.saveStoredData();
    }
    getPerformanceHistory() {
        return this.performanceHistory;
    }
    getAveragePerformance(operation) {
        const records = this.performanceHistory.filter(r => r.operation === operation);
        if (records.length === 0)
            return 0;
        const total = records.reduce((sum, record) => sum + record.duration, 0);
        return total / records.length;
    }
    // Cache management
    getCachedData(key) {
        return this.cache.get(key);
    }
    setCachedData(key, value, ttl = 3600) {
        this.cache.set(key, {
            value,
            expires: Date.now() + ttl * 1000
        });
    }
    clearCache() {
        this.cache.clear();
    }
    isCacheValid(key) {
        const cached = this.cache.get(key);
        if (!cached)
            return false;
        return Date.now() < cached.expires;
    }
    // Utility methods
    getIssueCounts() {
        return {
            errors: this.getIssuesBySeverity('error').length,
            warnings: this.getIssuesBySeverity('warning').length,
            info: this.getIssuesBySeverity('info').length
        };
    }
    getToolIssueCounts() {
        const counts = {};
        this.issues.forEach(issue => {
            counts[issue.tool] = (counts[issue.tool] || 0) + 1;
        });
        return counts;
    }
    getRecentActivity(limit = 10) {
        return this.performanceHistory
            .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
            .slice(0, limit);
    }
    initializeWorkspace(workspacePath) {
        // Initialize workspace-specific data
        this.cache.set('workspace_path', workspacePath);
        this.cache.set('initialized_at', new Date().toISOString());
        // Set workspace-specific learning memory
        this.learningMemory.userPreferences['workspace_path'] = workspacePath;
        this.learningMemory.userPreferences['last_initialized'] = new Date().toISOString();
        this.saveStoredData();
    }
}
exports.DataService = DataService;
//# sourceMappingURL=dataService.js.map