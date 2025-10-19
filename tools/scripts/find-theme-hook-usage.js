/**
 * Script to identify components using useTheme hooks that might need ThemeProvider wrappers
 *
 * This script searches the codebase for:
 * 1. Components using the useTheme hook directly
 * 2. Components using other components that might use useTheme
 * 3. Potential locations where ThemeProvider is missing
 *
 * Usage: node scripts/find-theme-hook-usage.js
 */

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

// Configuration
const SEARCH_DIRS = ["app", "components", "src", "contexts", "hooks"];
const THEME_HOOKS = [
  "useTheme",
  "useCurrentTheme",
  "useAvailableThemeVariants",
  "useThemeAwareImage",
];
const THEME_COMPONENTS = [
  "ThemeAwareImage",
  "ThemeAwareBackground",
  "ThemeToggle",
];
const THEME_PROVIDERS = ["ThemeProvider", "<ThemeProvider", "ThemeProvider>"];

// Results storage
const results = {
  hookUsage: [],
  themeComponents: [],
  themeProviders: [],
  potentialIssues: [],
};

/**
 * Recursively collects JavaScript and TypeScript source file paths from a directory and its subdirectories, excluding `node_modules` and `.next` folders.
 *
 * @param {string} dir - The root directory to search.
 * @param {string[]} [fileList=[]] - Accumulator for found file paths.
 * @returns {string[]} Array of file paths with `.js`, `.jsx`, `.ts`, or `.tsx` extensions.
 */
function findFiles(dir, fileList = []) {
  const files = fs.readdirSync(dir);

  files.forEach((file) => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);

    if (stat.isDirectory()) {
      // Skip node_modules and .next directories
      if (file !== "node_modules" && file !== ".next") {
        findFiles(filePath, fileList);
      }
    } else if (
      file.endsWith(".tsx") ||
      file.endsWith(".ts") ||
      file.endsWith(".jsx") ||
      file.endsWith(".js")
    ) {
      fileList.push(filePath);
    }
  });

  return fileList;
}

/**
 * Searches a file for specified string patterns and returns details of each match.
 *
 * For each pattern found, records the pattern, line number, and trimmed line content.
 *
 * @param {string} filePath - Path to the file to search.
 * @param {string[]} patterns - Array of string patterns to search for.
 * @returns {Array<{pattern: string, line: number, context: string}>} Array of match objects with pattern, line number, and context.
 *
 * @remark Returns an empty array if the file cannot be read.
 */
function searchInFile(filePath, patterns) {
  try {
    const content = fs.readFileSync(filePath, "utf8");
    const matches = [];

    patterns.forEach((pattern) => {
      // Simple string search
      if (content.includes(pattern)) {
        const lines = content.split("\n");
        lines.forEach((line, index) => {
          if (line.includes(pattern)) {
            matches.push({
              pattern,
              line: index + 1,
              context: line.trim(),
            });
          }
        });
      }
    });

    return matches;
  } catch (error) {
    console.error(`Error reading file ${filePath}:`, error);
    return [];
  }
}

/**
 * Analyzes a file for usage of theme-related hooks, components, and providers, recording findings and flagging potential missing `ThemeProvider` issues.
 *
 * If theme hooks or theme-aware components are detected without a corresponding `ThemeProvider` in the same file, the file is flagged as a potential issue, with additional context on whether it is likely a page component.
 */
function analyzeFile(filePath) {
  // Find hook usage
  const hookMatches = searchInFile(filePath, THEME_HOOKS);
  if (hookMatches.length > 0) {
    results.hookUsage.push({
      file: filePath,
      matches: hookMatches,
    });
  }

  // Find theme component usage
  const componentMatches = searchInFile(filePath, THEME_COMPONENTS);
  if (componentMatches.length > 0) {
    results.themeComponents.push({
      file: filePath,
      matches: componentMatches,
    });
  }

  // Find theme provider usage
  const providerMatches = searchInFile(filePath, THEME_PROVIDERS);
  if (providerMatches.length > 0) {
    results.themeProviders.push({
      file: filePath,
      matches: providerMatches,
    });
  }

  // Identify potential issues (hook usage without provider in same file)
  if (
    (hookMatches.length > 0 || componentMatches.length > 0) &&
    providerMatches.length === 0
  ) {
    // Check if this is a page component
    const isPageComponent =
      filePath.includes("/page.") ||
      filePath.includes("/pages/") ||
      filePath.includes("/app/");

    results.potentialIssues.push({
      file: filePath,
      isPageComponent,
      hookUsage: hookMatches.length > 0,
      componentUsage: componentMatches.length > 0,
    });
  }
}

// Main execution
console.log("Searching for theme hook and component usage...");

// Find all files to analyze
let allFiles = [];
SEARCH_DIRS.forEach((dir) => {
  if (fs.existsSync(dir)) {
    allFiles = allFiles.concat(findFiles(dir));
  }
});

console.log(`Found ${allFiles.length} files to analyze`);

// Analyze each file
allFiles.forEach((file) => {
  analyzeFile(file);
});

// Generate report
console.log("\n--- THEME USAGE ANALYSIS REPORT ---\n");

console.log(
  `Found ${results.hookUsage.length} files using theme hooks directly`,
);
console.log(
  `Found ${results.themeComponents.length} files using theme-aware components`,
);
console.log(`Found ${results.themeProviders.length} files with ThemeProvider`);
console.log(
  `Identified ${results.potentialIssues.length} files with potential theme provider issues`,
);

console.log("\n--- POTENTIAL ISSUES ---\n");
results.potentialIssues.forEach((issue) => {
  console.log(
    `${issue.file} ${issue.isPageComponent ? "(PAGE COMPONENT)" : ""}`,
  );
  console.log(`  - Hook Usage: ${issue.hookUsage}`);
  console.log(`  - Component Usage: ${issue.componentUsage}`);
  console.log("");
});

// Write results to file
const reportData = {
  summary: {
    totalFiles: allFiles.length,
    hookUsage: results.hookUsage.length,
    themeComponents: results.themeComponents.length,
    themeProviders: results.themeProviders.length,
    potentialIssues: results.potentialIssues.length,
  },
  details: results,
};

fs.writeFileSync(
  "theme-usage-report.json",
  JSON.stringify(reportData, null, 2),
);

console.log("Full report written to theme-usage-report.json");
console.log(
  "\nTo fix these issues, create bridge components that wrap the original components with ThemeProvider.",
);
