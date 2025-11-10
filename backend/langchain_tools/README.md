# External Tools Integration - LangChain Tools

This directory contains the LangChain tool wrappers that enable AI agents to interact with external services.

## Overview

The External Tools Integration provides AI agents with access to:
- **PostgreSQL** - Database queries and analytics
- **GitLab** - Code repository operations
- **Elasticsearch** - Log analysis and search
- **HTTP Client** - RESTful API calls

## Architecture

```
langchain_tools/
├── base.py                  # BaseLangChainTool abstract class
├── postgresql_tool.py       # PostgreSQL wrapper (4 tools)
├── gitlab_tool.py           # GitLab wrapper (5 tools)
├── elasticsearch_tool.py    # Elasticsearch wrapper (3 tools)
├── http_client_tool.py      # HTTP client wrapper (2 tools)
└── execution_logger.py      # Execution logging wrapper
```

## Base Class Pattern

All tool wrappers inherit from `BaseLangChainTool`:

```python
from langchain_tools.base import BaseLangChainTool
from langchain.tools import BaseTool
from typing import List, Dict, Any

class MyTool(BaseLangChainTool):
    def get_tool_type(self) -> str:
        """Return tool type identifier"""
        return "my_tool"

    def get_encrypted_fields(self) -> List[str]:
        """Return list of fields to encrypt"""
        return ["password", "api_key"]

    async def validate_config(self) -> None:
        """Validate configuration before use"""
        if not self.config.get("host"):
            raise ValueError("host is required")

    async def create_tools(self) -> List[BaseTool]:
        """Create and return LangChain tools"""
        decrypted = self.decrypt_config()
        # Create tool instances
        return [...]

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to external service"""
        return {
            "success": True,
            "message": "Connection successful",
            "latency_ms": 45
        }
```

## Tool Wrappers

### 1. PostgreSQLTool

**File:** `postgresql_tool.py` (324 lines)

**Configuration:**
```python
{
    "host": "db.example.com",
    "port": 5432,
    "database": "mydb",
    "username": "user",
    "password": "password",     # Encrypted
    "ssl_mode": "require",
    "read_only": true,          # Enforces SELECT-only
    "timeout": 30,              # Seconds
    "row_limit": 1000,          # Max rows returned
    "pool_size": 5,
    "max_overflow": 10
}
```

**Tools Created:**
- `sql_db_query` - Execute SELECT queries (read-only enforced)
- `sql_db_schema` - Get table schemas
- `sql_db_list_tables` - List all tables
- `sql_db_query_checker` - Validate SQL syntax

**Security Features:**
- Read-only SQL enforcement (blocks INSERT/UPDATE/DELETE/DROP/etc.)
- Query timeout (default 30s)
- Row limit (default 1000 rows)
- Connection pooling with limits
- SSL/TLS support

**Example:**
```python
from langchain_tools.postgresql_tool import PostgreSQLTool

config = {
    "host": "localhost",
    "port": 5432,
    "database": "analytics",
    "username": "readonly",
    "password": "encrypted_password",
    "read_only": True
}

tool = PostgreSQLTool(config)
await tool.validate_config()
tools = await tool.create_tools()  # Returns 4 LangChain tools

# Test connection
result = await tool.test_connection()
# {"success": True, "message": "Connected to PostgreSQL 14.5", ...}
```

### 2. GitLabTool

**File:** `gitlab_tool.py` (494 lines)

**Configuration:**
```python
{
    "gitlab_url": "https://gitlab.com",
    "access_token": "glpat-xxxxx",  # Encrypted
    "default_project": "org/project",
    "rate_limit": 600,              # Requests per hour
    "timeout": 30
}
```

**Tools Created:**
- `gitlab_read_file` - Read file contents from repository
- `gitlab_search_code` - Search code across repository
- `gitlab_list_commits` - List recent commits
- `gitlab_get_merge_request` - Get merge request details
- `gitlab_list_issues` - List issues

**Security Features:**
- Rate limiting (600 req/hour default)
- Project-scoped access
- Timeout enforcement
- Token scope validation

**Example:**
```python
from langchain_tools.gitlab_tool import GitLabTool

config = {
    "gitlab_url": "https://gitlab.com",
    "access_token": "glpat-encrypted_token",
    "default_project": "myorg/myproject"
}

tool = GitLabTool(config)
tools = await tool.create_tools()  # Returns 5 LangChain tools
```

### 3. ElasticsearchTool

**File:** `elasticsearch_tool.py` (287 lines)

**Configuration:**
```python
{
    "hosts": ["https://es.example.com:9200"],
    "index_name": "logs-*",
    "username": "elastic",      # Optional
    "password": "password",     # Encrypted, optional
    "api_key": "base64_key",    # Encrypted, optional
    "verify_certs": true,
    "ca_certs": "/path/to/ca.pem",  # Optional
    "timeout": 30,
    "max_hits": 100
}
```

**Tools Created:**
- `elasticsearch_search` - Full-text search with filters
- `elasticsearch_aggregate` - Aggregations (count, avg, etc.)
- `elasticsearch_get_document` - Get document by ID

**Security Features:**
- Index-based access control
- Query size limits (max_hits)
- Timeout enforcement
- SSL/TLS verification

**Example:**
```python
from langchain_tools.elasticsearch_tool import ElasticsearchTool

config = {
    "hosts": ["http://localhost:9200"],
    "index_name": "app-logs-*",
    "max_hits": 100
}

tool = ElasticsearchTool(config)
tools = await tool.create_tools()  # Returns 3 LangChain tools
```

### 4. HTTPClientTool

**File:** `http_client_tool.py` (198 lines)

**Configuration:**
```python
{
    "allowed_domains": ["api.example.com"],
    "default_headers": {
        "Authorization": "Bearer token",  # Encrypted
        "User-Agent": "DeepAgents/1.0"
    },
    "timeout": 30,
    "verify_ssl": true
}
```

**Tools Created:**
- `http_get` - HTTP GET request
- `http_post` - HTTP POST request

**Security Features:**
- Domain whitelisting (strict)
- SSL/TLS enforcement
- Timeout enforcement
- Header filtering

**Example:**
```python
from langchain_tools.http_client_tool import HTTPClientTool

config = {
    "allowed_domains": ["api.weather.com"],
    "default_headers": {
        "Authorization": "Bearer encrypted_token"
    }
}

tool = HTTPClientTool(config)
tools = await tool.create_tools()  # Returns 2 LangChain tools
```

## Execution Logging

All tools are automatically wrapped with `ToolExecutionLoggerWrapper` to provide audit trail.

**File:** `execution_logger.py` (375 lines)

**Logged Data:**
- Tool name and type
- User ID, agent ID, execution ID
- Input parameters (sanitized)
- Output result
- Success/failure status
- Execution duration (ms)
- Error messages
- Timestamp

**Example:**
```python
from langchain_tools.execution_logger import wrap_tools_with_logging

# Wrap all tools with logging
wrapped_tools = wrap_tools_with_logging(
    tools=original_tools,
    tool_config_id=config.id,
    tool_name=config.tool_name,
    tool_type=config.tool_type,
    user_id=user.id,
    db=db_session,
    agent_id=agent.id,
    execution_id=exec_id
)

# Every tool call now automatically logs to database
```

**Database Record:**
```sql
SELECT * FROM tool_execution_logs ORDER BY executed_at DESC LIMIT 1;

-- Example:
-- tool_name: "sql_db_query"
-- input_params: {"query": "SELECT COUNT(*) FROM users"}  -- Sanitized
-- output_result: "1247"
-- success: true
-- duration_ms: 156
-- executed_at: "2025-01-09T12:00:00Z"
```

## Usage in Agent Execution

Tools are loaded automatically by `ToolFactory` when an agent executes:

```python
from services.tool_factory import ToolFactory

tool_factory = ToolFactory()

# Load tools for agent
tools = await tool_factory.get_tools_for_agent(
    agent_id=agent.id,
    user_id=user.id,
    db=db_session,
    tool_ids=[1, 2, 3],  # From agent.langchain_tool_ids
    execution_id=exec_id
)

# Returns:
# - Decrypted credentials
# - Instantiated LangChain tools
# - Wrapped with execution logging
# - Ready to attach to agent
```

## Security Considerations

### Credential Encryption

All sensitive fields are encrypted using Fernet (AES-128 CBC):

```python
from core.encryption import CredentialEncryption

encryptor = CredentialEncryption()

# Encrypt before saving
config["password"] = encryptor.encrypt("my_password")

# Decrypt in tool wrapper
decrypted = self.decrypt_config()
password = decrypted["password"]  # Plaintext, in memory only
```

**Encrypted Fields:**
- password
- api_key
- access_token
- secret
- token
- bearer_token
- private_key
- credentials

### Credential Sanitization

All logs and API responses sanitize credentials:

```python
from core.encryption import CredentialSanitizer

sanitized = CredentialSanitizer.sanitize_dict(input_params)
# {"username": "admin", "password": "***SANITIZED***"}
```

### Read-Only Enforcement (PostgreSQL)

SQL queries are checked before execution:

```python
WRITE_KEYWORDS = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE",
                  "ALTER", "TRUNCATE", "GRANT", "REVOKE"]

def _is_write_query(sql: str) -> bool:
    sql_upper = sql.upper().strip()
    return any(sql_upper.startswith(keyword) for keyword in WRITE_KEYWORDS)

# Raises ValueError if write operation detected
```

### Domain Whitelisting (HTTP)

Domains are strictly validated:

```python
def _is_domain_allowed(url: str, allowed_domains: List[str]) -> bool:
    parsed = urlparse(url)
    return parsed.netloc in allowed_domains

# Raises ValueError if domain not in allowlist
```

## Testing Connections

All tools implement `test_connection()` method:

```python
# PostgreSQL
result = await postgresql_tool.test_connection()
{
    "success": True,
    "message": "Connected to PostgreSQL 14.5",
    "latency_ms": 45,
    "metadata": {
        "server_version": "PostgreSQL 14.5 on x86_64-pc-linux-gnu"
    }
}

# GitLab
result = await gitlab_tool.test_connection()
{
    "success": True,
    "message": "Connected to GitLab",
    "latency_ms": 123,
    "metadata": {
        "gitlab_version": "15.8.0",
        "api_version": "v4",
        "project_accessible": True
    }
}

# Elasticsearch
result = await elasticsearch_tool.test_connection()
{
    "success": True,
    "message": "Connected to Elasticsearch",
    "latency_ms": 67,
    "metadata": {
        "cluster_name": "production",
        "version": "8.5.0",
        "indices_found": 42
    }
}

# HTTP
result = await http_tool.test_connection()
{
    "success": True,
    "message": "Domain whitelist validated",
    "latency_ms": 0,
    "metadata": {
        "allowed_domains": ["api.example.com"],
        "ssl_verify": True
    }
}
```

## Error Handling

All tools use consistent error handling:

```python
try:
    tools = await tool.create_tools()
except ValueError as e:
    # Configuration validation error
    logger.error(f"Invalid config: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except ConnectionError as e:
    # Connection failed
    logger.error(f"Connection failed: {e}")
    raise HTTPException(status_code=503, detail="Service unavailable")
except Exception as e:
    # Unexpected error
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal error")
```

## Monitoring

Tools emit Prometheus metrics:

```python
from core.middleware import record_tool_execution

record_tool_execution(
    tool_type="postgresql",
    tool_name="Production DB",
    duration_seconds=0.156,
    success=True,
    user_id=1
)

# Metrics emitted:
# tool_executions_total{tool_type="postgresql", success="true"} 1
# tool_execution_duration_seconds{tool_type="postgresql"} 0.156
```

## Adding New Tool Types

To add a new tool type:

1. **Create wrapper class:**
```python
# langchain_tools/my_new_tool.py

from langchain_tools.base import BaseLangChainTool
from langchain.tools import BaseTool
from typing import List, Dict, Any

class MyNewTool(BaseLangChainTool):
    def get_tool_type(self) -> str:
        return "my_new_tool"

    def get_encrypted_fields(self) -> List[str]:
        return ["api_key"]

    async def validate_config(self) -> None:
        if not self.config.get("api_url"):
            raise ValueError("api_url is required")

    async def create_tools(self) -> List[BaseTool]:
        # Implement tool creation
        pass

    async def test_connection(self) -> Dict[str, Any]:
        # Implement connection test
        pass
```

2. **Register in ToolFactory:**
```python
# services/tool_factory.py

TOOL_CLASSES = {
    "postgresql": PostgreSQLTool,
    "gitlab": GitLabTool,
    "elasticsearch": ElasticsearchTool,
    "http": HTTPClientTool,
    "my_new_tool": MyNewTool,  # Add here
}
```

3. **Add to tool catalog:**
```python
# api/v1/external_tools.py

TOOL_CATALOG = {
    "my_new_tool": {
        "name": "My New Tool",
        "description": "Integration with My New Service",
        "category": "integration",
        "required_fields": ["api_url", "api_key"],
        "optional_fields": ["timeout"],
        # ...
    }
}
```

4. **Update frontend:**
```typescript
// frontend/src/types/externalTool.ts
export type ExternalToolType = 'postgresql' | 'gitlab' | 'elasticsearch' | 'http' | 'my_new_tool';

// frontend/src/components/externalTools/ExternalToolConfigModal.tsx
const TOOL_CONFIG_TEMPLATES = {
    my_new_tool: {
        api_url: 'https://api.example.com',
        api_key: '',
        timeout: 30,
    }
};
```

## Dependencies

```python
# requirements.txt
langchain-community>=0.3.0
langchain-elasticsearch>=0.3.0
python-gitlab>=4.0.0
psycopg2-binary>=2.9.0
cryptography>=42.0.0
sqlalchemy[asyncio]>=2.0.0
```

## References

- **Main Documentation:** `/EXTERNAL_TOOLS_INTEGRATION.md`
- **Quick Start Guide:** `/EXTERNAL_TOOLS_QUICKSTART.md`
- **Implementation Summary:** `/EXTERNAL_TOOLS_IMPLEMENTATION_SUMMARY.md`
- **API Endpoints:** `/backend/api/v1/external_tools.py`
- **ToolFactory:** `/backend/services/tool_factory.py`
- **Frontend Page:** `/frontend/src/pages/ExternalTools.tsx`

---

**Version:** 1.0
**Last Updated:** January 9, 2025
**Status:** Production Ready ✅
