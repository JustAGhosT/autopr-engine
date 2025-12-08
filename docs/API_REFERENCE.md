# AutoPR Engine API Reference

**Version:** 1.0.1  
**Last Updated:** 2025-11-22  
**Base URL:** `http://localhost:8080` (Dashboard), `http://localhost:8000` (FastAPI)

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Rate Limiting](#rate-limiting)
4. [Error Handling](#error-handling)
5. [Dashboard API](#dashboard-api)
6. [Workflow API](#workflow-api)
7. [Quality Engine API](#quality-engine-api)
8. [WebSocket API](#websocket-api)
9. [Request/Response Schemas](#request-response-schemas)
10. [Status Codes](#status-codes)
11. [Examples](#examples)

---

## Overview

AutoPR Engine provides RESTful APIs for:
- **Dashboard Operations:** Monitoring, metrics, and system health
- **Workflow Management:** Creating, executing, and monitoring workflows
- **Quality Analysis:** Code quality checks and AI-powered reviews
- **Real-time Updates:** WebSocket connections for live data streams

### API Architecture

```
┌──────────────┐
│   Client     │
└──────┬───────┘
       │
       ├─── HTTP/REST ───> Dashboard API (Flask, Port 8080)
       │                   └── Metrics, Health, File Operations
       │
       ├─── HTTP/REST ───> Workflow API (FastAPI, Port 8000)
       │                   └── Workflow CRUD, Execution, Validation
       │
       └─── WebSocket ───> Real-time API (Port 8080)
                            └── Live updates, streaming logs
```

---

## Authentication

### GitHub Token Authentication

Most API endpoints require GitHub token authentication for security.

**Header:**
```http
Authorization: Bearer ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Token Requirements:**
- Valid GitHub Personal Access Token (PAT)
- Required scopes: `repo`, `workflow`, `read:org`
- Token format: `ghp_` prefix followed by alphanumeric string

**Example:**
```bash
curl -H "Authorization: Bearer ghp_abc123..." \
     http://localhost:8080/api/workflows
```

### Token Validation

Tokens are validated on each request:
- Format validation (regex pattern)
- Scope verification
- Expiration check
- Rate limit association

**Error Response (Invalid Token):**
```json
{
  "error": "AuthenticationError",
  "message": "Invalid GitHub token format",
  "status_code": 401,
  "timestamp": "2025-11-22T18:00:00Z"
}
```

---

## Rate Limiting

### Rate Limit Configuration

**Default Limits:**
- **Anonymous:** 60 requests/hour
- **Authenticated:** 5,000 requests/hour
- **Burst:** 100 requests/minute

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 5000
X-RateLimit-Remaining: 4999
X-RateLimit-Reset: 1732291200
X-RateLimit-Retry-After: 3600
```

### Rate Limit Exceeded Response

**Status Code:** `429 Too Many Requests`

**Response Body:**
```json
{
  "error": "RateLimitError",
  "message": "Rate limit exceeded",
  "retry_after": 3600,
  "limit": 5000,
  "remaining": 0,
  "reset_at": "2025-11-22T19:00:00Z"
}
```

**Handling Rate Limits:**
```python
import time
import requests

response = requests.get(url, headers=headers)
if response.status_code == 429:
    retry_after = int(response.headers.get('X-RateLimit-Retry-After', 60))
    time.sleep(retry_after)
    response = requests.get(url, headers=headers)
```

---

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "error": "ErrorType",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional context"
  },
  "status_code": 400,
  "timestamp": "2025-11-22T18:00:00Z",
  "request_id": "req_abc123"
}
```

### Error Types

| Error Type | Status Code | Description |
|------------|-------------|-------------|
| `ValidationError` | 400 | Invalid request parameters or body |
| `AuthenticationError` | 401 | Missing or invalid authentication |
| `AuthorizationError` | 403 | Insufficient permissions |
| `NotFoundError` | 404 | Resource not found |
| `ConflictError` | 409 | Resource conflict (e.g., duplicate) |
| `RateLimitError` | 429 | Rate limit exceeded |
| `InternalServerError` | 500 | Server-side error |
| `ServiceUnavailableError` | 503 | Service temporarily unavailable |

### Sensitive Information Protection

**Security Note:** All error messages are automatically sanitized to prevent information leakage:
- Database credentials → `postgresql://[REDACTED]`
- API keys → `ghp_[REDACTED]` or `sk-[REDACTED]`
- File paths → `[FILE_PATH]`
- Email addresses → `[EMAIL_REDACTED]`
- IP addresses → `[IP_REDACTED]`
- SQL queries → `[QUERY_REDACTED]`

---

## Dashboard API

### Base Endpoints

#### GET /api/health

Check system health status.

**Request:**
```http
GET /api/health HTTP/1.1
Host: localhost:8080
```

**Response:**
```json
{
  "status": "healthy",
  "uptime": 3600,
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "workflow_engine": "healthy"
  },
  "timestamp": "2025-11-22T18:00:00Z"
}
```

**Status Codes:**
- `200` - System healthy
- `503` - System unhealthy

---

#### GET /api/metrics

Retrieve system metrics and statistics.

**Request:**
```http
GET /api/metrics HTTP/1.1
Host: localhost:8080
Authorization: Bearer ghp_abc123...
```

**Response:**
```json
{
  "start_time": "2025-11-22T17:00:00Z",
  "uptime_seconds": 3600,
  "total_checks": 1543,
  "total_issues": 87,
  "success_rate": 94.36,
  "average_processing_time": 2.34,
  "recent_activity": [
    {
      "timestamp": "2025-11-22T17:59:00Z",
      "type": "workflow_execution",
      "workflow_id": "wf_123",
      "status": "completed",
      "duration": 1.23
    }
  ],
  "quality_stats": {
    "ultra_fast": {"count": 450, "avg_time": 0.5},
    "fast": {"count": 380, "avg_time": 1.2},
    "smart": {"count": 290, "avg_time": 2.8},
    "comprehensive": {"count": 200, "avg_time": 5.4},
    "ai_enhanced": {"count": 223, "avg_time": 8.7}
  }
}
```

**Status Codes:**
- `200` - Metrics retrieved successfully
- `401` - Authentication required
- `500` - Server error

---

#### GET /api/files

List files in a directory (with security validation).

**Request:**
```http
GET /api/files?path=/home/user/projects HTTP/1.1
Host: localhost:8080
Authorization: Bearer ghp_abc123...
```

**Query Parameters:**
- `path` (required): Directory path to list

**Response:**
```json
{
  "path": "/home/user/projects",
  "files": [
    {
      "name": "project1",
      "type": "directory",
      "size": null,
      "modified": "2025-11-20T10:30:00Z"
    },
    {
      "name": "README.md",
      "type": "file",
      "size": 2048,
      "modified": "2025-11-22T15:00:00Z"
    }
  ],
  "total_count": 2
}
```

**Security:**
- Path traversal protection (validates against allowed directories)
- Symlink escape prevention
- Canonical path resolution

**Status Codes:**
- `200` - Files listed successfully
- `400` - Invalid path or path traversal attempt
- `401` - Authentication required
- `403` - Path not in allowed directories
- `404` - Directory not found

---

#### POST /api/quality/check

Run quality analysis on code.

**Request:**
```http
POST /api/quality/check HTTP/1.1
Host: localhost:8080
Authorization: Bearer ghp_abc123...
Content-Type: application/json

{
  "mode": "smart",
  "files": [
    "/path/to/file1.py",
    "/path/to/file2.py"
  ],
  "options": {
    "include_ai_suggestions": true,
    "severity_threshold": "medium"
  }
}
```

**Request Body:**
```typescript
{
  mode: "ultra_fast" | "fast" | "smart" | "comprehensive" | "ai_enhanced"
  files: string[]
  options?: {
    include_ai_suggestions?: boolean
    severity_threshold?: "low" | "medium" | "high" | "critical"
    max_issues?: number
  }
}
```

**Response:**
```json
{
  "check_id": "qc_abc123",
  "mode": "smart",
  "status": "completed",
  "duration": 2.34,
  "summary": {
    "total_files": 2,
    "total_issues": 7,
    "by_severity": {
      "critical": 1,
      "high": 2,
      "medium": 3,
      "low": 1
    }
  },
  "issues": [
    {
      "file": "/path/to/file1.py",
      "line": 42,
      "severity": "high",
      "type": "security",
      "message": "SQL injection vulnerability detected",
      "suggestion": "Use parameterized queries"
    }
  ],
  "ai_suggestions": [
    {
      "type": "refactoring",
      "confidence": 0.92,
      "description": "Consider extracting method 'calculate_total'"
    }
  ]
}
```

**Quality Modes:**
- `ultra_fast`: Basic syntax and lint checks (~0.5s)
- `fast`: + Style and complexity checks (~1.2s)
- `smart`: + Security and bug detection (~2.8s)
- `comprehensive`: + Deep analysis and patterns (~5.4s)
- `ai_enhanced`: + AI-powered suggestions (~8.7s)

**Status Codes:**
- `200` - Quality check completed
- `202` - Quality check started (async)
- `400` - Invalid request parameters
- `401` - Authentication required
- `429` - Rate limit exceeded

---

## Workflow API

### Workflow Management

#### POST /workflows/

Create a new workflow.

**Request:**
```http
POST /workflows/ HTTP/1.1
Host: localhost:8000
Authorization: Bearer ghp_abc123...
Content-Type: application/json

{
  "name": "PR Analysis Workflow",
  "description": "Automated PR analysis and issue creation",
  "trigger": "pull_request",
  "steps": [
    {
      "id": "analyze",
      "type": "ai_analysis",
      "config": {
        "provider": "openai",
        "model": "gpt-4"
      }
    },
    {
      "id": "create_issues",
      "type": "issue_creation",
      "depends_on": ["analyze"]
    }
  ],
  "config": {
    "timeout": 300,
    "retry_on_failure": true,
    "max_retries": 3
  }
}
```

**Request Schema:**
```typescript
{
  name: string                    // 1-100 characters
  description?: string            // Optional description
  trigger: "pull_request" | "push" | "manual" | "schedule"
  steps: WorkflowStep[]
  config?: {
    timeout?: number              // Seconds, max 3600
    retry_on_failure?: boolean
    max_retries?: number          // 0-5
    parallel?: boolean
  }
}

interface WorkflowStep {
  id: string                      // Unique within workflow
  type: string                    // Step type identifier
  config: Record<string, any>     // Step-specific configuration
  depends_on?: string[]           // Step IDs this depends on
}
```

**Response:**
```json
{
  "workflow_id": "wf_abc123",
  "name": "PR Analysis Workflow",
  "status": "created",
  "created_at": "2025-11-22T18:00:00Z",
  "trigger": "pull_request",
  "steps_count": 2,
  "validation": {
    "valid": true,
    "errors": []
  }
}
```

**Validation Rules:**
- Workflow name: 1-100 characters, alphanumeric + spaces/hyphens
- Step IDs must be unique within workflow
- Circular dependencies not allowed
- Maximum 50 steps per workflow
- Maximum 10,000 characters for entire workflow config

**Status Codes:**
- `201` - Workflow created successfully
- `400` - Validation error
- `401` - Authentication required
- `409` - Workflow with same name exists

---

#### GET /workflows/{workflow_id}

Retrieve workflow details.

**Request:**
```http
GET /workflows/wf_abc123 HTTP/1.1
Host: localhost:8000
Authorization: Bearer ghp_abc123...
```

**Response:**
```json
{
  "workflow_id": "wf_abc123",
  "name": "PR Analysis Workflow",
  "description": "Automated PR analysis and issue creation",
  "status": "active",
  "created_at": "2025-11-22T18:00:00Z",
  "updated_at": "2025-11-22T18:00:00Z",
  "trigger": "pull_request",
  "steps": [
    {
      "id": "analyze",
      "type": "ai_analysis",
      "config": {
        "provider": "openai",
        "model": "gpt-4"
      },
      "status": "configured"
    }
  ],
  "config": {
    "timeout": 300,
    "retry_on_failure": true,
    "max_retries": 3
  },
  "executions": {
    "total": 42,
    "successful": 39,
    "failed": 3,
    "success_rate": 92.86
  }
}
```

**Status Codes:**
- `200` - Workflow retrieved successfully
- `401` - Authentication required
- `404` - Workflow not found

---

#### POST /workflows/{workflow_id}/nodes

Add a node/step to an existing workflow.

**Request:**
```http
POST /workflows/wf_abc123/nodes HTTP/1.1
Host: localhost:8000
Authorization: Bearer ghp_abc123...
Content-Type: application/json

{
  "id": "notify",
  "type": "slack_notification",
  "config": {
    "webhook_url": "https://hooks.slack.com/...",
    "channel": "#pr-notifications"
  },
  "depends_on": ["create_issues"],
  "position": "after"
}
```

**Response:**
```json
{
  "workflow_id": "wf_abc123",
  "node_id": "notify",
  "status": "added",
  "updated_at": "2025-11-22T18:05:00Z",
  "validation": {
    "valid": true,
    "warnings": []
  }
}
```

**Status Codes:**
- `201` - Node added successfully
- `400` - Validation error
- `401` - Authentication required
- `404` - Workflow not found
- `409` - Node ID already exists

---

#### POST /workflows/{workflow_id}/validate

Validate workflow configuration.

**Request:**
```http
POST /workflows/wf_abc123/validate HTTP/1.1
Host: localhost:8000
Authorization: Bearer ghp_abc123...
```

**Response (Valid):**
```json
{
  "workflow_id": "wf_abc123",
  "valid": true,
  "checks": {
    "structure": "passed",
    "dependencies": "passed",
    "configuration": "passed",
    "security": "passed"
  },
  "warnings": [],
  "timestamp": "2025-11-22T18:00:00Z"
}
```

**Response (Invalid):**
```json
{
  "workflow_id": "wf_abc123",
  "valid": false,
  "checks": {
    "structure": "passed",
    "dependencies": "failed",
    "configuration": "passed",
    "security": "passed"
  },
  "errors": [
    {
      "type": "circular_dependency",
      "message": "Circular dependency detected: step_a -> step_b -> step_a",
      "steps": ["step_a", "step_b"]
    }
  ],
  "warnings": [
    {
      "type": "performance",
      "message": "High timeout value may impact system resources",
      "step": "analyze"
    }
  ],
  "timestamp": "2025-11-22T18:00:00Z"
}
```

**Validation Checks:**
1. **Structure:** Valid JSON, required fields present
2. **Dependencies:** No circular dependencies, all referenced steps exist
3. **Configuration:** Valid config values, within limits
4. **Security:** No sensitive data in config, valid credentials

**Status Codes:**
- `200` - Validation completed (check `valid` field)
- `401` - Authentication required
- `404` - Workflow not found

---

#### POST /workflows/{workflow_id}/execute

Execute a workflow.

**Request:**
```http
POST /workflows/wf_abc123/execute HTTP/1.1
Host: localhost:8000
Authorization: Bearer ghp_abc123...
Content-Type: application/json

{
  "context": {
    "pr_number": 42,
    "repository": "owner/repo",
    "base_branch": "main",
    "head_branch": "feature/new-feature"
  },
  "parameters": {
    "skip_tests": false,
    "notify_on_completion": true
  }
}
```

**Response (Async):**
```json
{
  "execution_id": "exec_xyz789",
  "workflow_id": "wf_abc123",
  "status": "queued",
  "started_at": "2025-11-22T18:00:00Z",
  "estimated_duration": 45,
  "context": {
    "pr_number": 42,
    "repository": "owner/repo"
  }
}
```

**Status Codes:**
- `202` - Execution started (async)
- `400` - Invalid context or parameters
- `401` - Authentication required
- `404` - Workflow not found
- `429` - Rate limit exceeded

---

#### GET /workflows/{workflow_id}/executions/{execution_id}

Get execution status and results.

**Request:**
```http
GET /workflows/wf_abc123/executions/exec_xyz789 HTTP/1.1
Host: localhost:8000
Authorization: Bearer ghp_abc123...
```

**Response (In Progress):**
```json
{
  "execution_id": "exec_xyz789",
  "workflow_id": "wf_abc123",
  "status": "running",
  "started_at": "2025-11-22T18:00:00Z",
  "current_step": "analyze",
  "completed_steps": [],
  "progress": 25,
  "estimated_remaining": 34
}
```

**Response (Completed):**
```json
{
  "execution_id": "exec_xyz789",
  "workflow_id": "wf_abc123",
  "status": "completed",
  "started_at": "2025-11-22T18:00:00Z",
  "completed_at": "2025-11-22T18:00:45Z",
  "duration": 45.2,
  "steps": [
    {
      "id": "analyze",
      "status": "completed",
      "duration": 23.4,
      "output": {
        "issues_found": 7,
        "suggestions": 3
      }
    },
    {
      "id": "create_issues",
      "status": "completed",
      "duration": 15.8,
      "output": {
        "issues_created": 7
      }
    }
  ],
  "result": {
    "success": true,
    "issues_created": 7,
    "notifications_sent": 1
  }
}
```

**Response (Failed):**
```json
{
  "execution_id": "exec_xyz789",
  "workflow_id": "wf_abc123",
  "status": "failed",
  "started_at": "2025-11-22T18:00:00Z",
  "failed_at": "2025-11-22T18:00:23Z",
  "duration": 23.4,
  "error": {
    "step": "analyze",
    "type": "APIError",
    "message": "OpenAI API rate limit exceeded",
    "retry_after": 60
  },
  "completed_steps": [],
  "failed_step": "analyze"
}
```

**Execution Statuses:**
- `queued`: Waiting to start
- `running`: Currently executing
- `completed`: Successfully completed
- `failed`: Execution failed
- `timeout`: Exceeded timeout limit
- `cancelled`: Manually cancelled

**Status Codes:**
- `200` - Execution status retrieved
- `401` - Authentication required
- `404` - Execution not found

---

## Quality Engine API

### Quality Check Endpoints

#### POST /api/quality/check

(See Dashboard API section for full details)

---

#### GET /api/quality/check/{check_id}

Get quality check status and results.

**Request:**
```http
GET /api/quality/check/qc_abc123 HTTP/1.1
Host: localhost:8080
Authorization: Bearer ghp_abc123...
```

**Response:**
```json
{
  "check_id": "qc_abc123",
  "status": "completed",
  "mode": "smart",
  "started_at": "2025-11-22T18:00:00Z",
  "completed_at": "2025-11-22T18:00:02Z",
  "duration": 2.34,
  "summary": {
    "total_files": 2,
    "total_issues": 7,
    "by_severity": {
      "critical": 1,
      "high": 2,
      "medium": 3,
      "low": 1
    },
    "by_type": {
      "security": 3,
      "bugs": 2,
      "code_smell": 2
    }
  },
  "issues": [...],
  "ai_suggestions": [...]
}
```

**Status Codes:**
- `200` - Check status retrieved
- `401` - Authentication required
- `404` - Check not found

---

## WebSocket API

### Real-time Updates

#### WebSocket Connection

Connect to WebSocket for real-time updates.

**URL:** `ws://localhost:8080/ws`

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onopen = () => {
  console.log('Connected to AutoPR WebSocket');
  
  // Subscribe to workflow updates
  ws.send(JSON.stringify({
    type: 'subscribe',
    topics: ['workflows', 'executions', 'quality_checks']
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from WebSocket');
};
```

**Message Types:**

1. **Subscribe:**
```json
{
  "type": "subscribe",
  "topics": ["workflows", "executions", "quality_checks"],
  "filters": {
    "workflow_id": "wf_abc123"
  }
}
```

2. **Workflow Update:**
```json
{
  "type": "workflow_update",
  "workflow_id": "wf_abc123",
  "status": "completed",
  "timestamp": "2025-11-22T18:00:45Z",
  "data": {
    "execution_id": "exec_xyz789",
    "duration": 45.2,
    "result": "success"
  }
}
```

3. **Execution Progress:**
```json
{
  "type": "execution_progress",
  "execution_id": "exec_xyz789",
  "workflow_id": "wf_abc123",
  "progress": 75,
  "current_step": "create_issues",
  "timestamp": "2025-11-22T18:00:30Z"
}
```

4. **Quality Check Update:**
```json
{
  "type": "quality_check_update",
  "check_id": "qc_abc123",
  "status": "in_progress",
  "progress": 50,
  "issues_found": 3,
  "timestamp": "2025-11-22T18:00:15Z"
}
```

5. **Error:**
```json
{
  "type": "error",
  "error": "AuthenticationError",
  "message": "Invalid token",
  "timestamp": "2025-11-22T18:00:00Z"
}
```

**Topics:**
- `workflows`: Workflow lifecycle events
- `executions`: Execution progress and completion
- `quality_checks`: Quality analysis updates
- `metrics`: System metrics updates
- `alerts`: System alerts and notifications

---

## Request/Response Schemas

### Common Types

```typescript
// Timestamp format: ISO 8601
type Timestamp = string; // "2025-11-22T18:00:00Z"

// UUID format
type UUID = string; // "abc123-def456-..."

// Status types
type WorkflowStatus = "created" | "active" | "paused" | "archived";
type ExecutionStatus = "queued" | "running" | "completed" | "failed" | "timeout" | "cancelled";
type QualityMode = "ultra_fast" | "fast" | "smart" | "comprehensive" | "ai_enhanced";
type Severity = "low" | "medium" | "high" | "critical";

// Pagination
interface PaginationParams {
  page?: number;      // Default: 1
  per_page?: number;  // Default: 20, Max: 100
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    per_page: number;
    total_items: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}
```

### Workflow Schema

```typescript
interface Workflow {
  workflow_id: string;
  name: string;
  description?: string;
  status: WorkflowStatus;
  created_at: Timestamp;
  updated_at: Timestamp;
  trigger: "pull_request" | "push" | "manual" | "schedule";
  steps: WorkflowStep[];
  config: WorkflowConfig;
  executions?: ExecutionSummary;
}

interface WorkflowStep {
  id: string;
  type: string;
  config: Record<string, any>;
  depends_on?: string[];
  status?: "configured" | "running" | "completed" | "failed";
}

interface WorkflowConfig {
  timeout?: number;           // Seconds
  retry_on_failure?: boolean;
  max_retries?: number;
  parallel?: boolean;
  notifications?: {
    on_success?: string[];    // Email addresses or webhook URLs
    on_failure?: string[];
  };
}

interface ExecutionSummary {
  total: number;
  successful: number;
  failed: number;
  success_rate: number;
  avg_duration: number;
}
```

### Execution Schema

```typescript
interface Execution {
  execution_id: string;
  workflow_id: string;
  status: ExecutionStatus;
  started_at: Timestamp;
  completed_at?: Timestamp;
  duration?: number;
  context: Record<string, any>;
  parameters: Record<string, any>;
  steps?: ExecutionStep[];
  result?: Record<string, any>;
  error?: ExecutionError;
}

interface ExecutionStep {
  id: string;
  status: ExecutionStatus;
  started_at: Timestamp;
  completed_at?: Timestamp;
  duration?: number;
  output?: Record<string, any>;
  error?: string;
}

interface ExecutionError {
  step: string;
  type: string;
  message: string;
  retry_after?: number;
  details?: Record<string, any>;
}
```

### Quality Check Schema

```typescript
interface QualityCheck {
  check_id: string;
  mode: QualityMode;
  status: "queued" | "running" | "completed" | "failed";
  started_at: Timestamp;
  completed_at?: Timestamp;
  duration?: number;
  summary: QualitySummary;
  issues: QualityIssue[];
  ai_suggestions?: AISuggestion[];
}

interface QualitySummary {
  total_files: number;
  total_issues: number;
  by_severity: Record<Severity, number>;
  by_type: Record<string, number>;
}

interface QualityIssue {
  file: string;
  line: number;
  column?: number;
  severity: Severity;
  type: string;
  message: string;
  suggestion?: string;
  rule?: string;
}

interface AISuggestion {
  type: "refactoring" | "optimization" | "security" | "best_practice";
  confidence: number;  // 0.0 to 1.0
  description: string;
  code_snippet?: string;
  estimated_impact: "low" | "medium" | "high";
}
```

---

## Status Codes

### Success Codes

| Code | Name | Description |
|------|------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 202 | Accepted | Request accepted for async processing |
| 204 | No Content | Request successful, no content to return |

### Client Error Codes

| Code | Name | Description |
|------|------|-------------|
| 400 | Bad Request | Invalid request parameters or body |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (e.g., duplicate) |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |

### Server Error Codes

| Code | Name | Description |
|------|------|-------------|
| 500 | Internal Server Error | Server-side error |
| 502 | Bad Gateway | Invalid response from upstream server |
| 503 | Service Unavailable | Service temporarily unavailable |
| 504 | Gateway Timeout | Upstream server timeout |

---

## Examples

### Complete Workflow Example

```bash
#!/bin/bash

# Set variables
BASE_URL="http://localhost:8000"
TOKEN="ghp_abc123..."

# 1. Create workflow
WORKFLOW_RESPONSE=$(curl -s -X POST "$BASE_URL/workflows/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PR Analysis Workflow",
    "trigger": "pull_request",
    "steps": [
      {
        "id": "analyze",
        "type": "ai_analysis",
        "config": {"provider": "openai", "model": "gpt-4"}
      },
      {
        "id": "create_issues",
        "type": "issue_creation",
        "depends_on": ["analyze"]
      }
    ]
  }')

WORKFLOW_ID=$(echo $WORKFLOW_RESPONSE | jq -r '.workflow_id')
echo "Created workflow: $WORKFLOW_ID"

# 2. Validate workflow
curl -s -X POST "$BASE_URL/workflows/$WORKFLOW_ID/validate" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# 3. Execute workflow
EXECUTION_RESPONSE=$(curl -s -X POST "$BASE_URL/workflows/$WORKFLOW_ID/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "pr_number": 42,
      "repository": "owner/repo"
    }
  }')

EXECUTION_ID=$(echo $EXECUTION_RESPONSE | jq -r '.execution_id')
echo "Started execution: $EXECUTION_ID"

# 4. Poll execution status
while true; do
  STATUS_RESPONSE=$(curl -s -X GET "$BASE_URL/workflows/$WORKFLOW_ID/executions/$EXECUTION_ID" \
    -H "Authorization: Bearer $TOKEN")
  
  STATUS=$(echo $STATUS_RESPONSE | jq -r '.status')
  echo "Execution status: $STATUS"
  
  if [ "$STATUS" == "completed" ] || [ "$STATUS" == "failed" ]; then
    echo $STATUS_RESPONSE | jq '.'
    break
  fi
  
  sleep 5
done
```

### Python SDK Example

```python
import requests
from typing import Dict, Any

class AutoPRClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def create_workflow(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new workflow."""
        response = requests.post(
            f"{self.base_url}/workflows/",
            json=config,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def execute_workflow(
        self, 
        workflow_id: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a workflow."""
        response = requests.post(
            f"{self.base_url}/workflows/{workflow_id}/execute",
            json={"context": context},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_execution_status(
        self, 
        workflow_id: str, 
        execution_id: str
    ) -> Dict[str, Any]:
        """Get execution status."""
        response = requests.get(
            f"{self.base_url}/workflows/{workflow_id}/executions/{execution_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage
client = AutoPRClient("http://localhost:8000", "ghp_abc123...")

# Create and execute workflow
workflow = client.create_workflow({
    "name": "PR Analysis",
    "trigger": "pull_request",
    "steps": [...]
})

execution = client.execute_workflow(
    workflow["workflow_id"],
    {"pr_number": 42, "repository": "owner/repo"}
)

# Check status
status = client.get_execution_status(
    workflow["workflow_id"],
    execution["execution_id"]
)
print(f"Status: {status['status']}")
```

---

## Best Practices

### API Usage Guidelines

1. **Authentication:**
   - Always use HTTPS in production
   - Store tokens securely (environment variables, secrets manager)
   - Rotate tokens regularly
   - Use fine-grained permissions

2. **Rate Limiting:**
   - Implement exponential backoff for 429 responses
   - Cache responses when appropriate
   - Use webhooks/WebSockets instead of polling when possible
   - Monitor rate limit headers

3. **Error Handling:**
   - Always check status codes
   - Parse error responses for details
   - Implement retry logic for transient errors (500, 502, 503, 504)
   - Log errors for debugging

4. **Performance:**
   - Use pagination for large result sets
   - Request only needed fields (if API supports field selection)
   - Compress request/response bodies (gzip)
   - Implement request timeouts

5. **Security:**
   - Validate and sanitize all inputs
   - Never log sensitive data (tokens, credentials)
   - Use TLS 1.2+ for all connections
   - Implement CSRF protection for web clients

---

## Support & Documentation

### Additional Resources

- **Main Documentation:** `/docs/README.md`
- **Troubleshooting Guide:** `/docs/TROUBLESHOOTING.md`
- **Security Best Practices:** `/docs/security/SECURITY_BEST_PRACTICES.md`
- **Database Optimization:** `/docs/DATABASE_OPTIMIZATION_GUIDE.md`
- **Design System:** `/docs/design/README.md`

### Getting Help

1. **Check Documentation:** Review relevant docs before requesting support
2. **Search Issues:** Check GitHub issues for similar problems
3. **Enable Debug Logging:** Set `LOG_LEVEL=DEBUG` for detailed logs
4. **Contact Support:**
   - Email: support@codeflow-engine.example.com
   - Slack: #autopr-support
   - GitHub Issues: https://github.com/owner/codeflow-engine/issues

### Reporting Issues

When reporting API issues, include:
- Request method, URL, headers (redact sensitive data)
- Request body (redact sensitive data)
- Response status code and body
- Timestamp of the request
- API version
- Client library/SDK version (if applicable)

---

**Document Version:** 1.0.0  
**Last Updated:** 2025-11-22  
**Maintainer:** AutoPR Engine Team
