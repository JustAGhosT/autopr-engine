import * as vscode from "vscode";
import { AutoPRIssue, AutoPRMetrics, PerformanceHistory } from "../types";
import { DataService } from "../services/dataService";

// Tree Items
export class AutoPRIssueItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState,
    public readonly issue?: AutoPRIssue,
  ) {
    super(label, collapsibleState);

    if (issue) {
      this.tooltip = `${issue.file}:${issue.line}:${issue.column} - ${issue.message}`;
      this.description = `${issue.tool} - ${issue.severity}`;

      // Set icon based on severity
      switch (issue.severity) {
        case "error":
          this.iconPath = new vscode.ThemeIcon("error");
          break;
        case "warning":
          this.iconPath = new vscode.ThemeIcon("warning");
          break;
        case "info":
          this.iconPath = new vscode.ThemeIcon("info");
          break;
      }
    }
  }
}

export class AutoPRMetricsItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState,
    public readonly value?: number,
    public readonly unit?: string,
  ) {
    super(label, collapsibleState);

    if (value !== undefined) {
      this.description = unit ? `${value}${unit}` : value.toString();
    }
  }
}

export class AutoPRHistoryItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState,
    public readonly record?: PerformanceHistory,
  ) {
    super(label, collapsibleState);

    if (record) {
      this.tooltip = `Duration: ${record.duration}ms, Issues: ${record.issues_found}, Fixed: ${record.issues_fixed}`;
      this.description = record.success ? "✅ Success" : "❌ Failed";
      this.iconPath = new vscode.ThemeIcon(record.success ? "check" : "error");
    }
  }
}

// Tree Data Providers
export class AutoPRIssuesProvider
  implements vscode.TreeDataProvider<AutoPRIssueItem>
{
  private _onDidChangeTreeData: vscode.EventEmitter<
    AutoPRIssueItem | undefined | null | void
  > = new vscode.EventEmitter<AutoPRIssueItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<
    AutoPRIssueItem | undefined | null | void
  > = this._onDidChangeTreeData.event;

  private dataService: DataService;

  constructor() {
    this.dataService = DataService.getInstance();
  }

  getTreeItem(element: AutoPRIssueItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: AutoPRIssueItem): Promise<AutoPRIssueItem[]> {
    if (element) {
      // Return child issues for grouped items
      return this.getChildIssues(element);
    } else {
      // Return root level items
      return this.getRootIssues();
    }
  }

  private async getRootIssues(): Promise<AutoPRIssueItem[]> {
    const issues = this.dataService.getIssues();
    const counts = this.dataService.getIssueCounts();
    const toolCounts = this.dataService.getToolIssueCounts();

    const items: AutoPRIssueItem[] = [];

    // Add summary items
    if (counts.errors > 0) {
      items.push(
        new AutoPRIssueItem(
          `❌ ${counts.errors} Errors`,
          vscode.TreeItemCollapsibleState.Collapsed,
        ),
      );
    }

    if (counts.warnings > 0) {
      items.push(
        new AutoPRIssueItem(
          `⚠️ ${counts.warnings} Warnings`,
          vscode.TreeItemCollapsibleState.Collapsed,
        ),
      );
    }

    if (counts.info > 0) {
      items.push(
        new AutoPRIssueItem(
          `ℹ️ ${counts.info} Info`,
          vscode.TreeItemCollapsibleState.Collapsed,
        ),
      );
    }

    // Add tool-specific groups
    Object.entries(toolCounts).forEach(([tool, count]) => {
      if (count > 0) {
        items.push(
          new AutoPRIssueItem(
            `🔧 ${tool}: ${count} issues`,
            vscode.TreeItemCollapsibleState.Collapsed,
          ),
        );
      }
    });

    if (items.length === 0) {
      items.push(
        new AutoPRIssueItem(
          "✅ No issues found",
          vscode.TreeItemCollapsibleState.None,
        ),
      );
    }

    return items;
  }

  private async getChildIssues(
    element: AutoPRIssueItem,
  ): Promise<AutoPRIssueItem[]> {
    const issues = this.dataService.getIssues();
    const label = element.label;

    if (label.includes("Errors")) {
      return this.dataService
        .getIssuesBySeverity("error")
        .map(
          (issue) =>
            new AutoPRIssueItem(
              `${issue.file}:${issue.line} - ${issue.message}`,
              vscode.TreeItemCollapsibleState.None,
              issue,
            ),
        );
    } else if (label.includes("Warnings")) {
      return this.dataService
        .getIssuesBySeverity("warning")
        .map(
          (issue) =>
            new AutoPRIssueItem(
              `${issue.file}:${issue.line} - ${issue.message}`,
              vscode.TreeItemCollapsibleState.None,
              issue,
            ),
        );
    } else if (label.includes("Info")) {
      return this.dataService
        .getIssuesBySeverity("info")
        .map(
          (issue) =>
            new AutoPRIssueItem(
              `${issue.file}:${issue.line} - ${issue.message}`,
              vscode.TreeItemCollapsibleState.None,
              issue,
            ),
        );
    } else if (label.includes(":")) {
      // Tool-specific issues
      const tool = label.split(":")[0].replace("🔧 ", "");
      return this.dataService
        .getIssuesByTool(tool)
        .map(
          (issue) =>
            new AutoPRIssueItem(
              `${issue.file}:${issue.line} - ${issue.message}`,
              vscode.TreeItemCollapsibleState.None,
              issue,
            ),
        );
    }

    return [];
  }

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }
}

export class AutoPRMetricsProvider
  implements vscode.TreeDataProvider<AutoPRMetricsItem>
{
  private _onDidChangeTreeData: vscode.EventEmitter<
    AutoPRMetricsItem | undefined | null | void
  > = new vscode.EventEmitter<AutoPRMetricsItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<
    AutoPRMetricsItem | undefined | null | void
  > = this._onDidChangeTreeData.event;

  private dataService: DataService;

  constructor() {
    this.dataService = DataService.getInstance();
  }

  getTreeItem(element: AutoPRMetricsItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: AutoPRMetricsItem): Promise<AutoPRMetricsItem[]> {
    const metrics = this.dataService.getMetrics();
    const performanceHistory = this.dataService.getPerformanceHistory();

    if (!metrics) {
      return Promise.resolve([
        new AutoPRMetricsItem(
          "No metrics available",
          vscode.TreeItemCollapsibleState.None,
        ),
      ]);
    }

    const items: AutoPRMetricsItem[] = [
      new AutoPRMetricsItem(
        "Code Quality Score",
        vscode.TreeItemCollapsibleState.None,
        metrics.code_quality_score,
        "/100",
      ),
      new AutoPRMetricsItem(
        "Issues Fixed",
        vscode.TreeItemCollapsibleState.None,
        metrics.issues_fixed,
      ),
      new AutoPRMetricsItem(
        "Files Analyzed",
        vscode.TreeItemCollapsibleState.None,
        metrics.files_analyzed,
      ),
      new AutoPRMetricsItem(
        "Average Performance",
        vscode.TreeItemCollapsibleState.None,
        metrics.performance_avg,
        "ms",
      ),
      new AutoPRMetricsItem(
        "Complexity Score",
        vscode.TreeItemCollapsibleState.None,
        metrics.complexity_score,
        "/10",
      ),
      new AutoPRMetricsItem(
        "Documentation Coverage",
        vscode.TreeItemCollapsibleState.None,
        metrics.documentation_coverage,
        "%",
      ),
      new AutoPRMetricsItem(
        "Security Score",
        vscode.TreeItemCollapsibleState.None,
        metrics.security_score,
        "/100",
      ),
    ];

    // Add performance averages for different operations
    const operations = [
      "quality_check",
      "auto_fix",
      "file_split_analysis",
      "security_scan",
    ];
    operations.forEach((operation) => {
      const avg = this.dataService.getAveragePerformance(operation);
      if (avg > 0) {
        items.push(
          new AutoPRMetricsItem(
            `${operation.replace("_", " ").toUpperCase()} Avg`,
            vscode.TreeItemCollapsibleState.None,
            Math.round(avg),
            "ms",
          ),
        );
      }
    });

    return Promise.resolve(items);
  }

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }
}

export class AutoPRHistoryProvider
  implements vscode.TreeDataProvider<AutoPRHistoryItem>
{
  private _onDidChangeTreeData: vscode.EventEmitter<
    AutoPRHistoryItem | undefined | null | void
  > = new vscode.EventEmitter<AutoPRHistoryItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<
    AutoPRHistoryItem | undefined | null | void
  > = this._onDidChangeTreeData.event;

  private dataService: DataService;

  constructor() {
    this.dataService = DataService.getInstance();
  }

  getTreeItem(element: AutoPRHistoryItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: AutoPRHistoryItem): Promise<AutoPRHistoryItem[]> {
    const recentActivity = this.dataService.getRecentActivity(20);
    const learningMemory = this.dataService.getLearningMemory();

    if (recentActivity.length === 0) {
      return Promise.resolve([
        new AutoPRHistoryItem(
          "No recent activity",
          vscode.TreeItemCollapsibleState.None,
        ),
      ]);
    }

    const items: AutoPRHistoryItem[] = [];

    // Add recent activity
    recentActivity.forEach((record) => {
      const date = new Date(record.timestamp).toLocaleDateString();
      const time = new Date(record.timestamp).toLocaleTimeString();
      const label = `${date} ${time}: ${record.operation.replace("_", " ")}`;

      items.push(
        new AutoPRHistoryItem(
          label,
          vscode.TreeItemCollapsibleState.None,
          record,
        ),
      );
    });

    // Add learning memory patterns
    learningMemory.patterns.forEach((pattern) => {
      const date = new Date(pattern.last_used).toLocaleDateString();
      const successRate = Math.round(pattern.success_rate * 100);
      const label = `${date}: ${pattern.type.replace("_", " ")} (${successRate}% success)`;

      items.push(
        new AutoPRHistoryItem(label, vscode.TreeItemCollapsibleState.None),
      );
    });

    return Promise.resolve(items);
  }

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }
}
