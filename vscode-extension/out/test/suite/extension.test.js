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
const assert = __importStar(require("assert"));
const vscode = __importStar(require("vscode"));
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
//# sourceMappingURL=extension.test.js.map
