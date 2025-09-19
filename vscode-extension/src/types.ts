export interface AutoPRIssue {
    file: string;
    line: number;
    column: number;
    message: string;
    severity: 'error' | 'warning' | 'info';
    tool: string;
    code?: string;
    fixable?: boolean;
    confidence?: number;
}

export interface AutoPRResult {
    success: boolean;
    total_issues: number;
    issues_by_tool: Record<string, AutoPRIssue[]>;
    processing_time: number;
    components?: any[];
    metrics?: AutoPRMetrics;
    errors?: string[];
}

export interface AutoPRMetrics {
    code_quality_score: number;
    issues_fixed: number;
    files_analyzed: number;
    performance_avg: number;
    complexity_score: number;
    documentation_coverage: number;
    security_score: number;
}

export interface AutoPRConfig {
    enabled: boolean;
    qualityMode: string;
    autoFixEnabled: boolean;
    showNotifications: boolean;
    pythonPath: string;
    maxFileSize: number;
    volume: number;
    maxFixes: number;
    maxIssues: number;
    enableAIAgents: boolean;
    aiProvider: string;
    aiModel: string;
    verbose: boolean;
    configPath: string;
    fileSplitter: FileSplitterConfig;
    performanceOptimization: PerformanceConfig;
    tools: Record<string, ToolConfig>;
    autoFix: AutoFixConfig;
    dashboard: DashboardConfig;
}

export interface FileSplitterConfig {
    maxLinesPerFile: number;
    maxFunctionsPerFile: number;
    maxClassesPerFile: number;
    useAIAnalysis: boolean;
    confidenceThreshold: number;
    createBackup: boolean;
    validateSyntax: boolean;
    enableLearning: boolean;
}

export interface PerformanceConfig {
    enableCaching: boolean;
    enableParallelProcessing: boolean;
    enableMemoryOptimization: boolean;
    cacheTTL: number;
    maxParallelWorkers: number;
    memoryLimitMB: number;
}

export interface ToolConfig {
    enabled: boolean;
    config?: Record<string, any>;
}

export interface AutoFixConfig {
    enabled: boolean;
    fixTypes: string[];
    dryRun: boolean;
    maxFixes: number;
    confidenceThreshold: number;
}

export interface DashboardConfig {
    port: number;
    host: string;
    autoStart: boolean;
    theme: string;
}

export interface LearningMemoryData {
    patterns: PatternData[];
    successRates: Record<string, number>;
    userPreferences: Record<string, any>;
    performanceHistory: PerformanceHistory[];
}

export interface PatternData {
    id: string;
    type: string;
    success_rate: number;
    usage_count: number;
    last_used: string;
    confidence: number;
}

export interface PerformanceHistory {
    timestamp: string;
    operation: string;
    duration: number;
    success: boolean;
    issues_found: number;
    issues_fixed: number;
}

export interface TreeItemData {
    label: string;
    collapsibleState: number; // vscode.TreeItemCollapsibleState
    iconPath?: string;
    tooltip?: string;
    command?: any; // vscode.Command
    contextValue?: string;
}
