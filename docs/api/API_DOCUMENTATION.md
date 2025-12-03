# AutoPR Engine API Documentation

**Version**: 1.0.0  
**Base URL**: `http://localhost:8080`  
**Documentation Type**: REST API

---

## **Overview**

The AutoPR Engine provides a REST API for code quality checking, workflow management, and dashboard monitoring. This document describes all available endpoints, request/response formats, and authentication requirements.

---

## **Table of Contents**

1. [Authentication](#authentication)
2. [Dashboard API](#dashboard-api)
3. [Quality Check API](#quality-check-api)
4. [Configuration API](#configuration-api)
5. [Metrics API](#metrics-api)
6. [Health Check API](#health-check-api)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)

---

## **Authentication**

### **Current Status**: No authentication required (Development)

**TODO: PRODUCTION**:
- [ ] Implement API key authentication
- [ ] Add OAuth 2.0 support
- [ ] JWT token-based auth for user sessions
- [ ] Role-based access control (RBAC)

**Future Authentication Header**:
```http
Authorization: Bearer YOUR_API_KEY
```

---

## **Dashboard API**

### **GET** `/`

Returns the HTML dashboard interface.

**Response**: `200 OK`
```html
<!DOCTYPE html>
<html>...</html>
```

---

### **GET** `/api/status`

Get current dashboard status and statistics.

**Response**: `200 OK`
```json
{
  "uptime_seconds": 3600.5,
  "uptime_formatted": "1:00:00",
  "total_checks": 42,
  "total_issues": 156,
  "success_rate": 0.95,
  "average_processing_time": 2.34,
  "quality_stats": {
    "ultra_fast": {
      "count": 10,
      "avg_time": 0.5
    },
    "fast": {
      "count": 20,
      "avg_time": 1.2
    },
    "smart": {
      "count": 8,
      "avg_time": 3.5
    },
    "comprehensive": {
      "count": 3,
      "avg_time": 8.2
    },
    "ai_enhanced": {
      "count": 1,
      "avg_time": 15.4
    }
  }
}
```

**Fields**:
- `uptime_seconds` (float): Server uptime in seconds
- `uptime_formatted` (string): Human-readable uptime
- `total_checks` (int): Total quality checks performed
- `total_issues` (int): Total issues found
- `success_rate` (float): Success rate (0.0-1.0)
- `average_processing_time` (float): Average processing time in seconds
- `quality_stats` (object): Statistics per quality mode

---

### **GET** `/api/metrics`

Get detailed metrics data for charts and analytics.

**Response**: `200 OK`
```json
{
  "processing_times": [
    {
      "timestamp": "2025-01-20T10:00:00Z",
      "processing_time": 2.5
    }
  ],
  "issue_counts": [
    {
      "timestamp": "2025-01-20T10:00:00Z",
      "issues": 5
    }
  ],
  "quality_mode_usage": {
    "ultra_fast": 10,
    "fast": 20,
    "smart": 8,
    "comprehensive": 3,
    "ai_enhanced": 1
  }
}
```

---

### **GET** `/api/history`

Get recent activity history.

**Response**: `200 OK`
```json
[
  {
    "timestamp": "2025-01-20T10:00:00Z",
    "mode": "fast",
    "files_checked": 10,
    "issues_found": 5,
    "success": true
  }
]
```

---

## **Quality Check API**

### **POST** `/api/quality-check`

Run a quality check on specified files or directory.

**Request Body**:
```json
{
  "mode": "fast",
  "files": ["src/main.py", "src/utils.py"],
  "directory": "/path/to/project"
}
```

**Parameters**:
- `mode` (string, optional): Quality check mode. Default: `"fast"`
  - Values: `"ultra_fast"`, `"fast"`, `"smart"`, `"comprehensive"`, `"ai_enhanced"`
- `files` (array, optional): List of file paths to check
- `directory` (string, optional): Directory to scan recursively

**Validation**:
- At least one of `files` or `directory` must be provided
- Files must be within allowed directories (security)
- Maximum 1000 files per scan

**Response**: `200 OK`
```json
{
  "success": true,
  "mode": "fast",
  "files_checked": 10,
  "total_issues_found": 5,
  "processing_time": 2.34,
  "issues_by_file": {
    "src/main.py": [
      {
        "line": 42,
        "column": 10,
        "severity": "error",
        "code": "E501",
        "message": "Line too long (120 > 88 characters)"
      }
    ]
  },
  "summary": {
    "errors": 2,
    "warnings": 3,
    "info": 0
  }
}
```

**Error Responses**:

`400 Bad Request` - Invalid input
```json
{
  "error": "No files or directory specified"
}
```

`403 Forbidden` - Path validation failed
```json
{
  "error": "Access denied: Path outside allowed directories",
  "details": ["file1.py: Invalid path"]
}
```

`500 Internal Server Error`
```json
{
  "error": "Internal server error"
}
```

---

## **Configuration API**

### **GET** `/api/config`

Get current configuration settings.

**Response**: `200 OK`
```json
{
  "quality_mode": "fast",
  "auto_fix": false,
  "max_file_size": 10000,
  "allowed_directories": [
    "/home/user/projects",
    "/var/app"
  ],
  "integrations": {
    "github": {
      "enabled": true,
      "api_url": "https://api.github.com"
    }
  }
}
```

---

### **POST** `/api/config`

Update configuration settings.

**Request Body**:
```json
{
  "quality_mode": "smart",
  "auto_fix": true,
  "max_file_size": 15000
}
```

**Response**: `200 OK`
```json
{
  "success": true
}
```

**Error Response**: `400 Bad Request`
```json
{
  "error": "Invalid JSON"
}
```

---

## **Health Check API**

### **GET** `/api/health`

Health check endpoint for monitoring.

**Response**: `200 OK`
```json
{
  "status": "healthy",
  "uptime": 3600.5,
  "version": "1.0.0",
  "timestamp": "2025-01-20T10:00:00Z",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "disk_space": "healthy"
  }
}
```

**Status Values**:
- `healthy`: All systems operational
- `degraded`: Some non-critical issues
- `unhealthy`: Critical issues present

---

## **Error Handling**

### **Standard Error Response**

All errors follow this format:

```json
{
  "error": "Error message",
  "details": "Additional details (optional)",
  "code": "ERROR_CODE",
  "timestamp": "2025-01-20T10:00:00Z"
}
```

### **HTTP Status Codes**

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid input/parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Access denied |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Server overloaded |

---

## **Rate Limiting**

**TODO: PRODUCTION - Implement rate limiting**

**Planned Limits**:
- `/api/quality-check`: 100 requests/hour per IP
- Other endpoints: 1000 requests/hour per IP

**Rate Limit Headers**:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642680000
```

**Rate Limit Exceeded Response**: `429 Too Many Requests`
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 3600
}
```

---

## **OpenAPI Specification**

### **OpenAPI 3.0 Schema**

```yaml
openapi: 3.0.0
info:
  title: AutoPR Engine API
  version: 1.0.0
  description: AI-powered code quality and automation platform

servers:
  - url: http://localhost:8080
    description: Development server
  - url: https://api.autopr.example.com
    description: Production server

paths:
  /api/status:
    get:
      summary: Get dashboard status
      tags:
        - Dashboard
      responses:
        '200':
          description: Dashboard status
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DashboardStatus'

  /api/quality-check:
    post:
      summary: Run quality check
      tags:
        - Quality
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/QualityCheckRequest'
      responses:
        '200':
          description: Quality check results
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/QualityCheckResponse'
        '400':
          description: Bad request
        '403':
          description: Forbidden

components:
  schemas:
    DashboardStatus:
      type: object
      properties:
        uptime_seconds:
          type: number
        total_checks:
          type: integer
        success_rate:
          type: number

    QualityCheckRequest:
      type: object
      properties:
        mode:
          type: string
          enum: [ultra_fast, fast, smart, comprehensive, ai_enhanced]
        files:
          type: array
          items:
            type: string
        directory:
          type: string

    QualityCheckResponse:
      type: object
      properties:
        success:
          type: boolean
        files_checked:
          type: integer
        total_issues_found:
          type: integer
```

---

## **Code Examples**

### **Python**

```python
import requests

# Get dashboard status
response = requests.get('http://localhost:8080/api/status')
status = response.json()
print(f"Total checks: {status['total_checks']}")

# Run quality check
payload = {
    'mode': 'fast',
    'files': ['src/main.py', 'src/utils.py']
}
response = requests.post('http://localhost:8080/api/quality-check', json=payload)
result = response.json()
print(f"Issues found: {result['total_issues_found']}")
```

### **cURL**

```bash
# Get status
curl http://localhost:8080/api/status

# Run quality check
curl -X POST http://localhost:8080/api/quality-check \
  -H "Content-Type: application/json" \
  -d '{"mode":"fast","files":["src/main.py"]}'

# Health check
curl http://localhost:8080/api/health
```

### **JavaScript/Fetch**

```javascript
// Get dashboard status
const status = await fetch('http://localhost:8080/api/status')
  .then(res => res.json());
console.log('Total checks:', status.total_checks);

// Run quality check
const result = await fetch('http://localhost:8080/api/quality-check', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    mode: 'fast',
    files: ['src/main.py']
  })
}).then(res => res.json());
console.log('Issues found:', result.total_issues_found);
```

---

## **Webhooks**

### **TODO: PRODUCTION - Webhook Support**

**Planned Webhook Events**:
- `quality_check.completed`
- `quality_check.failed`
- `workflow.started`
- `workflow.completed`

**Webhook Payload Example**:
```json
{
  "event": "quality_check.completed",
  "timestamp": "2025-01-20T10:00:00Z",
  "data": {
    "check_id": "abc123",
    "mode": "fast",
    "files_checked": 10,
    "issues_found": 5
  }
}
```

---

## **TODO: Production Enhancements**

- [ ] Generate interactive API docs with Swagger UI
- [ ] Add GraphQL endpoint for complex queries
- [ ] Implement WebSocket API for real-time updates
- [ ] Add bulk operations endpoints
- [ ] Create SDK libraries (Python, JavaScript, Go)
- [ ] Add request/response logging
- [ ] Implement API versioning (/v1/, /v2/)
- [ ] Add pagination for list endpoints
- [ ] Create API usage analytics
- [ ] Add request validation middleware

---

## **Resources**

- [OpenAPI Specification](https://swagger.io/specification/)
- [REST API Best Practices](https://restfulapi.net/)
- [HTTP Status Codes](https://httpstatuses.com/)

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-20  
**Next Review**: 2025-04-20
