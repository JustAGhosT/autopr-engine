---
trigger: model_decision
description: For AutoPR-Engine and Python repos
---

# Workspace Rules – autopr-engine

## Context & Goal

- This repo powers automated PR creation/maintenance across many VV/JustAGhosT repos.
- Priorities: determinism, idempotence, clear diffs, zero surprise merges.

## Stack & Runtime

- Language: TypeScript (Node ≥18). Strict TS config, no `any`.
- CLI-first design: every feature callable non-interactively (CI friendly).
- Package manager: pnpm (preferred) or npm – pick one and lock it. Don’t mix.

## Project Structure

- `src/core/` – pure logic (diff calc, rule parsing, repo scanning). No IO here.
- `src/adapters/` – GitHub, GitLab, Azure DevOps clients. Wrap octokit, don’t scatter API calls.
- `src/rules/` – rule/loaders for autopr recipes (JSON/YAML). One rule = one file.
- `src/cli/` – thin commander/yargs layer. Only parse args & call core.
- `tests/` mirrors src structure (unit first, E2E separately).
- No circular deps. Run madge in CI to enforce.

## Config & Secrets

- All tokens/keys via env vars or GH Actions secrets. Never hardcode.
- Config precedence: CLI flag > env var > config file. Document defaults.
- Support a local `.autopr.json` but ignore it in git (`.gitignore`).

## Git & PR Behaviour

- PR titles follow Conventional Commits (`feat:`, `fix:`, etc.) unless rule overrides.
- Never force-push on user branches; create/update bot branches (`autopr/<rule>/<hash>`).
- Comment in PR with a summary of changes, linked rule, and dry-run diff.
- Respect CODEOWNERS: request reviews automatically; don’t auto-merge unless rule explicitly says
  so.
- Idempotent reruns: second run on unchanged repo must be no-op.

## Diff / File Ops

- Don’t regenerate files that didn’t change (no churn). Compare content hash before write.
- Preserve user sections marked with `// <keep>` … `// </keep>`.
- For templated files, expose variables at top; don’t bury magic strings.

## Error Handling & Logging

- Fail fast with clear, actionable messages. Include repo/name + rule id.
- Structured logs (JSON) in CI mode; pretty logs locally.
- Retry transient HTTP errors (429/5xx) with exponential backoff.

## Testing & QA

- Unit test every rule transformer. Snapshot-test generated files.
- Mock GitHub API (nock/msw). No live calls in unit tests.
- E2E tests can hit a sandbox repo (separate org) – clean up after.
- Coverage >80% on core logic. Don’t chase 100% if it means trash tests.

## Performance & Cost

- Batch API calls; prefer GraphQL when faster. Respect rate limits.
- Cache repo metadata per run. Don’t refetch unless stale.
- Keep dependencies lean; prefer stdlib/utility functions over heavy libs.

## CI/CD

- GitHub Actions workflow: lint → test → build → dry-run → publish (npm) / release.
- Lint: ESLint + Prettier. No failing warnings in main.
- Automatically update CLI help (`--help`) docs in README on version bump.

## DX & Docs

- `README.md` = entry point: quick start, flags, config schema, examples.
- Add `--dry-run` everywhere. Default to dry-run when unsafe.
- Provide `--rule <name>` and `--rule-dir` flags for selective runs.

## When Cascade Helps

- Reference these rules explicitly in code changes (“per autopr-engine rule XYZ…”).
- Ask before touching CI files, LICENSEs, or SECURITY.md.
- If unsure about a repo’s intent, open an issue draft instead of a PR.
