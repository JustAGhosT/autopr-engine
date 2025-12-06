# AutoPR Dashboard - Product Requirements Document

> **Version:** 1.0
> **Date:** December 2025
> **Status:** Draft

---

## 1. Executive Summary

### 1.1 Product Overview
The AutoPR Dashboard is a web-based application at **app.autopr.io** that provides users with a complete interface to manage their AI-powered GitHub PR automation. It complements the marketing website at **autopr.io**.

### 1.2 Website Architecture

| Domain | Purpose | Tech Stack | Status |
|--------|---------|------------|--------|
| **autopr.io** | Marketing, docs, landing pages | Next.js, Tailwind | Exists |
| **app.autopr.io** | Dashboard, user management, API | FastAPI + React | To Build |

### 1.3 Goals
- Provide a user-friendly interface for managing AutoPR installations
- Enable real-time monitoring of PR automation activities
- Allow configuration of bot exclusions, workflows, and integrations
- Support multi-repository and multi-organization management

---

## 2. User Personas

### 2.1 Primary: Developer/DevOps Engineer
- **Needs:** Quick setup, minimal configuration, automated workflows
- **Pain Points:** Too many bots commenting, noisy PRs, manual issue creation
- **Goals:** Streamline PR reviews, reduce noise, automate repetitive tasks

### 2.2 Secondary: Engineering Manager
- **Needs:** Team-wide visibility, metrics, compliance
- **Pain Points:** Lack of visibility into PR review quality, inconsistent processes
- **Goals:** Standardize PR workflows, track team performance

### 2.3 Tertiary: Open Source Maintainer
- **Needs:** Free tier, bot management, community contribution handling
- **Pain Points:** Bot spam, managing multiple contributors, issue triage
- **Goals:** Efficient issue/PR management, contributor experience

---

## 3. Feature Requirements

### 3.1 Authentication & Authorization

#### 3.1.1 GitHub OAuth Login
- **Priority:** P0 (Critical)
- **Description:** Users authenticate via GitHub OAuth through the GitHub App
- **Requirements:**
  - [ ] GitHub OAuth 2.0 flow integration
  - [ ] Session management (JWT tokens)
  - [ ] Secure token storage (encrypted, HttpOnly cookies)
  - [ ] Auto-refresh of expired tokens
  - [ ] Logout functionality

#### 3.1.2 User Roles & Permissions
- **Priority:** P1 (High)
- **Description:** Role-based access control for team features
- **Roles:**
  | Role | Permissions |
  |------|-------------|
  | Owner | Full access, billing, delete org |
  | Admin | Manage repos, settings, users |
  | Member | View, configure assigned repos |
  | Viewer | Read-only access |

---

### 3.2 Dashboard Home

#### 3.2.1 Overview Cards
- **Priority:** P0
- **Metrics displayed:**
  - Total PRs processed (24h / 7d / 30d)
  - Issues auto-created
  - Bot comments filtered
  - System health status
  - Active workflows count

#### 3.2.2 Activity Feed
- **Priority:** P0
- **Description:** Real-time feed of recent AutoPR actions
- **Features:**
  - Chronological list of events
  - Filter by repo, action type, status
  - Click to view details
  - Pagination with infinite scroll

#### 3.2.3 Quick Actions
- **Priority:** P1
- **Actions:**
  - Run quality check on repo
  - Trigger workflow manually
  - Add/remove bot from exclusions
  - View API documentation

---

### 3.3 Repository Management

#### 3.3.1 Repository List
- **Priority:** P0
- **Features:**
  - View all repos where GitHub App is installed
  - Filter by organization/owner
  - Search by repo name
  - Sort by activity, name, date added
  - Show status indicators (active, paused, error)

#### 3.3.2 Repository Settings (per repo)
- **Priority:** P1
- **Settings:**
  - Enable/disable AutoPR for this repo
  - Select active workflows
  - Configure quality check modes
  - Set notification preferences
  - Custom bot exclusions (repo-level override)

#### 3.3.3 Add New Repository
- **Priority:** P0
- **Flow:**
  1. Click "Add Repository"
  2. Redirect to GitHub App installation
  3. Select repositories to install
  4. Return to dashboard with new repos

---

### 3.4 Bot Management

#### 3.4.1 Bot Exclusion List
- **Priority:** P0
- **Features:**
  - View currently excluded bots
  - Global exclusions vs repo-specific
  - Toggle "exclude all [bot] suffix" option
  - Add bot by username
  - Remove bot from exclusion

#### 3.4.2 Bot Comment History
- **Priority:** P1
- **Features:**
  - View recent comments from bots
  - Filter by bot, repo, date
  - One-click "Exclude this bot" action
  - Show which bots are most active
  - Preview comment content

#### 3.4.3 Bot Analytics
- **Priority:** P2
- **Metrics:**
  - Comments per bot (chart)
  - Most active bots this week
  - Filtered vs processed ratio

---

### 3.5 Workflow Management

#### 3.5.1 Active Workflows
- **Priority:** P1
- **Features:**
  - List all configured workflows
  - Show trigger conditions
  - Enable/disable toggle
  - View execution history

#### 3.5.2 Workflow History
- **Priority:** P1
- **Features:**
  - Execution logs with timestamps
  - Success/failure status
  - Duration metrics
  - Filter by workflow, status, date
  - Retry failed executions

#### 3.5.3 Workflow Builder (Future)
- **Priority:** P3
- **Description:** Visual drag-and-drop workflow editor
- **Deferred to Phase 2**

---

### 3.6 Integrations

#### 3.6.1 Integration Status
- **Priority:** P1
- **Integrations:**
  | Integration | Status | Configuration |
  |-------------|--------|---------------|
  | GitHub | Always connected | Via GitHub App |
  | Slack | Optional | Webhook URL |
  | Linear | Optional | API Key + Team ID |
  | Discord | Optional | Webhook URL |
  | Jira | Optional | API Token + Domain |

#### 3.6.2 Integration Configuration
- **Priority:** P1
- **Features:**
  - Connect/disconnect integrations
  - Test connection button
  - Configure notification channels
  - Map workflows to integrations

---

### 3.7 Settings

#### 3.7.1 General Settings
- **Priority:** P1
- **Options:**
  - Default quality mode (ultra-fast, fast, smart, comprehensive, ai-enhanced)
  - Auto-fix enabled/disabled
  - Notification preferences
  - Timezone

#### 3.7.2 API Keys
- **Priority:** P1
- **Features:**
  - Generate API keys for CLI/automation
  - View/revoke existing keys
  - Set key expiration
  - Scope permissions per key

#### 3.7.3 Billing (Future)
- **Priority:** P3
- **Deferred to monetization phase**

---

### 3.8 Analytics & Reporting

#### 3.8.1 Dashboard Analytics
- **Priority:** P2
- **Charts:**
  - PRs processed over time
  - Issues created trend
  - Response time metrics
  - Bot filter effectiveness

#### 3.8.2 Export & Reports
- **Priority:** P3
- **Features:**
  - Export CSV of activity
  - Weekly summary emails
  - Custom date range reports

---

## 4. Technical Architecture

### 4.1 System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         app.autopr.io                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   React SPA  │    │  FastAPI     │    │  PostgreSQL  │      │
│  │   (Frontend) │◄──►│  (Backend)   │◄──►│  (Database)  │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                                    │
│         │                   ▼                                    │
│         │            ┌──────────────┐                           │
│         │            │    Redis     │                           │
│         │            │  (Sessions)  │                           │
│         │            └──────────────┘                           │
│         │                   │                                    │
│         ▼                   ▼                                    │
│  ┌─────────────────────────────────────┐                        │
│  │           GitHub API                 │                        │
│  │  (App Installations, Webhooks)       │                        │
│  └─────────────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Frontend Stack
- **Framework:** React 18+ with TypeScript
- **Styling:** Tailwind CSS + shadcn/ui (match website)
- **State:** React Query (TanStack Query) for server state
- **Routing:** React Router v6
- **Build:** Vite

### 4.3 Backend Stack
- **Framework:** FastAPI (existing)
- **Auth:** GitHub OAuth + JWT sessions
- **Database:** PostgreSQL (existing Alembic setup)
- **Cache/Sessions:** Redis
- **Background Jobs:** Celery or FastAPI BackgroundTasks

### 4.4 API Design

#### 4.4.1 Authentication Endpoints
```
POST   /api/auth/github/login     # Initiate GitHub OAuth
GET    /api/auth/github/callback  # OAuth callback
POST   /api/auth/logout           # Logout
GET    /api/auth/me               # Current user info
POST   /api/auth/refresh          # Refresh token
```

#### 4.4.2 Repository Endpoints
```
GET    /api/repos                 # List user's repos
GET    /api/repos/:id             # Get repo details
PATCH  /api/repos/:id             # Update repo settings
POST   /api/repos/:id/enable      # Enable AutoPR
POST   /api/repos/:id/disable     # Disable AutoPR
```

#### 4.4.3 Bot Management Endpoints
```
GET    /api/bots/exclusions       # List excluded bots
POST   /api/bots/exclusions       # Add bot to exclusions
DELETE /api/bots/exclusions/:user # Remove bot
GET    /api/bots/comments         # Recent bot comments
GET    /api/bots/analytics        # Bot activity stats
```

#### 4.4.4 Workflow Endpoints
```
GET    /api/workflows             # List workflows
GET    /api/workflows/:id         # Get workflow details
PATCH  /api/workflows/:id         # Update workflow
GET    /api/workflows/:id/history # Execution history
POST   /api/workflows/:id/run     # Manual trigger
```

#### 4.4.5 Settings Endpoints
```
GET    /api/settings              # Get user settings
PATCH  /api/settings              # Update settings
GET    /api/settings/api-keys     # List API keys
POST   /api/settings/api-keys     # Create API key
DELETE /api/settings/api-keys/:id # Revoke API key
```

---

## 5. Database Schema Additions

### 5.1 New Tables

```sql
-- User sessions and preferences
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    github_id BIGINT UNIQUE NOT NULL,
    github_login VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    avatar_url TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Organization-level settings
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    github_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- User's role in organization
CREATE TABLE user_organizations (
    user_id UUID REFERENCES users(id),
    org_id UUID REFERENCES organizations(id),
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    PRIMARY KEY (user_id, org_id)
);

-- Repository settings (extends GitHub App installation)
CREATE TABLE repository_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    github_repo_id BIGINT UNIQUE NOT NULL,
    owner VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    enabled BOOLEAN DEFAULT true,
    settings JSONB DEFAULT '{}',
    bot_exclusions JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Bot exclusions (global)
CREATE TABLE bot_exclusions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    username VARCHAR(255) NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, username)
);

-- Bot comment history (for display)
CREATE TABLE bot_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id BIGINT NOT NULL,
    pr_number INT NOT NULL,
    comment_id BIGINT NOT NULL,
    bot_username VARCHAR(255) NOT NULL,
    body TEXT,
    created_at TIMESTAMP NOT NULL,
    was_excluded BOOLEAN DEFAULT false,
    INDEX idx_bot_comments_bot (bot_username),
    INDEX idx_bot_comments_repo (repo_id)
);

-- API keys for programmatic access
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    scopes JSONB DEFAULT '[]',
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Workflow execution history
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id VARCHAR(255) NOT NULL,
    repo_id BIGINT NOT NULL,
    status VARCHAR(50) NOT NULL,
    trigger_type VARCHAR(50) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_ms INT,
    result JSONB,
    error TEXT
);
```

---

## 6. UI/UX Design

### 6.1 Design System
- **Inherit from marketing site** (autopr.io)
- **Colors:** Purple/blue gradient primary, slate grays
- **Typography:** System fonts (Inter or similar)
- **Components:** shadcn/ui library
- **Dark mode:** Support required

### 6.2 Page Structure

```
┌─────────────────────────────────────────────────────────────┐
│  Logo    [Dashboard] [Repos] [Bots] [Workflows] [Settings]  │  ← Header
├─────────────────────────────────────────────────────────────┤
│  ┌───────────┐  ┌─────────────────────────────────────────┐ │
│  │           │  │                                         │ │
│  │  Sidebar  │  │              Main Content               │ │
│  │  (Nav)    │  │                                         │ │
│  │           │  │                                         │ │
│  │           │  │                                         │ │
│  └───────────┘  └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 Key Pages

#### Dashboard (/)
- 4 stat cards at top
- Activity feed (center)
- Quick actions panel (right)

#### Repositories (/repos)
- Search/filter bar
- Card or table view toggle
- Repo cards with status badges

#### Bot Management (/bots)
- Tab: Exclusion List
- Tab: Recent Comments
- Tab: Analytics

#### Settings (/settings)
- Tab: General
- Tab: Integrations
- Tab: API Keys
- Tab: Account

---

## 7. Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Set up React frontend project
- [ ] Implement GitHub OAuth flow
- [ ] Create user/session management
- [ ] Build dashboard home with basic stats
- [ ] Deploy to app.autopr.io

### Phase 2: Core Features (Week 3-4)
- [ ] Repository list and management
- [ ] Bot exclusion management (CRUD)
- [ ] Bot comment viewing
- [ ] Basic settings page

### Phase 3: Workflows & Integrations (Week 5-6)
- [ ] Workflow list and history
- [ ] Integration status page
- [ ] Activity feed with filtering
- [ ] Analytics charts

### Phase 4: Polish & Advanced (Week 7-8)
- [ ] API key management
- [ ] Advanced filtering/search
- [ ] Export functionality
- [ ] Performance optimization
- [ ] Mobile responsiveness

---

## 8. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| User activation | 50% of installs create account | Analytics |
| Daily active users | 30% of registered users | Analytics |
| Bot exclusion usage | 70% configure exclusions | Database |
| Time to first value | < 5 minutes from signup | User tracking |
| Page load time | < 2 seconds | Performance monitoring |
| Error rate | < 1% of API requests | Logging |

---

## 9. Security Considerations

### 9.1 Authentication
- GitHub OAuth only (no password management)
- JWT tokens with short expiry (15 min) + refresh tokens
- Secure cookie storage (HttpOnly, SameSite, Secure)

### 9.2 Authorization
- All API calls verify user owns/has access to resource
- Rate limiting per user (100 requests/min)
- Audit logging for sensitive actions

### 9.3 Data Protection
- Encrypt sensitive data at rest (API keys, tokens)
- No storage of GitHub access tokens (use App installation tokens)
- GDPR compliance (data export, deletion)

---

## 10. Open Questions

1. **Pricing Model:** Free tier limits? Pro features?
2. **Multi-org Support:** Can users belong to multiple orgs?
3. **Self-hosted Option:** Should we support on-premise deployment?
4. **API Rate Limits:** What limits for API key usage?
5. **Data Retention:** How long to keep execution history?

---

## 11. Appendix

### A. Existing Infrastructure
- FastAPI server: `autopr/server.py`
- GitHub App handlers: `autopr/integrations/github_app/`
- Database models: `autopr/database/models.py`
- Security/auth: `autopr/security/`

### B. Related Documents
- [GitHub App Setup](../GITHUB_APP_SETUP.md)
- [API Documentation](../api/API_DOCUMENTATION.md)
- [Security Best Practices](../security/SECURITY_BEST_PRACTICES.md)

### C. References
- [GitHub OAuth Apps](https://docs.github.com/en/apps/oauth-apps)
- [GitHub Apps Installation](https://docs.github.com/en/apps/creating-github-apps)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
