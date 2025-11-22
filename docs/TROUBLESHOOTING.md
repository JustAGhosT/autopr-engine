# AutoPR Engine Troubleshooting Guide

**Version:** 1.0  
**Last Updated:** 2025-11-22  
**Status:** Production Guide

---

## Table of Contents

1. [Common Errors](#common-errors)
2. [Installation Issues](#installation-issues)
3. [Configuration Problems](#configuration-problems)
4. [Runtime Errors](#runtime-errors)
5. [Performance Issues](#performance-issues)
6. [Integration Problems](#integration-problems)
7. [Database Issues](#database-issues)
8. [Security & Authentication](#security--authentication)
9. [Debugging Guide](#debugging-guide)
10. [Getting Help](#getting-help)

---

## Common Errors

### Error: "Workflow engine is not running"

**Symptoms:**
```
WorkflowError: Workflow engine is not running
```

**Cause:** Attempting to execute a workflow before the engine has been started.

**Solution:**
```python
from autopr import AutoPREngine
from autopr.config import AutoPRConfig

# Ensure engine is started
engine = AutoPREngine(config)
await engine.start()  # Must call start() before executing workflows

# Now you can execute workflows
await engine.execute_workflow("my-workflow", context)
```

**Prevention:** Always use the async context manager:
```python
async with AutoPREngine(config) as engine:
    # Engine automatically started and will be stopped
    await engine.execute_workflow("my-workflow", context)
```

---

### Error: "Workflow context validation failed"

**Symptoms:**
```
WorkflowError: Workflow context validation failed: Workflow name contains invalid characters
```

**Cause:** Workflow name or context parameters contain invalid characters or suspicious patterns.

**Solution:**
- Use only alphanumeric characters, hyphens, underscores, dots, and spaces in workflow names
- Avoid special characters like: `; | & < > $ ( ) { } [ ] \`
- Remove HTML tags and JavaScript from parameters

**Valid Examples:**
```python
# ✅ Good
context = {
    "workflow_name": "pr-review-workflow",
    "data": {"key": "safe value"}
}

# ❌ Bad
context = {
    "workflow_name": "test'; DROP TABLE;--",  # SQL injection attempt
    "data": "<script>alert('xss')</script>"   # XSS attempt
}
```

**For legitimate special characters in data:**
```python
# Encode special characters
import json
context = {
    "workflow_name": "safe-workflow",
    "data": json.dumps({"raw_data": "Can contain <anything>"})
}
```

---

### Error: "Invalid GitHub token format"

**Symptoms:**
```
ValueError: Invalid GitHub token format
```

**Cause:** GitHub token doesn't match expected format.

**Solution:**
1. **For Personal Access Tokens:** Should start with `ghp_` or `github_pat_`
2. **For App Tokens:** Configure `github_app_id` and `github_private_key` instead

```bash
# Check your token format
echo $GITHUB_TOKEN | cut -c1-5

# Should output: ghp_ or github_pat_

# If using GitHub App:
export GITHUB_APP_ID=123456
export GITHUB_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----..."
```

**Regenerate Token:**
- Go to GitHub → Settings → Developer settings → Personal access tokens
- Generate new token with required scopes: `repo`, `workflow`

---

### Error: "Rate limit exceeded"

**Symptoms:**
```
RateLimitError: Rate limit exceeded. Retry after 3600 seconds
```

**Cause:** Too many API requests to GitHub/LLM providers.

**Solution:**

**Immediate:**
```python
import time
from autopr.exceptions import RateLimitError

try:
    result = await engine.execute_workflow(...)
except RateLimitError as e:
    if e.retry_after:
        print(f"Rate limited. Waiting {e.retry_after} seconds...")
        time.sleep(e.retry_after)
        result = await engine.execute_workflow(...)
```

**Long-term:**
1. **Implement caching:**
   ```python
   # Add Redis caching
   export REDIS_URL=redis://localhost:6379
   ```

2. **Use multiple API keys with rotation:**
   ```yaml
   # autopr.yml
   api_keys:
     github:
       - token: $GITHUB_TOKEN_1
       - token: $GITHUB_TOKEN_2
   ```

3. **Reduce polling frequency:**
   ```yaml
   polling:
     interval: 300  # Increase from 60 to 300 seconds
   ```

---

### Error: "Database connection failed"

**Symptoms:**
```
ConnectionError: Could not connect to database at postgresql://localhost:5432/autopr
```

**Cause:** Database not running or incorrect connection string.

**Solution:**

**1. Check database is running:**
```bash
# PostgreSQL
pg_isready -h localhost -p 5432

# Docker
docker ps | grep postgres
```

**2. Verify connection string:**
```bash
# Format: postgresql://user:password@host:port/database
export DATABASE_URL="postgresql://autopr:password@localhost:5432/autopr_db"

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

**3. Check network connectivity:**
```bash
# Test port
nc -zv localhost 5432

# Check firewall
sudo ufw status
```

**4. Use SQLite for development:**
```bash
# Fallback to SQLite
export DATABASE_URL="sqlite:///./autopr.db"
```

---

## Installation Issues

### Issue: "Failed to install dependencies"

**Symptoms:**
```
ERROR: Could not find a version that satisfies the requirement autopr-engine
```

**Solutions:**

**1. Upgrade pip:**
```bash
python -m pip install --upgrade pip setuptools wheel
```

**2. Check Python version:**
```bash
python --version  # Should be 3.12 or higher

# If needed, use specific Python version
python3.12 -m pip install autopr-engine
```

**3. Install with all features:**
```bash
pip install "autopr-engine[full]"
```

**4. Install from source:**
```bash
git clone https://github.com/JustAGhosT/autopr-engine.git
cd autopr-engine
pip install -e ".[dev]"
```

---

### Issue: "Import errors after installation"

**Symptoms:**
```
ModuleNotFoundError: No module named 'autopr'
```

**Solutions:**

**1. Verify installation:**
```bash
pip list | grep autopr-engine
python -c "import autopr; print(autopr.__version__)"
```

**2. Check virtual environment:**
```bash
# Ensure you're in the right venv
which python
pip list

# If wrong venv, activate correct one
source venv/bin/activate
```

**3. Reinstall clean:**
```bash
pip uninstall autopr-engine
pip cache purge
pip install autopr-engine
```

---

## Configuration Problems

### Issue: "Configuration file not found"

**Symptoms:**
```
Warning: Failed to load config from autopr.yaml
```

**Solutions:**

**1. Check file location:**
```bash
# Search for config files
find . -name "autopr.y*ml" -o -name ".autopr.y*ml"

# Expected locations:
# - ./autopr.yaml
# - ./autopr.yml
# - ~/.autopr.yaml
# - ~/.autopr.yml
```

**2. Create default configuration:**
```bash
cat > autopr.yaml << EOF
repositories:
  - owner: your-org
    repos: ["your-repo"]

integrations:
  github:
    enabled: true
    
ai_providers:
  default: "openai"
  models:
    openai: "gpt-4"
EOF
```

**3. Use environment variables instead:**
```bash
export GITHUB_TOKEN="your_token"
export OPENAI_API_KEY="your_key"
# Config file optional if using env vars
```

---

### Issue: "Invalid configuration format"

**Symptoms:**
```
yaml.scanner.ScannerError: while scanning a simple key
```

**Solutions:**

**1. Validate YAML syntax:**
```bash
# Install yamllint
pip install yamllint

# Check syntax
yamllint autopr.yaml
```

**2. Common YAML mistakes:**
```yaml
# ❌ Wrong (tabs)
integrations:
	slack:
		enabled: true

# ✅ Correct (spaces)
integrations:
  slack:
    enabled: true

# ❌ Wrong (unquoted special characters)
password: P@ssw0rd!

# ✅ Correct (quoted)
password: "P@ssw0rd!"
```

**3. Test configuration:**
```python
from autopr.config import AutoPRConfig

try:
    config = AutoPRConfig.from_file("autopr.yaml")
    print("✅ Configuration valid")
except Exception as e:
    print(f"❌ Configuration error: {e}")
```

---

## Runtime Errors

### Error: "Workflow execution timed out"

**Symptoms:**
```
WorkflowError: Workflow execution timed out after 3 attempts
```

**Cause:** Workflow taking longer than configured timeout.

**Solutions:**

**1. Increase timeout:**
```python
config = AutoPRConfig()
config.workflow_timeout = 600  # Increase from 300 to 600 seconds
```

**2. Optimize workflow:**
- Check for blocking I/O operations
- Use async operations properly
- Reduce unnecessary API calls
- Implement caching

**3. Check resource constraints:**
```bash
# Check system resources
htop
df -h
free -m
```

**4. Enable debug logging:**
```bash
export ENABLE_DEBUG_LOGGING=true
export AUTOPR_LOG_LEVEL=DEBUG
```

---

### Error: "Memory leak / High memory usage"

**Symptoms:**
- Memory usage continuously increases
- Process crashes with `MemoryError`
- System becomes slow

**Diagnosis:**
```python
# Add memory profiling
import psutil
import os

process = psutil.Process(os.getpid())
print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")
```

**Solutions:**

**1. Check workflow history limit:**
```python
# Verify history is being cleaned
from autopr.workflows.engine import MAX_WORKFLOW_HISTORY
print(f"History limit: {MAX_WORKFLOW_HISTORY}")  # Should be 1000

# Check actual history size
print(f"Actual size: {len(engine.workflow_history)}")
```

**2. Clear caches periodically:**
```python
# Implement cache cleanup
import gc
gc.collect()
```

**3. Use connection pooling:**
```python
# Configure connection limits
config.database_pool_size = 10
config.database_max_overflow = 20
```

---

## Performance Issues

### Issue: "Slow API responses"

**Diagnosis:**
```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8080/api/status

# Create curl-format.txt:
cat > curl-format.txt << EOF
    time_namelookup:  %{time_namelookup}
       time_connect:  %{time_connect}
    time_appconnect:  %{time_appconnect}
      time_redirect:  %{time_redirect}
   time_starttransfer:  %{time_starttransfer}
                        ----------
           time_total:  %{time_total}
EOF
```

**Solutions:**

**1. Enable caching:**
```bash
export REDIS_URL=redis://localhost:6379
```

**2. Use database connection pooling:**
```python
from autopr.config import AutoPRConfig

config = AutoPRConfig()
config.database_pool_size = 20
config.database_pool_recycle = 3600
```

**3. Optimize queries:**
```sql
-- Check slow queries
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;

-- Add missing indexes
CREATE INDEX idx_workflows_status ON workflows(status);
CREATE INDEX idx_workflows_created_at ON workflows(created_at);
```

---

### Issue: "High CPU usage"

**Diagnosis:**
```bash
# Check process CPU
top -p $(pgrep -f autopr)

# Profile Python code
python -m cProfile -o profile.stats your_script.py
python -m pstats profile.stats
```

**Solutions:**

**1. Reduce polling frequency:**
```yaml
polling:
  interval: 300  # Increase interval
```

**2. Use async operations:**
```python
# ❌ Synchronous (blocks)
def process_item(item):
    result = requests.get(url)
    return result

# ✅ Asynchronous
async def process_item(item):
    async with aiohttp.ClientSession() as session:
        result = await session.get(url)
        return await result.json()
```

**3. Implement batching:**
```python
# Process items in batches
batch_size = 10
for i in range(0, len(items), batch_size):
    batch = items[i:i + batch_size]
    await asyncio.gather(*[process_item(item) for item in batch])
```

---

## Integration Problems

### Issue: "Slack webhook not working"

**Symptoms:**
- No notifications in Slack
- Error: `IntegrationError: Slack webhook failed`

**Solutions:**

**1. Test webhook manually:**
```bash
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Hello, World!"}' \
  https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**2. Check webhook URL:**
```python
# Verify configuration
config = get_settings()
print(config.integrations.slack.webhook_url)

# Should start with: https://hooks.slack.com/services/
```

**3. Check Slack app permissions:**
- Go to https://api.slack.com/apps
- Select your app
- Check OAuth & Permissions
- Ensure `chat:write` scope is enabled

---

### Issue: "Linear integration failing"

**Symptoms:**
```
IntegrationError: Linear API request failed: Unauthorized
```

**Solutions:**

**1. Verify API key:**
```bash
# Test Linear API
curl -H "Authorization: YOUR_LINEAR_API_KEY" \
  https://api.linear.app/graphql \
  -d '{"query": "{ viewer { id name } }"}'
```

**2. Check team ID:**
```python
# Get your team ID
import requests

headers = {"Authorization": "YOUR_LINEAR_API_KEY"}
query = """
{
  teams {
    nodes {
      id
      name
    }
  }
}
"""

response = requests.post(
    "https://api.linear.app/graphql",
    json={"query": query},
    headers=headers
)
print(response.json())
```

---

## Database Issues

### Issue: "Migration failed"

**Symptoms:**
```
alembic.util.exc.CommandError: Target database is not up to date
```

**Solutions:**

**1. Check current revision:**
```bash
alembic current
alembic history
```

**2. Run migrations:**
```bash
# Upgrade to latest
alembic upgrade head

# If fails, try step by step
alembic upgrade +1
```

**3. Reset database (development only):**
```bash
# ⚠️ WARNING: Destroys all data
alembic downgrade base
alembic upgrade head
```

**4. Manual migration fix:**
```bash
# Mark current state
alembic stamp head

# Then upgrade normally
alembic upgrade head
```

---

### Issue: "Database locks / deadlocks"

**Symptoms:**
```
OperationalError: database is locked
```

**Solutions:**

**1. For PostgreSQL:**
```sql
-- Check locks
SELECT * FROM pg_locks WHERE granted = false;

-- Kill blocking queries
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle in transaction'
AND NOW() - query_start > interval '5 minutes';
```

**2. For SQLite (development):**
```python
# Increase timeout
import sqlite3
conn = sqlite3.connect('autopr.db', timeout=30.0)
```

**3. Use connection pooling:**
```python
from autopr.database import get_session

async with get_session() as session:
    # Connection automatically managed
    result = await session.execute(query)
```

---

## Security & Authentication

### Issue: "Authentication failed"

**Symptoms:**
```
AuthenticationError: GitHub authentication failed
```

**Solutions:**

**1. Verify token is set:**
```bash
echo $GITHUB_TOKEN | head -c 10
# Should output: ghp_ or github_pat_
```

**2. Check token scopes:**
```bash
# Test token
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user
```

**3. Regenerate token:**
- Go to GitHub Settings → Developer settings → Personal access tokens
- Delete old token
- Generate new with scopes: `repo`, `workflow`, `read:org`

---

### Issue: "Permission denied errors"

**Symptoms:**
```
AutoPRPermissionError: Permission denied for resource
```

**Solutions:**

**1. Check repository permissions:**
```bash
# Verify you have write access
gh api repos/OWNER/REPO | jq '.permissions'
```

**2. Check organization settings:**
- Go to Organization Settings → OAuth App access restrictions
- Ensure AutoPR is authorized

**3. Use GitHub App instead:**
```bash
# GitHub App has more reliable permissions
export GITHUB_APP_ID=123456
export GITHUB_PRIVATE_KEY_PATH=/path/to/key.pem
```

---

## Debugging Guide

### Enable Debug Logging

**Method 1: Environment Variable**
```bash
export ENABLE_DEBUG_LOGGING=true
export AUTOPR_LOG_LEVEL=DEBUG
python -m autopr.cli run
```

**Method 2: Configuration**
```python
from autopr.config import AutoPRConfig

config = AutoPRConfig()
config.enable_debug_logging = True
```

**Method 3: Python Logging**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

### Inspect Workflow Execution

```python
# Get workflow history
history = engine.get_workflow_history(limit=10)
for execution in history:
    print(f"ID: {execution['execution_id']}")
    print(f"Status: {execution['status']}")
    print(f"Result: {execution['result']}")
    print("---")

# Get current metrics
metrics = await engine.get_metrics()
print(f"Success rate: {metrics['success_rate_percent']}%")
print(f"Avg execution time: {metrics['average_execution_time']:.2f}s")
```

---

### Network Debugging

```bash
# Check API connectivity
curl -v https://api.github.com/rate_limit

# Check with authentication
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/rate_limit

# Test OpenAI API
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

### Common Log Messages

**"Workflow execution completed"**
- ✅ Normal - workflow finished successfully

**"Retrying workflow after Xs"**
- ⚠️ Warning - workflow failed, being retried

**"Workflow execution timed out"**
- ❌ Error - workflow exceeded timeout, check performance

**"Workflow context validation failed"**
- ❌ Error - invalid input, check parameters

**"Race condition detected"**
- 🐛 Bug - contact support, this shouldn't happen post-fix

---

## Getting Help

### Before Asking for Help

1. **Check logs:**
   ```bash
   # View recent logs
   tail -f logs/autopr.log
   
   # Search for errors
   grep -i error logs/autopr.log | tail -20
   ```

2. **Verify configuration:**
   ```python
   from autopr.config import validate_configuration
   
   errors = validate_configuration()
   if errors:
       print("Configuration errors:", errors)
   ```

3. **Test basic functionality:**
   ```python
   import asyncio
   from autopr import AutoPREngine
   from autopr.config import AutoPRConfig
   
   async def test():
       config = AutoPRConfig()
       async with AutoPREngine(config) as engine:
           status = await engine.get_status()
           print("Engine status:", status)
   
   asyncio.run(test())
   ```

---

### Reporting Issues

**Include this information:**

1. **Version:**
   ```bash
   pip show autopr-engine
   python --version
   uname -a
   ```

2. **Configuration (sanitized):**
   ```python
   config.to_dict()  # Secrets automatically masked
   ```

3. **Error message:**
   ```
   Full stack trace from logs
   ```

4. **Steps to reproduce:**
   ```
   1. ...
   2. ...
   3. ...
   ```

5. **Environment:**
   ```bash
   Docker / Kubernetes / Local
   Python 3.12.3
   OS: Ubuntu 22.04
   ```

---

### Support Channels

- **GitHub Issues:** https://github.com/JustAGhosT/autopr-engine/issues
- **Discussions:** https://github.com/JustAGhosT/autopr-engine/discussions
- **Email:** support@justaghost.com
- **Documentation:** https://autopr-engine.readthedocs.io

---

### Emergency Contacts

**Critical Production Issues:**
- Create GitHub issue with label `priority: critical`
- Email: support@justaghost.com
- Include "URGENT" in subject line

**Security Vulnerabilities:**
- **DO NOT** create public issue
- Email: security@justaghost.com
- Use PGP key from website if available

---

## Quick Reference

### Most Common Fixes

```bash
# Reset everything (dev only)
docker-compose down -v
docker-compose up -d
alembic upgrade head

# Clear cache
redis-cli FLUSHALL

# Restart with debug
export AUTOPR_LOG_LEVEL=DEBUG
python -m autopr.server --reload

# Test configuration
python -c "from autopr.config import AutoPRConfig; print(AutoPRConfig().to_dict())"

# Check connectivity
curl -v http://localhost:8080/api/status
```

### Health Check Script

```python
#!/usr/bin/env python3
"""Health check script for AutoPR Engine"""
import asyncio
import sys
from autopr import AutoPREngine
from autopr.config import AutoPRConfig

async def health_check():
    try:
        config = AutoPRConfig()
        if not config.validate():
            print("❌ Configuration invalid")
            return False
        
        async with AutoPREngine(config) as engine:
            status = await engine.get_status()
            if status['running']:
                print("✅ Engine healthy")
                return True
            else:
                print("❌ Engine not running")
                return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(health_check())
    sys.exit(0 if result else 1)
```

---

**Document Version:** 1.0  
**Last Updated:** 2025-11-22  
**Maintained by:** AutoPR Engine Team
