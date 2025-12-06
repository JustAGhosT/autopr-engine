# 21. Bot Exclusion System

## Status

Accepted

## Context

GitHub PRs often receive comments from multiple automated bots:
- Code review bots (CodeRabbit, Codacy, SonarCloud)
- Dependency bots (Dependabot, Renovate)
- CI/CD bots (GitHub Actions, Netlify, Vercel)
- AI assistants (Copilot, ChatGPT integrations)

When AutoPR's comment handler processes PR comments, it should not respond to or process comments from these bots, as this creates:
- Infinite loops (bot responding to bot)
- Noise in PR discussions
- Wasted API calls and compute
- Confusing user experience

### Requirements

1. **Default Exclusions**: Pre-configured list of common bots
2. **User Configuration**: Users can add/remove bots from their exclusion list
3. **Global vs Repository-Level**: Support both global and per-repo overrides
4. **Pattern Matching**: Support for `[bot]` suffix detection
5. **Comment History**: Track which comments were filtered for transparency
6. **Dashboard Management**: UI for managing exclusions

## Decision

We implement a **multi-layer bot exclusion system** with the following components:

### 1. Exclusion Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     Bot Comment                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Built-in Exclusions (hardcoded)                   │
│  - github-actions[bot], dependabot[bot], etc.               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Config File Exclusions (configs/config.yaml)      │
│  - Managed via YAML, versioned in repo                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: User Database Exclusions (per-user)               │
│  - Managed via Dashboard UI                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Repository Overrides (per-repo)                   │
│  - Can override global settings                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    [EXCLUDED] or [PROCESS]
```

### 2. Configuration Schema

#### Config File (configs/config.yaml)

```yaml
comment_analyzer:
  enabled: true

  bot_exclusions:
    enabled: true

    # Explicit username list
    excluded_users:
      - "github-actions[bot]"
      - "dependabot[bot]"
      - "renovate[bot]"
      - "coderabbitai[bot]"
      - "chatgpt-codex-connector[bot]"
      - "copilot[bot]"

    # Auto-exclude any username ending with [bot]
    exclude_bot_suffix: true

    # Regex patterns (optional, advanced)
    excluded_patterns:
      - ".*\\[bot\\]$"
      - "^bot-.*"
      - "^.*-bot$"
```

#### Database Schema

```sql
-- Global user exclusions
CREATE TABLE bot_exclusions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    username VARCHAR(255) NOT NULL,
    reason TEXT,
    source VARCHAR(50) DEFAULT 'user',  -- 'user', 'auto', 'default'
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, username)
);

-- Repository-level overrides
CREATE TABLE repository_bot_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id BIGINT NOT NULL,  -- GitHub repo ID
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    inherit_global BOOLEAN DEFAULT true,
    additional_exclusions JSONB DEFAULT '[]',
    removed_exclusions JSONB DEFAULT '[]',  -- Override global
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(repo_id, user_id)
);

-- Comment history for audit/display
CREATE TABLE bot_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id BIGINT NOT NULL,
    pr_number INT NOT NULL,
    comment_id BIGINT UNIQUE NOT NULL,
    bot_username VARCHAR(255) NOT NULL,
    body TEXT,
    was_excluded BOOLEAN DEFAULT true,
    exclusion_reason VARCHAR(100),  -- 'config', 'user', 'pattern', 'suffix'
    created_at TIMESTAMP NOT NULL,
    recorded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_bot_comments_repo ON bot_comments(repo_id);
CREATE INDEX idx_bot_comments_username ON bot_comments(bot_username);
CREATE INDEX idx_bot_comments_created ON bot_comments(created_at DESC);
```

### 3. Exclusion Check Algorithm

```python
# autopr/bots/exclusion_checker.py
from dataclasses import dataclass
from typing import Optional
import re

@dataclass
class ExclusionResult:
    excluded: bool
    reason: Optional[str] = None  # 'builtin', 'config', 'user', 'pattern', 'suffix'
    matched_rule: Optional[str] = None

class BotExclusionChecker:
    """Check if a username should be excluded from comment processing."""

    # Layer 1: Built-in exclusions (always applied)
    BUILTIN_EXCLUSIONS = {
        "github-actions[bot]",
        "dependabot[bot]",
        "dependabot-preview[bot]",
    }

    def __init__(self, config: dict, user_exclusions: list[str] = None):
        self.config = config
        self.user_exclusions = set(user_exclusions or [])
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        self.patterns = []
        patterns_config = self.config.get("excluded_patterns", [])
        for pattern in patterns_config:
            try:
                self.patterns.append(re.compile(pattern))
            except re.error:
                pass  # Skip invalid patterns

    def check(self, username: str, repo_settings: dict = None) -> ExclusionResult:
        """
        Check if username should be excluded.

        Args:
            username: GitHub username to check
            repo_settings: Optional repository-specific overrides

        Returns:
            ExclusionResult with excluded status and reason
        """
        # Layer 1: Built-in (always checked first)
        if username in self.BUILTIN_EXCLUSIONS:
            return ExclusionResult(True, "builtin", username)

        # Check if exclusions are enabled
        if not self.config.get("enabled", True):
            return ExclusionResult(False)

        # Layer 2: Config file exclusions
        config_exclusions = set(self.config.get("excluded_users", []))
        if username in config_exclusions:
            return ExclusionResult(True, "config", username)

        # Layer 3: User database exclusions
        if username in self.user_exclusions:
            return ExclusionResult(True, "user", username)

        # Layer 4: Repository overrides
        if repo_settings:
            # Check if removed from exclusions at repo level
            removed = set(repo_settings.get("removed_exclusions", []))
            if username in removed:
                return ExclusionResult(False)  # Explicitly allowed

            # Check additional repo-level exclusions
            additional = set(repo_settings.get("additional_exclusions", []))
            if username in additional:
                return ExclusionResult(True, "repo", username)

        # Pattern matching: [bot] suffix
        if self.config.get("exclude_bot_suffix", True):
            if username.endswith("[bot]"):
                return ExclusionResult(True, "suffix", "[bot] suffix")

        # Pattern matching: custom patterns
        for pattern in self.patterns:
            if pattern.match(username):
                return ExclusionResult(True, "pattern", pattern.pattern)

        return ExclusionResult(False)
```

### 4. GitHub Actions Integration

The exclusion check happens early in the workflow:

```yaml
# .github/workflows/pr-comment-handler.yml
- name: Check if commenter is excluded bot
  id: check_bot
  run: |
    COMMENTER="${{ github.event.comment.user.login }}"

    # Check config file
    BOT_EXCLUSIONS_ENABLED=$(yq '.comment_analyzer.bot_exclusions.enabled' configs/config.yaml)
    if [ "$BOT_EXCLUSIONS_ENABLED" != "true" ]; then
      echo "is_excluded=false" >> $GITHUB_OUTPUT
      exit 0
    fi

    # Check excluded users list
    if yq '.comment_analyzer.bot_exclusions.excluded_users[]' configs/config.yaml | grep -q "^${COMMENTER}$"; then
      echo "is_excluded=true" >> $GITHUB_OUTPUT
      exit 0
    fi

    # Check [bot] suffix
    if [[ "$COMMENTER" == *"[bot]" ]]; then
      EXCLUDE_SUFFIX=$(yq '.comment_analyzer.bot_exclusions.exclude_bot_suffix' configs/config.yaml)
      if [ "$EXCLUDE_SUFFIX" == "true" ]; then
        echo "is_excluded=true" >> $GITHUB_OUTPUT
        exit 0
      fi
    fi

    echo "is_excluded=false" >> $GITHUB_OUTPUT
```

### 5. Dashboard API

```python
# GET /api/bots/exclusions
{
  "data": [
    {"username": "coderabbitai[bot]", "source": "config", "reason": null},
    {"username": "my-custom-bot", "source": "user", "reason": "Too noisy"}
  ],
  "meta": {"total": 2}
}

# POST /api/bots/exclusions
{
  "username": "some-bot[bot]",
  "reason": "Creates duplicate comments"
}

# GET /api/bots/comments?excluded=true&limit=20
{
  "data": [
    {
      "id": "abc123",
      "bot_username": "coderabbitai[bot]",
      "repo": "owner/repo",
      "pr_number": 42,
      "body": "## Summary\n...",
      "exclusion_reason": "config",
      "created_at": "2025-12-06T10:00:00Z"
    }
  ]
}
```

### 6. Dashboard UI Components

```typescript
// Exclusion List Component
<BotExclusionList>
  <ExclusionItem
    username="coderabbitai[bot]"
    source="config"
    onRemove={() => removeExclusion(username)}
  />
  <AddExclusionButton onClick={openAddModal} />
</BotExclusionList>

// Recent Bot Comments
<BotCommentsList>
  <BotCommentCard
    bot="some-bot[bot]"
    body="..."
    excluded={false}
    onExclude={() => addExclusion(bot)}
  />
</BotCommentsList>
```

## Consequences

### Positive

- **Prevents Bot Loops**: Stops infinite comment chains
- **Reduces Noise**: Cleaner PR discussions
- **User Control**: Users can customize exclusions
- **Transparency**: Comment history shows what was filtered
- **Performance**: Early exit in workflow saves resources
- **Flexibility**: Multiple layers for different use cases

### Negative

- **Complexity**: Multiple layers to understand
- **Sync Issues**: Config file vs database can diverge
- **False Positives**: Might exclude legitimate bot comments
- **Maintenance**: Built-in list needs updates for new bots

### Neutral

- **Migration**: Existing users need to adopt new config
- **Documentation**: Need to explain exclusion precedence
- **Testing**: Need comprehensive test coverage

## Default Exclusion List

The following bots are excluded by default:

| Bot | Type | Reason |
|-----|------|--------|
| github-actions[bot] | CI/CD | Workflow notifications |
| dependabot[bot] | Dependencies | Auto-update PRs |
| renovate[bot] | Dependencies | Auto-update PRs |
| coderabbitai[bot] | Code Review | AI review comments |
| chatgpt-codex-connector[bot] | AI | ChatGPT integration |
| copilot[bot] | AI | GitHub Copilot |
| codacy[bot] | Code Quality | Static analysis |
| codecov[bot] | Coverage | Coverage reports |
| sonarcloud[bot] | Code Quality | SonarCloud analysis |
| snyk-bot | Security | Vulnerability scanning |
| imgbot[bot] | Optimization | Image compression |
| allcontributors[bot] | Community | Contributor recognition |
| stale[bot] | Maintenance | Stale issue management |
| mergify[bot] | Automation | Auto-merge |
| netlify[bot] | Deployment | Preview deployments |
| vercel[bot] | Deployment | Preview deployments |

## Related Decisions

- [ADR-0008: Event-Driven Architecture](0008-event-driven-architecture.md)
- [ADR-0020: Dashboard API Design](0020-dashboard-api-design.md)
