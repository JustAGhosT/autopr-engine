const chalk = require("chalk");
const glob = require("fast-glob");
const fs = require("fs");
const { exit } = require("process");

const CONFIG_FILES = [
  "config.kjson",
  ".aiguidance/context-providers.json",
  ".aiguidance/commands/*.json",
];

const violations = [];

/** Load and parse a JSON/JSONC file. */
function loadJson(file) {
  const raw = fs.readFileSync(file, "utf8");
  // strip simple // comments
  const cleaned = raw.replace(/\/\/.*$/gm, "");
  return JSON.parse(cleaned);
}

/** Rule 1 – Duplicate command names across files. */
function checkDuplicateCommands(objs, fileNames) {
  const map = new Map();
  objs.forEach((obj, idx) => {
    const cmds = obj.customCommands ?? [];
    cmds.forEach((c) => {
      const where = fileNames[idx];
      if (map.has(c.name)) {
        violations.push({
          file: where,
          message: `Duplicate command "${c.name}" also found in ${map.get(c.name)}`,
        });
      } else {
        map.set(c.name, where);
      }
    });
  });
}

/** Rule 2 – Token limits sanity check. */
function checkTokenLimits(obj, file) {
  const providers = obj.contextProviders ?? obj;
  const BIG = 20000;
  Object.entries(providers).forEach(([name, cfg]) => {
    if (cfg.maxTokens && cfg.maxTokens > BIG) {
      violations.push({
        file,
        message: `Provider "${name}" maxTokens=${cfg.maxTokens} is excessive (> ${BIG}).`,
      });
    }
  });
}

/** MAIN **/
(async () => {
  try {
    const files = (await glob(CONFIG_FILES)).sort();
    const jsonObjs = files.map(loadJson);

    checkDuplicateCommands(jsonObjs, files);
    files.forEach((file, i) => checkTokenLimits(jsonObjs[i], file));

    if (violations.length) {
      console.error(
        chalk.red(`✖ Found ${violations.length} AI-config violation(s):`),
      );
      violations.forEach((v) =>
        console.error(`${chalk.yellow(v.file)} → ${v.message}`),
      );
      exit(1);
    } else {
      console.log(chalk.green("✓ AI-config audit passed with no violations."));
    }
  } catch (error) {
    console.error(chalk.red("✖ Error running AI-config audit:"));
    console.error(error.message);
    exit(1);
  }
})();
