import * as assert from "assert";
import * as vscode from "vscode";

suite("Extension Test Suite", () => {
  vscode.window.showInformationMessage("Start all tests.");

  test("Extension should be present", () => {
    assert.ok(vscode.extensions.getExtension("autopr"));
  });

  test("Should activate", async () => {
    const extension = vscode.extensions.getExtension("autopr");
    if (extension) {
      await extension.activate();
      assert.ok(extension.isActive);
    }
  });

  test("Should register commands", async () => {
    const commands = await vscode.commands.getCommands();
    const autoprCommands = commands.filter((cmd) => cmd.startsWith("autopr."));

    assert.ok(autoprCommands.includes("autopr.qualityCheck"));
    assert.ok(autoprCommands.includes("autopr.qualityCheckFile"));
    assert.ok(autoprCommands.includes("autopr.qualityCheckWorkspace"));
    assert.ok(autoprCommands.includes("autopr.fileSplit"));
    assert.ok(autoprCommands.includes("autopr.autoFix"));
    assert.ok(autoprCommands.includes("autopr.showDashboard"));
    assert.ok(autoprCommands.includes("autopr.configure"));
  });

  test("Should have configuration", () => {
    const config = vscode.workspace.getConfiguration("autopr");
    assert.ok(config.has("enabled"));
    assert.ok(config.has("qualityMode"));
    assert.ok(config.has("autoFixEnabled"));
    assert.ok(config.has("showNotifications"));
    assert.ok(config.has("pythonPath"));
    assert.ok(config.has("maxFileSize"));
  });
});
