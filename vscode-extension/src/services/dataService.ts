import * as vscode from "vscode";
import {
  AutoPRIssue,
  AutoPRResult,
  AutoPRMetrics,
  LearningMemoryData,
  PerformanceHistory,
} from "../types";

export class DataService {
  private static instance: DataService;
  private issues: AutoPRIssue[] = [];
  private metrics: AutoPRMetrics | null = null;
  private learningMemory: LearningMemoryData;
  private performanceHistory: PerformanceHistory[] = [];
  private cache: Map<string, any> = new Map();

  private constructor() {
    this.learningMemory = this.initializeLearningMemory();
    this.loadStoredData();
  }

  public static getInstance(): DataService {
    if (!DataService.instance) {
      DataService.instance = new DataService();
    }
    return DataService.instance;
  }

  private initializeLearningMemory(): LearningMemoryData {
    return {
      patterns: [
        {
          id: "file-split-success",
          type: "file_splitting",
          success_rate: 0.85,
          usage_count: 23,
          last_used: new Date().toISOString(),
          confidence: 0.92,
        },
        {
          id: "auto-fix-success",
          type: "auto_fix",
          success_rate: 0.92,
          usage_count: 156,
          last_used: new Date().toISOString(),
          confidence: 0.88,
        },
        {
          id: "quality-analysis",
          type: "quality_analysis",
          success_rate: 0.78,
          usage_count: 89,
          last_used: new Date().toISOString(),
          confidence: 0.85,
        },
      ],
      successRates: {
        file_splitting: 0.85,
        auto_fix: 0.92,
        quality_analysis: 0.78,
        security_scan: 0.91,
        performance_analysis: 0.83,
      },
      userPreferences: {
        preferred_mode: "smart",
        auto_fix_enabled: true,
        notification_level: "info",
        dashboard_theme: "dark",
      },
      performanceHistory: [],
    };
  }

  private loadStoredData(): void {
    // Load data from VS Code storage
    const context = this.getExtensionContext();
    if (context) {
      this.issues = context.globalState.get("autopr.issues", []);
      this.metrics = context.globalState.get("autopr.metrics", null);
      this.learningMemory = context.globalState.get(
        "autopr.learningMemory",
        this.learningMemory,
      );
      this.performanceHistory = context.globalState.get(
        "autopr.performanceHistory",
        [],
      );
    }
  }

  private saveStoredData(): void {
    const context = this.getExtensionContext();
    if (context) {
      context.globalState.update("autopr.issues", this.issues);
      context.globalState.update("autopr.metrics", this.metrics);
      context.globalState.update("autopr.learningMemory", this.learningMemory);
      context.globalState.update(
        "autopr.performanceHistory",
        this.performanceHistory,
      );
    }
  }

  private getExtensionContext(): vscode.ExtensionContext | null {
    // This would be set during extension activation
    return (global as any).extensionContext || null;
  }

  // Issues management
  public setIssues(issues: AutoPRIssue[]): void {
    this.issues = issues;
    this.saveStoredData();
  }

  public getIssues(): AutoPRIssue[] {
    return this.issues;
  }

  public getIssuesBySeverity(
    severity: "error" | "warning" | "info",
  ): AutoPRIssue[] {
    return this.issues.filter((issue) => issue.severity === severity);
  }

  public getIssuesByTool(tool: string): AutoPRIssue[] {
    return this.issues.filter((issue) => issue.tool === tool);
  }

  public addIssue(issue: AutoPRIssue): void {
    this.issues.push(issue);
    this.saveStoredData();
  }

  public clearIssues(): void {
    this.issues = [];
    this.saveStoredData();
  }

  // Metrics management
  public setMetrics(metrics: AutoPRMetrics): void {
    this.metrics = metrics;
    this.saveStoredData();
  }

  public getMetrics(): AutoPRMetrics | null {
    return this.metrics;
  }

  public updateMetrics(partialMetrics: Partial<AutoPRMetrics>): void {
    if (this.metrics) {
      this.metrics = { ...this.metrics, ...partialMetrics };
    } else {
      this.metrics = partialMetrics as AutoPRMetrics;
    }
    this.saveStoredData();
  }

  // Learning memory management
  public getLearningMemory(): LearningMemoryData {
    return this.learningMemory;
  }

  public updatePatternSuccessRate(patternId: string, success: boolean): void {
    const pattern = this.learningMemory.patterns.find(
      (p) => p.id === patternId,
    );
    if (pattern) {
      pattern.usage_count++;
      pattern.last_used = new Date().toISOString();

      // Update success rate using exponential moving average
      const alpha = 0.1;
      pattern.success_rate =
        alpha * (success ? 1 : 0) + (1 - alpha) * pattern.success_rate;
    }
    this.saveStoredData();
  }

  public getUserPreferences(): Record<string, any> {
    return this.learningMemory.userPreferences;
  }

  public updateUserPreference(key: string, value: any): void {
    this.learningMemory.userPreferences[key] = value;
    this.saveStoredData();
  }

  // Performance history
  public addPerformanceRecord(record: PerformanceHistory): void {
    this.performanceHistory.push(record);
    // Keep only last 100 records
    if (this.performanceHistory.length > 100) {
      this.performanceHistory = this.performanceHistory.slice(-100);
    }
    this.saveStoredData();
  }

  public getPerformanceHistory(): PerformanceHistory[] {
    return this.performanceHistory;
  }

  public getAveragePerformance(operation: string): number {
    const records = this.performanceHistory.filter(
      (r) => r.operation === operation,
    );
    if (records.length === 0) return 0;

    const total = records.reduce((sum, record) => sum + record.duration, 0);
    return total / records.length;
  }

  // Cache management
  public getCachedData(key: string): any {
    return this.cache.get(key);
  }

  public setCachedData(key: string, value: any, ttl: number = 3600): void {
    this.cache.set(key, {
      value,
      expires: Date.now() + ttl * 1000,
    });
  }

  public clearCache(): void {
    this.cache.clear();
  }

  public isCacheValid(key: string): boolean {
    const cached = this.cache.get(key);
    if (!cached) return false;
    return Date.now() < cached.expires;
  }

  // Utility methods
  public getIssueCounts(): { errors: number; warnings: number; info: number } {
    return {
      errors: this.getIssuesBySeverity("error").length,
      warnings: this.getIssuesBySeverity("warning").length,
      info: this.getIssuesBySeverity("info").length,
    };
  }

  public getToolIssueCounts(): Record<string, number> {
    const counts: Record<string, number> = {};
    this.issues.forEach((issue) => {
      counts[issue.tool] = (counts[issue.tool] || 0) + 1;
    });
    return counts;
  }

  public getRecentActivity(limit: number = 10): PerformanceHistory[] {
    return this.performanceHistory
      .sort(
        (a, b) =>
          new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
      )
      .slice(0, limit);
  }

  public initializeWorkspace(workspacePath: string): void {
    // Initialize workspace-specific data
    this.cache.set("workspace_path", workspacePath);
    this.cache.set("initialized_at", new Date().toISOString());

    // Set workspace-specific learning memory
    this.learningMemory.userPreferences["workspace_path"] = workspacePath;
    this.learningMemory.userPreferences["last_initialized"] =
      new Date().toISOString();

    this.saveStoredData();
  }
}
