# AutoPR Engine - Security Best Practices

## **Table of Contents**
1. [Overview](#overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [Secrets Management](#secrets-management)
4. [Network Security](#network-security)
5. [Input Validation](#input-validation)
6. [Database Security](#database-security)
7. [API Security](#api-security)
8. [Monitoring & Incident Response](#monitoring--incident-response)
9. [OWASP Top 10 Compliance](#owasp-top-10-compliance)
10. [Security Checklist](#security-checklist)

---

## **Overview**

AutoPR Engine handles sensitive data including GitHub tokens, API keys, and code repositories. This document outlines security best practices for production deployments.

**Threat Model**: 
- GitHub token compromise → Unauthorized repository access
- API key leakage → Unauthorized AI service usage
- Path traversal → Unauthorized file system access
- Injection attacks → Code execution vulnerabilities

---

## **Authentication & Authorization**

### **GitHub Authentication**

#### **Personal Access Tokens (PAT)**
```bash
# Required scopes
- repo (full control)
- workflow (update workflows)
- write:packages (optional, for package publishing)

# Token rotation schedule
- Development: 90 days
- Production: 30 days
```

#### **GitHub Apps (Recommended for Production)**
```python
# Use GitHub Apps for better security and granular permissions
GITHUB_APP_ID=your_app_id
GITHUB_PRIVATE_KEY_PATH=/secure/path/to/private-key.pem
```

**Benefits**:
- Scoped permissions per repository
- Audit logging
- Rate limit advantages
- Organization-wide installations

### **API Key Management**

#### **AI Provider Keys**
```bash
# Never hardcode keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Use key rotation
# - OpenAI: Monthly rotation
# - Anthropic: Monthly rotation
```

#### **Integration Keys**
```bash
# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Linear
LINEAR_API_KEY=lin_api_...

# Set restrictive permissions
```

---

## **Secrets Management**

### **Development Environment**
```bash
# Use .env file (NEVER commit to git)
cp .env.example .env
# Edit .env with real values

# Verify .gitignore includes
.env
*.key
*.pem
secrets/
```

### **Production Environment**

#### **Option 1: HashiCorp Vault (Recommended)**
```python
# Install vault client
from hvac import Client

vault = Client(url='https://vault.example.com')
vault.auth.approle.login(role_id=ROLE_ID, secret_id=SECRET_ID)

# Fetch secrets
secrets = vault.secrets.kv.v2.read_secret_version(path='autopr/prod')
GITHUB_TOKEN = secrets['data']['data']['github_token']
```

#### **Option 2: AWS Secrets Manager**
```bash
# Store secrets
aws secretsmanager create-secret \
    --name autopr/prod/github-token \
    --secret-string "ghp_..."

# Retrieve in application
import boto3
client = boto3.client('secretsmanager', region_name='us-east-1')
response = client.get_secret_value(SecretId='autopr/prod/github-token')
GITHUB_TOKEN = response['SecretString']
```

#### **Option 3: Azure Key Vault**
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://autopr-vault.vault.azure.net", credential=credential)

GITHUB_TOKEN = client.get_secret("github-token").value
```

#### **Option 4: Kubernetes Secrets**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: autopr-secrets
type: Opaque
stringData:
  github-token: ghp_...
  openai-api-key: sk-...
```

---

## **Network Security**

### **TLS/SSL Configuration**

#### **Nginx Reverse Proxy**
```nginx
server {
    listen 443 ssl http2;
    server_name autopr.example.com;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/autopr.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/autopr.example.com/privkey.pem;
    
    # Strong SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Content-Security-Policy "default-src 'self';" always;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### **Firewall Rules**

#### **iptables (Linux)**
```bash
# Allow SSH (restrict to specific IPs in production)
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTPS
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow HTTP (for Let's Encrypt)
iptables -A INPUT -p tcp --dport 80 -j ACCEPT

# Block all other incoming
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT
```

#### **AWS Security Groups**
```yaml
IngressRules:
  - IpProtocol: tcp
    FromPort: 443
    ToPort: 443
    CidrIp: 0.0.0.0/0
    Description: HTTPS
  
  - IpProtocol: tcp
    FromPort: 22
    ToPort: 22
    CidrIp: 10.0.0.0/8  # VPN only
    Description: SSH from VPN
```

---

## **Input Validation**

### **Path Traversal Prevention**
```python
# IMPLEMENTED in autopr/dashboard/server.py

def _validate_path(self, path_str: str) -> tuple[bool, str | None]:
    """Prevent directory traversal attacks"""
    path = Path(path_str).resolve()
    
    # Check against allowed directories
    is_allowed = any(
        path.is_relative_to(allowed_dir) 
        for allowed_dir in self.allowed_directories
    )
    
    if not is_allowed:
        return False, "Access denied"
    
    return True, None
```

### **Input Sanitization**
```python
# File paths
import re

def sanitize_filename(filename: str) -> str:
    """Remove dangerous characters from filenames"""
    # Remove path separators and null bytes
    safe_name = re.sub(r'[/\\\\\\x00]', '', filename)
    # Remove leading dots
    safe_name = safe_name.lstrip('.')
    return safe_name

# SQL injection prevention (use parameterized queries)
# GOOD
cursor.execute("SELECT * FROM workflows WHERE id = %s", (workflow_id,))

# BAD
cursor.execute(f"SELECT * FROM workflows WHERE id = '{workflow_id}'")
```

---

## **Database Security**

### **Connection Security**
```bash
# PostgreSQL with SSL
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# Connection pooling limits
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT=30
```

### **User Permissions**
```sql
-- Create restricted user for application
CREATE USER autopr_app WITH PASSWORD 'strong_random_password';

-- Grant minimal required permissions
GRANT CONNECT ON DATABASE autopr TO autopr_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO autopr_app;

-- Revoke dangerous permissions
REVOKE DELETE, TRUNCATE, DROP ON ALL TABLES IN SCHEMA public FROM autopr_app;
```

### **Encryption at Rest**
```bash
# PostgreSQL (AWS RDS)
--storage-encrypted \
--kms-key-id arn:aws:kms:us-east-1:123456789:key/...

# Self-hosted
# Enable PostgreSQL encryption in postgresql.conf
ssl = on
ssl_cert_file = '/path/to/server.crt'
ssl_key_file = '/path/to/server.key'
```

---

## **API Security**

### **Rate Limiting**
```python
# Install: pip install slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.route("/api/quality-check")
@limiter.limit("10/minute")  # Max 10 requests per minute
def quality_check():
    pass
```

### **CORS Configuration**
```python
# Restrict CORS in production
from flask_cors import CORS

# Development (permissive)
CORS(app)

# Production (restrictive)
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://autopr.example.com"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

### **Request Validation**
```python
from pydantic import BaseModel, validator

class QualityCheckRequest(BaseModel):
    mode: str
    files: list[str]
    
    @validator('files')
    def validate_files(cls, v):
        if len(v) > 1000:
            raise ValueError('Too many files')
        return v
    
    @validator('mode')
    def validate_mode(cls, v):
        allowed = ['ultra_fast', 'fast', 'smart', 'comprehensive', 'ai_enhanced']
        if v not in allowed:
            raise ValueError(f'Invalid mode: {v}')
        return v
```

---

## **Monitoring & Incident Response**

### **Security Logging**
```python
import structlog

logger = structlog.get_logger()

# Log security events
logger.warning("authentication_failed", 
    ip=request.remote_addr,
    user_agent=request.user_agent.string)

logger.error("path_traversal_attempt",
    requested_path=path,
    source_ip=request.remote_addr)
```

### **Intrusion Detection**
```bash
# Install fail2ban
sudo apt-get install fail2ban

# Configure for AutoPR
# /etc/fail2ban/jail.local
[autopr-api]
enabled = true
port = 443
filter = autopr-api
logpath = /var/log/autopr/access.log
maxretry = 5
bantime = 3600
```

### **Audit Logging**
```python
# Log all administrative actions
@app.route("/api/config", methods=["POST"])
def update_config():
    audit_log.info("config_updated",
        user=get_current_user(),
        changes=config_diff,
        timestamp=datetime.now(),
        ip=request.remote_addr)
```

---

## **OWASP Top 10 Compliance**

### **1. Broken Access Control**
✅ **Mitigated**: Path validation, allowed directories, permission checks

### **2. Cryptographic Failures**
✅ **Mitigated**: TLS/SSL enforced, secrets in vault, encrypted database connections

### **3. Injection**
✅ **Mitigated**: Parameterized queries, input validation, Pydantic models

### **4. Insecure Design**
✅ **Mitigated**: Security by design, principle of least privilege

### **5. Security Misconfiguration**
⚠️ **TODO**: Harden production configuration, remove debug flags

### **6. Vulnerable Components**
⚠️ **TODO**: Regular dependency scanning (see TASK-3 in analysis)

### **7. Authentication Failures**
✅ **Mitigated**: Token-based auth, GitHub Apps, rate limiting

### **8. Software and Data Integrity**
⚠️ **TODO**: Implement code signing, verify dependencies

### **9. Logging Failures**
⚠️ **TODO**: Centralized logging, log aggregation (see DOC-7)

### **10. Server-Side Request Forgery (SSRF)**
✅ **Mitigated**: Whitelist allowed URLs, validate external requests

---

## **Security Checklist**

### **Pre-Deployment**
- [ ] All default passwords changed
- [ ] Secrets in vault/secrets manager
- [ ] TLS/SSL certificates configured
- [ ] Firewall rules applied
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Security headers added
- [ ] Input validation implemented
- [ ] Database user permissions restricted
- [ ] Audit logging configured

### **Post-Deployment**
- [ ] Security scanning scheduled
- [ ] Monitoring alerts configured
- [ ] Incident response plan documented
- [ ] Backup strategy tested
- [ ] Disaster recovery plan in place
- [ ] Security training completed

### **Ongoing**
- [ ] Weekly: Review security logs
- [ ] Monthly: Rotate API keys
- [ ] Monthly: Security dependency scan
- [ ] Quarterly: Penetration testing
- [ ] Quarterly: Security audit
- [ ] Annually: Compliance review

---

## **Incident Response**

### **Suspected Token Compromise**
```bash
# 1. Immediate: Revoke compromised token
gh auth token delete

# 2. Generate new token
gh auth login --scopes repo,workflow

# 3. Update in secrets manager
vault kv put autopr/prod github_token="new_token"

# 4. Restart application
kubectl rollout restart deployment/codeflow-engine

# 5. Audit recent activity
gh api /user/events | jq '.[] | select(.created_at > "2025-01-01")'

# 6. Document incident
```

### **Suspected Breach**
1. **Isolate**: Disconnect compromised system
2. **Assess**: Determine scope and impact
3. **Contain**: Revoke all credentials
4. **Investigate**: Review logs and audit trails
5. **Recover**: Deploy from clean backup
6. **Document**: Postmortem analysis

---

## **Additional Resources**

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks/)

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-20  
**Next Review**: 2025-04-20  

**Contact**: `security@autopr.dev`
