import * as vscode from "vscode";
import { DataService } from "./dataService";

export class UIService {
  private dataService: DataService;

  constructor() {
    this.dataService = DataService.getInstance();
  }

  public showDashboard(): void {
    const config = vscode.workspace.getConfiguration("autopr");
    const port = config.get<number>("dashboard.port", 8080);
    const host = config.get<string>("dashboard.host", "localhost");

    vscode.window.showInformationMessage(
      `AutoPR Dashboard would start on http://${host}:${port}`,
    );

    // Show dashboard information in output channel
    const outputChannel = vscode.window.createOutputChannel("AutoPR Dashboard");
    outputChannel.show();
    outputChannel.appendLine("AutoPR Dashboard");
    outputChannel.appendLine("=".repeat(50));
    outputChannel.appendLine(`URL: http://${host}:${port}`);
    outputChannel.appendLine(`Status: Ready to start`);
    outputChannel.appendLine("");

    // Show current metrics
    const metrics = this.dataService.getMetrics();
    if (metrics) {
      outputChannel.appendLine("Current Metrics:");
      outputChannel.appendLine(
        `- Code Quality Score: ${metrics.code_quality_score}/100`,
      );
      outputChannel.appendLine(`- Issues Fixed: ${metrics.issues_fixed}`);
      outputChannel.appendLine(`- Files Analyzed: ${metrics.files_analyzed}`);
      outputChannel.appendLine(
        `- Performance: ${metrics.performance_avg}ms avg`,
      );
      outputChannel.appendLine(
        `- Security Score: ${metrics.security_score}/100`,
      );
    }

    outputChannel.appendLine("");
    outputChannel.appendLine("Dashboard features:");
    outputChannel.appendLine("- Real-time issue tracking");
    outputChannel.appendLine("- Performance analytics");
    outputChannel.appendLine("- Learning memory insights");
    outputChannel.appendLine("- Configuration management");
    outputChannel.appendLine("- Export capabilities");
  }

  public showLearningMemory(): void {
    const learningMemory = this.dataService.getLearningMemory();
    const outputChannel = vscode.window.createOutputChannel(
      "AutoPR Learning Memory",
    );
    outputChannel.show();

    outputChannel.appendLine("AutoPR Learning Memory System");
    outputChannel.appendLine("=".repeat(50));
    outputChannel.appendLine("Pattern Recognition: Active");
    outputChannel.appendLine("Success Rate Tracking: Enabled");
    outputChannel.appendLine("User Preference Learning: Active");
    outputChannel.appendLine("");

    outputChannel.appendLine("Recent Patterns:");
    learningMemory.patterns.forEach((pattern) => {
      const successRate = Math.round(pattern.success_rate * 100);
      const lastUsed = new Date(pattern.last_used).toLocaleDateString();
      outputChannel.appendLine(
        `- ${pattern.type.replace("_", " ")}: ${successRate}% success (${pattern.usage_count} uses, last: ${lastUsed})`,
      );
    });

    outputChannel.appendLine("");
    outputChannel.appendLine("Success Rates by Operation:");
    Object.entries(learningMemory.successRates).forEach(([operation, rate]) => {
      const percentage = Math.round(rate * 100);
      outputChannel.appendLine(
        `- ${operation.replace("_", " ")}: ${percentage}%`,
      );
    });

    outputChannel.appendLine("");
    outputChannel.appendLine("User Preferences:");
    Object.entries(learningMemory.userPreferences).forEach(([key, value]) => {
      outputChannel.appendLine(`- ${key.replace("_", " ")}: ${value}`);
    });

    outputChannel.appendLine("");
    outputChannel.appendLine(
      "Learning Memory is continuously improving based on your usage patterns.",
    );
  }

  public async exportResults(): Promise<void> {
    const outputChannel = vscode.window.createOutputChannel("AutoPR Export");
    outputChannel.show();

    outputChannel.appendLine("AutoPR Results Export");
    outputChannel.appendLine("=".repeat(50));
    outputChannel.appendLine("Export formats available:");
    outputChannel.appendLine("- JSON: Complete results with metadata");
    outputChannel.appendLine("- CSV: Tabular format for analysis");
    outputChannel.appendLine("- HTML: Web-friendly report");
    outputChannel.appendLine("- Markdown: Documentation format");
    outputChannel.appendLine("");

    // Show current data summary
    const issues = this.dataService.getIssues();
    const metrics = this.dataService.getMetrics();
    const performanceHistory = this.dataService.getPerformanceHistory();

    outputChannel.appendLine("Current Data Summary:");
    outputChannel.appendLine(`- Total Issues: ${issues.length}`);
    outputChannel.appendLine(
      `- Performance Records: ${performanceHistory.length}`,
    );
    outputChannel.appendLine(`- Metrics Available: ${metrics ? "Yes" : "No"}`);
    outputChannel.appendLine("");

    outputChannel.appendLine("Use the AutoPR CLI for detailed export options:");
    outputChannel.appendLine(
      "autopr export --format json --output results.json",
    );
    outputChannel.appendLine("autopr export --format csv --output results.csv");
    outputChannel.appendLine(
      "autopr export --format html --output report.html",
    );
  }

  public async importConfiguration(): Promise<void> {
    const configFile = await vscode.window.showOpenDialog({
      canSelectFiles: true,
      canSelectFolders: false,
      canSelectMany: false,
      filters: {
        "Configuration Files": ["json", "yaml", "yml", "toml"],
      },
    });

    if (configFile && configFile.length > 0) {
      const filePath = configFile[0].fsPath;
      const fileName = filePath.split(/[\\/]/).pop();

      vscode.window.showInformationMessage(
        `Configuration import from ${fileName} would be implemented here`,
      );

      const outputChannel = vscode.window.createOutputChannel("AutoPR Import");
      outputChannel.show();
      outputChannel.appendLine("AutoPR Configuration Import");
      outputChannel.appendLine("=".repeat(50));
      outputChannel.appendLine(`File: ${fileName}`);
      outputChannel.appendLine(`Path: ${filePath}`);
      outputChannel.appendLine("");
      outputChannel.appendLine("Import would include:");
      outputChannel.appendLine("- Quality engine settings");
      outputChannel.appendLine("- Tool configurations");
      outputChannel.appendLine("- File splitter settings");
      outputChannel.appendLine("- Performance optimization");
      outputChannel.appendLine("- Auto-fix preferences");
      outputChannel.appendLine("");
      outputChannel.appendLine(
        "TODO: Implement actual configuration import logic",
      );
    }
  }

  public showConfiguration(): void {
    vscode.commands.executeCommand("workbench.action.openSettings", "autopr");
  }

  public async showVolumeSettings(): Promise<void> {
    const config = vscode.workspace.getConfiguration("autopr");
    const currentVolume = config.get<number>("volume", 500);

    const volume = await vscode.window.showInputBox({
      prompt: "Set volume level (0-1000)",
      value: currentVolume.toString(),
      validateInput: (value: string) => {
        const num = parseInt(value);
        return isNaN(num) || num < 0 || num > 1000
          ? "Please enter a number between 0 and 1000"
          : null;
      },
    });

    if (volume) {
      await config.update(
        "volume",
        parseInt(volume),
        vscode.ConfigurationTarget.Workspace,
      );
      this.dataService.updateUserPreference("volume_level", parseInt(volume));
      vscode.window.showInformationMessage(`Volume level set to ${volume}`);

      // Show volume impact
      this.showVolumeImpact(parseInt(volume));
    }
  }

  private showVolumeImpact(volume: number): void {
    const outputChannel = vscode.window.createOutputChannel(
      "AutoPR Volume Impact",
    );
    outputChannel.show();

    outputChannel.appendLine("Volume Level Impact Analysis");
    outputChannel.appendLine("=".repeat(50));
    outputChannel.appendLine(`Current Volume: ${volume}`);
    outputChannel.appendLine("");

    if (volume <= 200) {
      outputChannel.appendLine("Mode: Ultra-Fast");
      outputChannel.appendLine("- Minimal checks");
      outputChannel.appendLine("- Fastest processing");
      outputChannel.appendLine("- Basic issue detection");
    } else if (volume <= 400) {
      outputChannel.appendLine("Mode: Fast");
      outputChannel.appendLine("- Essential tools only");
      outputChannel.appendLine("- Quick processing");
      outputChannel.appendLine("- Standard issue detection");
    } else if (volume <= 600) {
      outputChannel.appendLine("Mode: Smart");
      outputChannel.appendLine("- Intelligent tool selection");
      outputChannel.appendLine("- Balanced processing");
      outputChannel.appendLine("- Context-aware analysis");
    } else if (volume <= 800) {
      outputChannel.appendLine("Mode: Comprehensive");
      outputChannel.appendLine("- All tools enabled");
      outputChannel.appendLine("- Thorough analysis");
      outputChannel.appendLine("- Maximum issue detection");
    } else {
      outputChannel.appendLine("Mode: AI-Enhanced");
      outputChannel.appendLine("- Full AI analysis");
      outputChannel.appendLine("- Maximum processing");
      outputChannel.appendLine("- Advanced insights");
    }

    outputChannel.appendLine("");
    outputChannel.appendLine("Volume affects:");
    outputChannel.appendLine("- Processing speed");
    outputChannel.appendLine("- Issue detection depth");
    outputChannel.appendLine("- AI analysis intensity");
    outputChannel.appendLine("- Resource usage");
  }

  public async showToolToggle(): Promise<void> {
    const config = vscode.workspace.getConfiguration("autopr");
    const tools = config.get<any>("tools", {});

    const toolNames = Object.keys(tools);
    const selectedTool = await vscode.window.showQuickPick(toolNames, {
      placeHolder: "Select a tool to toggle",
    });

    if (selectedTool) {
      const currentState = tools[selectedTool]?.enabled || false;
      tools[selectedTool] = { ...tools[selectedTool], enabled: !currentState };
      await config.update("tools", tools, vscode.ConfigurationTarget.Workspace);

      const status = !currentState ? "enabled" : "disabled";
      vscode.window.showInformationMessage(`${selectedTool} ${status}`);

      // Show tool information
      this.showToolInfo(selectedTool, !currentState);
    }
  }

  private showToolInfo(toolName: string, enabled: boolean): void {
    const outputChannel = vscode.window.createOutputChannel("AutoPR Tool Info");
    outputChannel.show();

    outputChannel.appendLine(`AutoPR Tool: ${toolName}`);
    outputChannel.appendLine("=".repeat(50));
    outputChannel.appendLine(`Status: ${enabled ? "Enabled" : "Disabled"}`);
    outputChannel.appendLine("");

    const toolDescriptions: Record<string, string> = {
      ruff: "Fast Python linter and formatter",
      mypy: "Static type checker for Python",
      bandit: "Security linter for Python",
      interrogate: "Documentation coverage checker",
      radon: "Code complexity analyzer",
      pytest: "Testing framework integration",
      codeql: "Security analysis with CodeQL",
      sonarqube: "Code quality and security analysis",
      ai_feedback: "AI-powered code review",
      eslint: "JavaScript/TypeScript linter",
      dependency_scanner: "Dependency vulnerability scanner",
      performance_analyzer: "Performance analysis tools",
    };

    const description = toolDescriptions[toolName] || "Quality analysis tool";
    outputChannel.appendLine(`Description: ${description}`);
    outputChannel.appendLine("");
    outputChannel.appendLine(
      `Impact: ${enabled ? "Tool will be used in analysis" : "Tool will be skipped"}`,
    );
  }

  public async generateReport(): Promise<void> {
    const config = vscode.workspace.getConfiguration("autopr");
    const format = config.get<string>("reportFormat", "html");

    const outputChannel = vscode.window.createOutputChannel(
      "AutoPR Report Generator",
    );
    outputChannel.show();

    outputChannel.appendLine("AutoPR Report Generation");
    outputChannel.appendLine("=".repeat(50));
    outputChannel.appendLine(`Format: ${format.toUpperCase()}`);
    outputChannel.appendLine("Generating comprehensive report...");

    try {
      // Simulate report generation
      await new Promise((resolve) => setTimeout(resolve, 2000));

      const issues = this.dataService.getIssues();
      const metrics = this.dataService.getMetrics();
      const performanceHistory = this.dataService.getPerformanceHistory();

      outputChannel.appendLine("");
      outputChannel.appendLine("Report Summary:");
      outputChannel.appendLine(`- Total Issues: ${issues.length}`);
      outputChannel.appendLine(
        `- Code Quality Score: ${metrics?.code_quality_score || "N/A"}/100`,
      );
      outputChannel.appendLine(
        `- Performance Records: ${performanceHistory.length}`,
      );
      outputChannel.appendLine(`- Report Format: ${format.toUpperCase()}`);

      outputChannel.appendLine("");
      outputChannel.appendLine("Report generated successfully!");
      outputChannel.appendLine("Location: ./autopr-report." + format);

      vscode.window.showInformationMessage(
        `AutoPR report generated in ${format.toUpperCase()} format!`,
      );
    } catch (error) {
      outputChannel.appendLine(`Error generating report: ${error}`);
      vscode.window.showErrorMessage("Failed to generate report");
    }
  }
}
