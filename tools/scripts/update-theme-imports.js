#!/usr/bin/env node

/**
 * Theme Import Migration Script
 *
 * This script scans the codebase for theme-related imports and updates them
 * to use the consolidated single source of truth.
 *
 * Usage:
 *   node scripts/update-theme-imports.js [--dry-run] [--path=./src]
 *
 * Options:
 *   --dry-run    Show changes without applying them
 *   --path       Specify a subdirectory to process (default: ./src)
 */

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

// Parse command line arguments
const args = process.argv.slice(2);
const dryRun = args.includes("--dry-run");
const pathArg = args.find((arg) => arg.startsWith("--path="));
const rootDir = pathArg ? pathArg.split("=")[1] : "./src";

// Import patterns to replace
const importPatterns = [
  {
    // Replace theme variant types imported from context/theme-variants
    pattern:
      /import\s+\{([^}]*ThemeVariant[^}]*)\}\s+from\s+['"]@\/src\/context\/theme-variants['"]/g,
    replacement: "import {$1} from '@/src/types/theme'",
  },
  {
    // Replace theme variant types imported from types/theme-variants
    pattern:
      /import\s+\{([^}]*ThemeVariant[^}]*)\}\s+from\s+['"]@\/src\/types\/theme-variants['"]/g,
    replacement: "import {$1} from '@/src/types/theme'",
  },
  {
    // Replace getDefaultVariant import
    pattern:
      /import\s+\{([^}]*getDefaultVariant[^}]*)\}\s+from\s+['"]@\/src\/context\/theme-variants['"]/g,
    replacement: "import {$1} from '@/src/utils/theme-utils'",
  },
  {
    // Replace standardVariants/corporateVariants imports with STANDARD_VARIANTS/CORPORATE_VARIANTS
    pattern:
      /import\s+\{([^}]*)(standardVariants|corporateVariants)([^}]*)\}\s+from\s+['"]@\/src\/context\/theme-variants['"]/g,
    replacement: (match, before, varName, after) => {
      const constName =
        varName === "standardVariants"
          ? "STANDARD_VARIANTS"
          : "CORPORATE_VARIANTS";
      return `import {${before}${constName}${after}} from '@/src/constants/theme'`;
    },
  },
  {
    // Replace ExperienceType import from theme-variants
    pattern:
      /import\s+\{([^}]*ExperienceType[^}]*)\}\s+from\s+['"]@\/src\/types\/theme-variants['"]/g,
    replacement: "import {$1} from '@/src/types/theme'",
  },
  {
    // Replace ColorMode import from theme-variants
    pattern:
      /import\s+\{([^}]*ColorMode[^}]*)\}\s+from\s+['"]@\/src\/types\/theme-variants['"]/g,
    replacement: "import {$1} from '@/src/types/theme'",
  },
];

/**
 * Updates theme-related import statements in a file to use consolidated module paths.
 *
 * Skips files in `node_modules` and `.next` directories, and processes only `.ts`, `.tsx`, `.js`, and `.jsx` files. Applies a series of regex-based transformations to update legacy theme import statements. If changes are detected, either logs the file path (in dry-run mode) or writes the updated content back to the file.
 *
 * @param {string} filePath - The path to the file to process.
 */
function processFile(filePath) {
  // Skip node_modules and .next directories
  if (filePath.includes("node_modules") || filePath.includes(".next")) {
    return;
  }

  // Only process TypeScript and JavaScript files
  if (![".ts", ".tsx", ".js", ".jsx"].includes(path.extname(filePath))) {
    return;
  }

  // Read the file content
  let content;
  try {
    content = fs.readFileSync(filePath, "utf8");
  } catch (error) {
    console.error(`Error reading file ${filePath}:`, error);
    return;
  }

  // Apply replacements
  let newContent = content;
  let hasChanges = false;

  importPatterns.forEach(({ pattern, replacement }) => {
    const updatedContent = newContent.replace(pattern, (match) => {
      hasChanges = true;
      if (typeof replacement === "function") {
        return replacement(match);
      }
      return replacement;
    });

    if (updatedContent !== newContent) {
      newContent = updatedContent;
    }
  });

  // If there are changes, write them back or report them
  if (hasChanges) {
    if (dryRun) {
      console.log(`Would update: ${filePath}`);
    } else {
      try {
        fs.writeFileSync(filePath, newContent, "utf8");
        console.log(`Updated: ${filePath}`);
      } catch (error) {
        console.error(`Error writing to ${filePath}:`, error);
      }
    }
  }
}

/**
 * Recursively processes all files in a directory and its subdirectories.
 *
 * For each file found, calls {@link processFile} to apply import statement updates.
 * Skips no files or directories except as handled by {@link processFile}.
 *
 * @param {string} dirPath - The path to the directory to process.
 */
function processDirectory(dirPath) {
  const entries = fs.readdirSync(dirPath, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dirPath, entry.name);

    if (entry.isDirectory()) {
      processDirectory(fullPath);
    } else {
      processFile(fullPath);
    }
  }
}

// Main execution
console.log(`Scanning ${rootDir} for theme imports to update...`);
console.log(
  `Mode: ${dryRun ? "Dry run (no changes will be made)" : "Making changes"}`,
);

try {
  processDirectory(rootDir);
  console.log("Scan complete!");

  // Run TypeScript check if not in dry run mode
  if (!dryRun) {
    console.log("\nRunning TypeScript check to verify changes...");
    try {
      execSync("npx tsc --noEmit", { stdio: "inherit" });
      console.log("TypeScript check passed!");
    } catch (error) {
      console.error(
        "TypeScript check failed. You may need to manually fix some imports.",
      );
    }
  }
} catch (error) {
  console.error("Error processing files:", error);
}
