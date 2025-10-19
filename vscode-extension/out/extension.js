"use strict";
var __createBinding =
  (this && this.__createBinding) ||
  (Object.create
    ? function (o, m, k, k2) {
        if (k2 === undefined) k2 = k;
        var desc = Object.getOwnPropertyDescriptor(m, k);
        if (
          !desc ||
          ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)
        ) {
          desc = {
            enumerable: true,
            get: function () {
              return m[k];
            },
          };
        }
        Object.defineProperty(o, k2, desc);
      }
    : function (o, m, k, k2) {
        if (k2 === undefined) k2 = k;
        o[k2] = m[k];
      });
var __setModuleDefault =
  (this && this.__setModuleDefault) ||
  (Object.create
    ? function (o, v) {
        Object.defineProperty(o, "default", { enumerable: true, value: v });
      }
    : function (o, v) {
        o["default"] = v;
      });
var __importStar =
  (this && this.__importStar) ||
  function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null)
      for (var k in mod)
        if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k))
          __createBinding(result, mod, k);
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
  const packageJson = require("../package.json");
  // Initialize logging
  const logChannel = vscode.window.createOutputChannel("AutoPR Logs");
  logChannel.appendLine(
    `[${new Date().toISOString()}] AutoPR extension v${packageJson.version} is now active!`,
  );
  console.log(`AutoPR extension v${packageJson.version} is now active!`);
  // Set global extension context for data service
  global.extensionContext = context;
  // Initialize services first
  const commandService = new commandService_1.CommandService();
  const uiService = new uiService_1.UIService();
  const dataService = dataService_1.DataService.getInstance();
  // Check if AutoPR has been initialized for this workspace
  const config = vscode.workspace.getConfiguration("autopr");
  const isInitialized = config.get("initialized", false);
  if (!isInitialized) {
    // First time setup - show initialization options
    const initializeAction = "Initialize AutoPR";
    const analyzeAction = "Analyze Now (Skip Setup)";
    const dismissAction = "Dismiss";
    vscode.window
      .showInformationMessage(
        `AutoPR v${packageJson.version} - First time setup for this workspace:`,
        initializeAction,
        analyzeAction,
        dismissAction,
      )
      .then((selection) => {
        if (selection === initializeAction) {
          // Initialize AutoPR with workspace setup
          logChannel.appendLine(
            `[${new Date().toISOString()}] User selected: Initialize AutoPR`,
          );
          initializeAutoPR(context, commandService, uiService, dataService);
        } else if (selection === analyzeAction) {
          // Run immediate analysis without full setup
          logChannel.appendLine(
            `[${new Date().toISOString()}] User selected: Analyze Now (Skip Setup)`,
          );
          runInitialAnalysis(
            commandService,
            issuesProvider,
            metricsProvider,
            historyProvider,
          );
        } else {
          logChannel.appendLine(
            `[${new Date().toISOString()}] User dismissed initialization`,
          );
        }
      });
  } else {
    // Already initialized - show quick actions
    const analyzeAction = "Analyze Now";
    const settingsAction = "Settings";
    const dismissAction = "Dismiss";
    vscode.window
      .showInformationMessage(
        `AutoPR v${packageJson.version} is ready!`,
        analyzeAction,
        settingsAction,
        dismissAction,
      )
      .then((selection) => {
        if (selection === analyzeAction) {
          logChannel.appendLine(
            `[${new Date().toISOString()}] User selected: Analyze Now`,
          );
          runInitialAnalysis(
            commandService,
            issuesProvider,
            metricsProvider,
            historyProvider,
          );
        } else if (selection === settingsAction) {
          logChannel.appendLine(
            `[${new Date().toISOString()}] User selected: Settings`,
          );
          vscode.commands.executeCommand("autopr.showSettings");
        } else {
          logChannel.appendLine(
            `[${new Date().toISOString()}] User dismissed notification`,
          );
        }
      });
  }
  // Try to show the AutoPR views automatically with editor-specific timing
  const appName = vscode.env.appName || "";
  const delay = appName.toLowerCase().includes("cursor") ? 1500 : 1000; // Cursor might need more time
  setTimeout(() => {
    vscode.commands.executeCommand("workbench.view.extension.autopr").then(
      () => {
        console.log("AutoPR: Views shown successfully");
      },
      (error) => {
        console.log(
          "AutoPR: Could not show views automatically:",
          error.message,
        );
      },
    );
  }, delay);
  // Register diagnostic collection
  const diagnosticCollection =
    vscode.languages.createDiagnosticCollection("autopr");
  context.subscriptions.push(diagnosticCollection);
  // Register tree data providers and create tree views
  const issuesProvider = new treeProviders_1.AutoPRIssuesProvider();
  const metricsProvider = new treeProviders_1.AutoPRMetricsProvider();
  const historyProvider = new treeProviders_1.AutoPRHistoryProvider();
  // Register tree data providers first
  vscode.window.registerTreeDataProvider("autoprIssues", issuesProvider);
  vscode.window.registerTreeDataProvider("autoprMetrics", metricsProvider);
  vscode.window.registerTreeDataProvider("autoprHistory", historyProvider);
  // Create tree views
  const issuesView = vscode.window.createTreeView("autoprIssues", {
    treeDataProvider: issuesProvider,
  });
  const metricsView = vscode.window.createTreeView("autoprMetrics", {
    treeDataProvider: metricsProvider,
  });
  const historyView = vscode.window.createTreeView("autoprHistory", {
    treeDataProvider: historyProvider,
  });
  context.subscriptions.push(issuesView, metricsView, historyView);
  // Debug logging
  console.log("Tree views created:", {
    issues: issuesView.visible,
    metrics: metricsView.visible,
    history: historyView.visible,
  });
  // Register commands
  const commands = [
    // Quality Check Commands
    vscode.commands.registerCommand("autopr.qualityCheck", () => {
      commandService.runQualityCheck().then(() => {
        issuesProvider.refresh();
        metricsProvider.refresh();
      });
    }),
    vscode.commands.registerCommand("autopr.qualityCheckFile", () => {
      commandService.runQualityCheckFile().then(() => {
        issuesProvider.refresh();
        metricsProvider.refresh();
      });
    }),
    vscode.commands.registerCommand("autopr.qualityCheckWorkspace", () => {
      commandService.runQualityCheckWorkspace().then(() => {
        issuesProvider.refresh();
        metricsProvider.refresh();
      });
    }),
    // File Splitter Commands
    vscode.commands.registerCommand("autopr.fileSplit", () => {
      commandService.runFileSplit().then(() => {
        issuesProvider.refresh();
        metricsProvider.refresh();
      });
    }),
    // Auto-Fix Commands
    vscode.commands.registerCommand("autopr.autoFix", () => {
      commandService.runAutoFix().then(() => {
        issuesProvider.refresh();
        metricsProvider.refresh();
      });
    }),
    // Specialized Analysis Commands
    vscode.commands.registerCommand("autopr.performanceCheck", () => {
      commandService.runPerformanceCheck().then(() => {
        issuesProvider.refresh();
        metricsProvider.refresh();
      });
    }),
    vscode.commands.registerCommand("autopr.dependencyScan", () => {
      commandService.runDependencyScan().then(() => {
        issuesProvider.refresh();
        metricsProvider.refresh();
      });
    }),
    vscode.commands.registerCommand("autopr.securityScan", () => {
      commandService.runSecurityScan().then(() => {
        issuesProvider.refresh();
        metricsProvider.refresh();
      });
    }),
    vscode.commands.registerCommand("autopr.complexityAnalysis", () => {
      commandService.runComplexityAnalysis().then(() => {
        issuesProvider.refresh();
        metricsProvider.refresh();
      });
    }),
    vscode.commands.registerCommand("autopr.documentationCheck", () => {
      commandService.runDocumentationCheck().then(() => {
        issuesProvider.refresh();
        metricsProvider.refresh();
      });
    }),
    // Configuration Commands
    vscode.commands.registerCommand("autopr.setVolume", () => {
      uiService.showVolumeSettings();
    }),
    vscode.commands.registerCommand("autopr.toggleTool", () => {
      uiService.showToolToggle();
    }),
    vscode.commands.registerCommand("autopr.configure", () => {
      uiService.showConfiguration();
    }),
    // Utility Commands
    vscode.commands.registerCommand("autopr.clearCache", () => {
      commandService.clearCache();
    }),
    vscode.commands.registerCommand("autopr.exportResults", () => {
      uiService.exportResults();
    }),
    vscode.commands.registerCommand("autopr.importConfig", () => {
      uiService.importConfiguration();
    }),
    // UI Commands
    vscode.commands.registerCommand("autopr.showDashboard", () => {
      uiService.showDashboard();
    }),
    vscode.commands.registerCommand("autopr.learningMemory", () => {
      uiService.showLearningMemory();
    }),
    // Refresh commands for tree views
    vscode.commands.registerCommand("autopr.refreshIssues", () => {
      issuesProvider.refresh();
    }),
    vscode.commands.registerCommand("autopr.refreshMetrics", () => {
      metricsProvider.refresh();
    }),
    vscode.commands.registerCommand("autopr.refreshHistory", () => {
      historyProvider.refresh();
    }),
    vscode.commands.registerCommand("autopr.showVersion", () => {
      const packageJson = require("../package.json");
      vscode.window.showInformationMessage(
        `AutoPR Extension Version: ${packageJson.version}`,
      );
    }),
    vscode.commands.registerCommand("autopr.refreshAll", () => {
      issuesProvider.refresh();
      metricsProvider.refresh();
      historyProvider.refresh();
      vscode.window.showInformationMessage("All AutoPR views refreshed!");
    }),
    vscode.commands.registerCommand("autopr.showViews", () => {
      // Force show the AutoPR view container
      vscode.commands.executeCommand("workbench.view.extension.autopr");
      vscode.window.showInformationMessage(
        "AutoPR views should now be visible!",
      );
    }),
    vscode.commands.registerCommand("autopr.quickFix", () => {
      commandService.runQuickFix().then(() => {
        issuesProvider.refresh();
        metricsProvider.refresh();
        vscode.window.showInformationMessage("AutoPR: Quick fixes applied!");
      });
    }),
    vscode.commands.registerCommand("autopr.analyzeWorkspace", () => {
      commandService.runWorkspaceAnalysis().then(() => {
        issuesProvider.refresh();
        metricsProvider.refresh();
        historyProvider.refresh();
        vscode.window.showInformationMessage(
          "AutoPR: Workspace analysis complete!",
        );
      });
    }),
    vscode.commands.registerCommand("autopr.generateReport", () => {
      uiService.generateReport().then(() => {
        vscode.window.showInformationMessage(
          "AutoPR: Report generated successfully!",
        );
      });
    }),
    vscode.commands.registerCommand("autopr.toggleAutoMode", () => {
      const config = vscode.workspace.getConfiguration("autopr");
      const currentMode = config.get("autoMode", false);
      config.update(
        "autoMode",
        !currentMode,
        vscode.ConfigurationTarget.Global,
      );
      vscode.window.showInformationMessage(
        `AutoPR: Auto mode ${!currentMode ? "enabled" : "disabled"}!`,
      );
    }),
    vscode.commands.registerCommand("autopr.showSettings", () => {
      vscode.commands.executeCommand("workbench.action.openSettings", "autopr");
    }),
    vscode.commands.registerCommand("autopr.showHelp", () => {
      vscode.window.showInformationMessage(
        "AutoPR Help: Visit https://github.com/autopr/autopr-engine for documentation",
      );
    }),
    vscode.commands.registerCommand("autopr.checkCompatibility", () => {
      checkEditorCompatibility();
    }),
    vscode.commands.registerCommand("autopr.showLogs", () => {
      vscode.window.createOutputChannel("AutoPR Logs").show();
    }),
  ];
  // Add all commands to subscriptions
  context.subscriptions.push(...commands);
  // Initialize with sample data for demonstration
  initializeSampleData(dataService);
  console.log("AutoPR extension activated with modular architecture");
  logChannel.appendLine(
    `[${new Date().toISOString()}] AutoPR extension activated with modular architecture`,
  );
  // Log editor compatibility
  logEditorCompatibility(logChannel);
}
exports.activate = activate;
async function initializeAutoPR(
  context,
  commandService,
  uiService,
  dataService,
) {
  const outputChannel = vscode.window.createOutputChannel(
    "AutoPR Initialization",
  );
  outputChannel.show();
  outputChannel.appendLine("AutoPR Initialization");
  outputChannel.appendLine("=".repeat(50));
  outputChannel.appendLine("Setting up AutoPR for your workspace...");
  try {
    // Check workspace structure
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders) {
      throw new Error("No workspace folder found");
    }
    outputChannel.appendLine(`Workspace: ${workspaceFolders[0].name}`);
    // Detect project type and set up configuration
    const projectType = await detectProjectType(workspaceFolders[0].uri.fsPath);
    outputChannel.appendLine(`Project type detected: ${projectType}`);
    // Set up initial configuration
    await setupInitialConfiguration(projectType);
    outputChannel.appendLine("Configuration initialized");
    // Initialize data service with workspace context
    dataService.initializeWorkspace(workspaceFolders[0].uri.fsPath);
    outputChannel.appendLine("Data service initialized");
    // Show success notification with next steps
    const analyzeAction = "Run First Analysis";
    const configureAction = "Configure Settings";
    vscode.window
      .showInformationMessage(
        "AutoPR initialized successfully! Your workspace is ready for analysis.",
        analyzeAction,
        configureAction,
      )
      .then((selection) => {
        if (selection === analyzeAction) {
          vscode.commands.executeCommand("autopr.analyzeWorkspace");
        } else if (selection === configureAction) {
          vscode.commands.executeCommand("autopr.showSettings");
        }
      });
    outputChannel.appendLine("Initialization completed successfully!");
  } catch (error) {
    outputChannel.appendLine(`Error during initialization: ${error}`);
    vscode.window.showErrorMessage(`AutoPR initialization failed: ${error}`);
  }
}
async function runInitialAnalysis(
  commandService,
  issuesProvider,
  metricsProvider,
  historyProvider,
) {
  const outputChannel = vscode.window.createOutputChannel("AutoPR Analysis");
  outputChannel.show();
  outputChannel.appendLine("AutoPR Initial Analysis");
  outputChannel.appendLine("=".repeat(50));
  outputChannel.appendLine("Starting workspace analysis...");
  try {
    // Run workspace analysis
    await commandService.runWorkspaceAnalysis();
    // Refresh all providers
    issuesProvider.refresh();
    metricsProvider.refresh();
    historyProvider.refresh();
    outputChannel.appendLine("Analysis completed successfully!");
    // Show results notification
    const viewResultsAction = "View Results";
    const configureAction = "Configure Analysis";
    vscode.window
      .showInformationMessage(
        "Initial analysis completed! Issues and metrics are now available.",
        viewResultsAction,
        configureAction,
      )
      .then((selection) => {
        if (selection === viewResultsAction) {
          vscode.commands.executeCommand("workbench.view.extension.autopr");
        } else if (selection === configureAction) {
          vscode.commands.executeCommand("autopr.showSettings");
        }
      });
  } catch (error) {
    outputChannel.appendLine(`Error during analysis: ${error}`);
    vscode.window.showErrorMessage(`Analysis failed: ${error}`);
  }
}
async function detectProjectType(workspacePath) {
  // Simple project type detection
  const fs = require("fs");
  const path = require("path");
  if (fs.existsSync(path.join(workspacePath, "pyproject.toml"))) {
    return "Python (Poetry)";
  } else if (fs.existsSync(path.join(workspacePath, "requirements.txt"))) {
    return "Python (pip)";
  } else if (fs.existsSync(path.join(workspacePath, "package.json"))) {
    return "Node.js";
  } else if (fs.existsSync(path.join(workspacePath, "Cargo.toml"))) {
    return "Rust";
  } else if (fs.existsSync(path.join(workspacePath, "go.mod"))) {
    return "Go";
  } else {
    return "Mixed/Unknown";
  }
}
async function setupInitialConfiguration(projectType) {
  const config = vscode.workspace.getConfiguration("autopr");
  // Set project-specific defaults
  if (projectType.includes("Python")) {
    await config.update(
      "qualityMode",
      "smart",
      vscode.ConfigurationTarget.Workspace,
    );
    // Note: tools configuration is handled by the tools object, not individual settings
  } else if (projectType.includes("Node.js")) {
    await config.update(
      "qualityMode",
      "fast",
      vscode.ConfigurationTarget.Workspace,
    );
    // Note: tools configuration is handled by the tools object, not individual settings
  } else {
    await config.update(
      "qualityMode",
      "comprehensive",
      vscode.ConfigurationTarget.Workspace,
    );
  }
  // Set general defaults
  await config.update("autoMode", false, vscode.ConfigurationTarget.Workspace);
  await config.update(
    "showNotifications",
    true,
    vscode.ConfigurationTarget.Workspace,
  );
  await config.update(
    "notificationLevel",
    "warnings",
    vscode.ConfigurationTarget.Workspace,
  );
  // Mark workspace as initialized
  await config.update(
    "initialized",
    true,
    vscode.ConfigurationTarget.Workspace,
  );
}
function logEditorCompatibility(logChannel) {
  const appName = vscode.env.appName || "Unknown";
  const appVersion = vscode.version || "Unknown";
  const logMessage = `AutoPR running on: ${appName} v${appVersion}`;
  console.log(logMessage);
  logChannel?.appendLine(`[${new Date().toISOString()}] ${logMessage}`);
  // Check for specific editors and log compatibility
  let editorInfo = "";
  if (appName.toLowerCase().includes("cursor")) {
    editorInfo = "AutoPR: Cursor editor detected - full compatibility";
  } else if (appName.toLowerCase().includes("windsurf")) {
    editorInfo = "AutoPR: Windsurf editor detected - full compatibility";
  } else if (appName.toLowerCase().includes("vscode")) {
    editorInfo = "AutoPR: VS Code editor detected - full compatibility";
  } else {
    editorInfo = "AutoPR: Unknown editor - testing compatibility";
  }
  console.log(editorInfo);
  logChannel?.appendLine(`[${new Date().toISOString()}] ${editorInfo}`);
  // Log available features
  console.log("AutoPR: Available features:");
  logChannel?.appendLine(
    `[${new Date().toISOString()}] AutoPR: Available features:`,
  );
  const features = [
    { name: "Tree views", test: () => !!vscode.window.createTreeView },
    { name: "Status bar", test: () => !!vscode.window.createStatusBarItem },
    {
      name: "Output channels",
      test: () => !!vscode.window.createOutputChannel,
    },
    { name: "Commands", test: () => !!vscode.commands.registerCommand },
    { name: "Configuration", test: () => !!vscode.workspace.getConfiguration },
  ];
  features.forEach((feature) => {
    const available = feature.test();
    const message = `- ${feature.name}: ${available}`;
    console.log(message);
    logChannel?.appendLine(`[${new Date().toISOString()}] ${message}`);
  });
}
function checkEditorCompatibility() {
  const appName = vscode.env.appName || "Unknown";
  const appVersion = vscode.version || "Unknown";
  const outputChannel = vscode.window.createOutputChannel(
    "AutoPR Compatibility",
  );
  outputChannel.show();
  outputChannel.appendLine("AutoPR Editor Compatibility Check");
  outputChannel.appendLine("=".repeat(50));
  outputChannel.appendLine(`Editor: ${appName}`);
  outputChannel.appendLine(`Version: ${appVersion}`);
  outputChannel.appendLine("");
  // Test various features
  const features = [
    { name: "Tree Views", test: () => !!vscode.window.createTreeView },
    { name: "Status Bar", test: () => !!vscode.window.createStatusBarItem },
    {
      name: "Output Channels",
      test: () => !!vscode.window.createOutputChannel,
    },
    { name: "Commands", test: () => !!vscode.commands.registerCommand },
    { name: "Configuration", test: () => !!vscode.workspace.getConfiguration },
    { name: "File System", test: () => !!vscode.workspace.fs },
    {
      name: "Language Features",
      test: () => !!vscode.languages.createDiagnosticCollection,
    },
  ];
  outputChannel.appendLine("Feature Compatibility:");
  features.forEach((feature) => {
    const available = feature.test();
    const status = available ? "✓ Available" : "✗ Not Available";
    outputChannel.appendLine(`- ${feature.name}: ${status}`);
  });
  outputChannel.appendLine("");
  // Editor-specific information
  if (appName.toLowerCase().includes("cursor")) {
    outputChannel.appendLine("Cursor Editor Detected:");
    outputChannel.appendLine("- Full compatibility with AutoPR features");
    outputChannel.appendLine("- AI-enhanced code analysis supported");
    outputChannel.appendLine("- All tree views and commands available");
  } else if (appName.toLowerCase().includes("windsurf")) {
    outputChannel.appendLine("Windsurf Editor Detected:");
    outputChannel.appendLine("- Full compatibility with AutoPR features");
    outputChannel.appendLine("- All tree views and commands available");
  } else if (appName.toLowerCase().includes("vscode")) {
    outputChannel.appendLine("VS Code Editor Detected:");
    outputChannel.appendLine("- Full compatibility with AutoPR features");
    outputChannel.appendLine("- All features supported");
  } else {
    outputChannel.appendLine("Unknown Editor:");
    outputChannel.appendLine("- Testing compatibility with available features");
    outputChannel.appendLine("- Some features may not work as expected");
  }
  outputChannel.appendLine("");
  outputChannel.appendLine("AutoPR is ready to use!");
  vscode.window.showInformationMessage(
    `AutoPR compatibility check completed. Check the output channel for details.`,
  );
}
function initializeSampleData(dataService) {
  // Add some sample issues for demonstration
  const sampleIssues = [
    {
      file: "src/example.py",
      line: 15,
      column: 5,
      message: 'Unused import "os"',
      severity: "warning",
      tool: "ruff",
      code: "F401",
      fixable: true,
      confidence: 0.95,
    },
    {
      file: "src/example.py",
      line: 25,
      column: 10,
      message: 'Variable "x" is assigned but never used',
      severity: "warning",
      tool: "ruff",
      code: "F841",
      fixable: true,
      confidence: 0.98,
    },
    {
      file: "src/security.py",
      line: 42,
      column: 8,
      message: "Possible SQL injection vulnerability",
      severity: "error",
      tool: "bandit",
      code: "B608",
      fixable: false,
      confidence: 0.85,
    },
    {
      file: "src/complexity.py",
      line: 78,
      column: 12,
      message: "Function has high cyclomatic complexity (15)",
      severity: "info",
      tool: "radon",
      code: "C901",
      fixable: false,
      confidence: 0.75,
    },
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
    security_score: 92,
  };
  dataService.setMetrics(sampleMetrics);
  // Add sample performance history
  const sampleHistory = [
    {
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      operation: "quality_check",
      duration: 2500,
      success: true,
      issues_found: 8,
      issues_fixed: 3,
    },
    {
      timestamp: new Date(Date.now() - 7200000).toISOString(),
      operation: "auto_fix",
      duration: 1800,
      success: true,
      issues_found: 5,
      issues_fixed: 5,
    },
    {
      timestamp: new Date(Date.now() - 10800000).toISOString(),
      operation: "file_split_analysis",
      duration: 3200,
      success: true,
      issues_found: 0,
      issues_fixed: 0,
    },
  ];
  sampleHistory.forEach((record) => {
    dataService.addPerformanceRecord(record);
  });
}
function deactivate() {
  console.log("AutoPR extension is now deactivated!");
}
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map
