# deepagents Integration Reference

Comprehensive technical reference for deepagents framework integration.

## Table of Contents

- [Core API](#core-api)
- [Middleware Configuration](#middleware-configuration)
- [Subagent System](#subagent-system)
- [Tool System](#tool-system)
- [Event Streaming](#event-streaming)
- [Platform Integration](#platform-integration)
- [Error Handling](#error-handling)

## Core API

### DeepAgent.create()

Factory method for creating configured agent instances.

```python
DeepAgent.create(
    model: str,
    system_prompt: str | None = None,
    tools: list[BaseTool] | None = None,
    planning: bool = False,
    filesystem: bool = False,
    filesystem_config: dict | None = None,
    subagents: dict[str, Subagent] | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
    **kwargs
) -> DeepAgent
```

**Parameters:**

- `model` (str): Model identifier (e.g., "claude-sonnet-4-5-20250929")
- `system_prompt` (str, optional): Custom system instructions
- `tools` (list[BaseTool], optional): Additional tools to provide
- `planning` (bool, default=False): Enable planning middleware with `write_todos` tool
- `filesystem` (bool, default=False): Enable filesystem operations
- `filesystem_config` (dict, optional): Configuration for file storage
  - `storage_path` (str, default="./agent_storage"): Path for file operations
  - `max_file_size` (int, default=10_000_000): Maximum file size in bytes
- `subagents` (dict, optional): Named subagents for delegation
- `checkpointer` (BaseCheckpointSaver, optional): State persistence backend

**Returns:** Configured DeepAgent instance

### Agent Methods

#### ainvoke()

Execute agent with a single prompt.

```python
async def ainvoke(
    self,
    input: str | dict,
    config: RunnableConfig | None = None
) -> AIMessage
```

**Parameters:**
- `input` (str | dict): User prompt or structured input
- `config` (RunnableConfig, optional): Runtime configuration

**Returns:** Final AI message with content and metadata

#### astream_events()

Stream agent execution events.

```python
async def astream_events(
    self,
    input: str | dict,
    config: RunnableConfig | None = None
) -> AsyncIterator[dict]
```

**Event Types:**
- `on_chat_model_start`: Model invocation begins
- `on_chat_model_stream`: Token streaming
- `on_chat_model_end`: Model response complete
- `on_tool_start`: Tool execution begins
- `on_tool_end`: Tool execution complete
- `on_chain_start`: Agent chain starts
- `on_chain_end`: Agent chain completes

## Middleware Configuration

### Planning Middleware

Enables task decomposition with `write_todos` tool.

**Tool Schema:**
```python
{
    "name": "write_todos",
    "description": "Create or update task list",
    "input_schema": {
        "type": "object",
        "properties": {
            "todos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "completed"]
                        },
                        "dependencies": {
                            "type": "array",
                            "items": {"type": "integer"}
                        }
                    },
                    "required": ["description", "status"]
                }
            }
        },
        "required": ["todos"]
    }
}
```

**Best Practices:**
- Create todos with clear, actionable descriptions
- Use dependencies to enforce execution order
- Update status as work progresses
- Keep todo list under 20 items for clarity

### Filesystem Middleware

Provides file operations within controlled sandbox.

**Available Tools:**

1. **file_write**
```python
{
    "name": "file_write",
    "input": {
        "filename": str,  # Relative path within storage
        "content": str    # File content
    }
}
```

2. **file_read**
```python
{
    "name": "file_read",
    "input": {
        "filename": str  # Relative path within storage
    }
}
```

3. **file_list**
```python
{
    "name": "file_list",
    "input": {}  # Lists all files in storage
}
```

**Storage Path Resolution:**
- All paths relative to `filesystem_config.storage_path`
- Path traversal attacks prevented
- Files created with secure permissions

## Subagent System

### Subagent Class

```python
class Subagent:
    def __init__(
        self,
        model: str,
        system_prompt: str,
        tools: list[str | BaseTool] | None = None,
        planning: bool = False,
        filesystem: bool = False,
        **kwargs
    ):
        """Configure a specialized subagent."""
```

**Parameters:**
- `model`: Model for this subagent
- `system_prompt`: Specialized instructions
- `tools`: Subset of tools or tool names
- `planning`: Enable planning for subagent
- `filesystem`: Enable file operations

### Delegation Mechanism

When main agent uses `call_subagent` tool:

1. Context passes to subagent
2. Subagent executes with its configuration
3. Result returns to main agent
4. Main agent continues with subagent output

**Tool Schema:**
```python
{
    "name": "call_subagent",
    "input": {
        "subagent_name": str,  # Key from subagents dict
        "task": str            # Instructions for subagent
    }
}
```

## Tool System

### Custom Tool Definition

```python
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    """Input schema for tool."""
    param1: str = Field(description="Description of param1")
    param2: int = Field(default=10, description="Optional param2")

class MyTool(BaseTool):
    name: str = "my_tool"
    description: str = "What this tool does and when to use it"
    args_schema: type[BaseModel] = MyToolInput
    
    def _run(self, param1: str, param2: int = 10) -> str:
        """Synchronous execution."""
        return f"Result: {param1} x {param2}"
    
    async def _arun(self, param1: str, param2: int = 10) -> str:
        """Async execution (preferred)."""
        # Async implementation
        return f"Result: {param1} x {param2}"
```

### Tool Registry Pattern

```python
class ToolRegistry:
    """Centralized tool management."""
    
    _tools: dict[str, BaseTool] = {}
    
    @classmethod
    def register(cls, tool: BaseTool) -> None:
        """Register tool by name."""
        cls._tools[tool.name] = tool
    
    @classmethod
    def get_tool(cls, name: str) -> BaseTool:
        """Retrieve tool by name."""
        if name not in cls._tools:
            raise ValueError(f"Tool {name} not found")
        return cls._tools[name]
    
    @classmethod
    def get_tools(cls, names: list[str]) -> list[BaseTool]:
        """Retrieve multiple tools."""
        return [cls.get_tool(name) for name in names]

# Usage
ToolRegistry.register(MyTool())
tools = ToolRegistry.get_tools(["my_tool", "another_tool"])
```

## Event Streaming

### Event Structure

All events follow this schema:

```python
{
    "event": str,           # Event type
    "name": str,            # Component name
    "run_id": str,          # Unique run identifier
    "timestamp": str,       # ISO 8601 timestamp
    "metadata": dict,       # Additional metadata
    "data": dict            # Event-specific data
}
```

### Event Types Detail

**on_chat_model_start:**
```python
{
    "event": "on_chat_model_start",
    "data": {
        "input": {
            "messages": [...]  # Input messages
        }
    }
}
```

**on_chat_model_stream:**
```python
{
    "event": "on_chat_model_stream",
    "data": {
        "chunk": {
            "content": str,      # Token content
            "type": "content"    # Chunk type
        }
    }
}
```

**on_tool_start:**
```python
{
    "event": "on_tool_start",
    "name": "tool_name",
    "data": {
        "input": {
            "param1": "value1"  # Tool inputs
        }
    }
}
```

**on_tool_end:**
```python
{
    "event": "on_tool_end",
    "name": "tool_name",
    "data": {
        "output": "tool result"
    }
}
```

### Streaming Handler Pattern

```python
class ExecutionTracer:
    """Track agent execution."""
    
    def __init__(self, execution_id: int, db: AsyncSession):
        self.execution_id = execution_id
        self.db = db
        self.traces: list[dict] = []
    
    async def handle_event(self, event: dict) -> None:
        """Process streaming event."""
        
        # Store trace
        trace = Trace(
            execution_id=self.execution_id,
            event_type=event["event"],
            event_name=event.get("name"),
            run_id=event["run_id"],
            data=event.get("data", {}),
            timestamp=datetime.utcnow()
        )
        self.db.add(trace)
        
        # Handle specific events
        if event["event"] == "on_tool_start":
            await self._handle_tool_start(event)
        elif event["event"] == "on_tool_end":
            await self._handle_tool_end(event)
    
    async def _handle_tool_start(self, event: dict) -> None:
        """Process tool execution start."""
        # Update execution status
        pass
    
    async def _handle_tool_end(self, event: dict) -> None:
        """Process tool execution completion."""
        # Store tool results
        pass
```

## Platform Integration

### Configuration Model

```python
from pydantic import BaseModel, Field

class MiddlewareConfig(BaseModel):
    """Middleware configuration."""
    planning: bool = False
    filesystem: bool = False
    filesystem_path: str = "./storage"
    max_file_size: int = 10_000_000

class SubagentConfig(BaseModel):
    """Subagent configuration."""
    name: str
    model: str
    system_prompt: str
    tools: list[str] = []
    planning: bool = False
    filesystem: bool = False

class AgentConfig(BaseModel):
    """Complete agent configuration."""
    name: str = Field(min_length=3, max_length=64)
    description: str | None = None
    model_name: str
    system_prompt: str
    tools: list[str] = []
    middleware: MiddlewareConfig = MiddlewareConfig()
    subagents: list[SubagentConfig] = []
```

### Factory Implementation

```python
class DeepAgentsFactory:
    """Create agents from configurations."""
    
    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry
    
    async def create_from_config(
        self, 
        config: AgentConfig
    ) -> DeepAgent:
        """Build agent from configuration object."""
        
        # Resolve tools
        tools = self.tool_registry.get_tools(config.tools)
        
        # Build subagents
        subagents = {}
        for sub_config in config.subagents:
            subagents[sub_config.name] = Subagent(
                model=sub_config.model,
                system_prompt=sub_config.system_prompt,
                tools=self.tool_registry.get_tools(sub_config.tools),
                planning=sub_config.planning,
                filesystem=sub_config.filesystem
            )
        
        # Create agent
        agent = DeepAgent.create(
            model=config.model_name,
            system_prompt=config.system_prompt,
            tools=tools,
            planning=config.middleware.planning,
            filesystem=config.middleware.filesystem,
            filesystem_config={
                "storage_path": config.middleware.filesystem_path,
                "max_file_size": config.middleware.max_file_size
            },
            subagents=subagents
        )
        
        return agent
```

### Execution Service

```python
class AgentExecutionService:
    """Manage agent execution lifecycle."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def execute(
        self,
        agent: DeepAgent,
        user_input: str,
        execution_id: int
    ) -> ExecutionResult:
        """Execute agent with full tracking."""
        
        # Create tracer
        tracer = ExecutionTracer(execution_id, self.db)
        
        # Update execution status
        await self._update_status(execution_id, "running")
        
        try:
            # Stream execution
            async for event in agent.astream_events(user_input):
                await tracer.handle_event(event)
                await self.db.flush()  # Commit traces incrementally
            
            # Mark complete
            await self._update_status(execution_id, "completed")
            
        except Exception as e:
            # Handle errors
            await self._update_status(execution_id, "failed")
            await self._store_error(execution_id, str(e))
            raise
        
        finally:
            await self.db.commit()
        
        return await self._get_result(execution_id)
    
    async def _update_status(
        self, 
        execution_id: int, 
        status: str
    ) -> None:
        """Update execution status."""
        execution = await self.db.get(Execution, execution_id)
        execution.status = status
        execution.updated_at = datetime.utcnow()
    
    async def _store_error(
        self, 
        execution_id: int, 
        error: str
    ) -> None:
        """Store execution error."""
        execution = await self.db.get(Execution, execution_id)
        execution.error = error
    
    async def _get_result(
        self, 
        execution_id: int
    ) -> ExecutionResult:
        """Retrieve execution result."""
        execution = await self.db.get(Execution, execution_id)
        traces = await self.db.execute(
            select(Trace)
            .where(Trace.execution_id == execution_id)
            .order_by(Trace.timestamp)
        )
        
        return ExecutionResult(
            execution=execution,
            traces=traces.scalars().all()
        )
```

## Error Handling

### Exception Hierarchy

```python
class DeepAgentsError(Exception):
    """Base exception for deepagents errors."""
    pass

class ConfigurationError(DeepAgentsError):
    """Invalid configuration."""
    pass

class ToolExecutionError(DeepAgentsError):
    """Tool execution failed."""
    pass

class SubagentError(DeepAgentsError):
    """Subagent execution failed."""
    pass

class FilesystemError(DeepAgentsError):
    """Filesystem operation failed."""
    pass
```

### Error Recovery Patterns

```python
async def execute_with_retry(
    agent: DeepAgent,
    input: str,
    max_retries: int = 3
) -> AIMessage:
    """Execute with automatic retry."""
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            result = await agent.ainvoke(input)
            return result
        
        except ToolExecutionError as e:
            last_error = e
            # Exponential backoff
            await asyncio.sleep(2 ** attempt)
            continue
        
        except SubagentError as e:
            # Don't retry subagent errors
            raise
    
    raise last_error

async def execute_with_fallback(
    primary_agent: DeepAgent,
    fallback_agent: DeepAgent,
    input: str
) -> AIMessage:
    """Execute with fallback agent."""
    
    try:
        return await primary_agent.ainvoke(input)
    except DeepAgentsError:
        # Try fallback
        return await fallback_agent.ainvoke(input)
```

## Performance Optimization

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_cached_agent(config_hash: str) -> DeepAgent:
    """Cache agent instances by configuration."""
    # Agent creation is expensive
    pass

# Use with immutable config
config_hash = hash(frozenset(config.model_dump().items()))
agent = get_cached_agent(config_hash)
```

### Batching

```python
async def execute_batch(
    agent: DeepAgent,
    inputs: list[str]
) -> list[AIMessage]:
    """Execute multiple inputs concurrently."""
    
    tasks = [agent.ainvoke(input) for input in inputs]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return results
```

### Streaming Optimization

```python
async def stream_to_client(
    agent: DeepAgent,
    input: str,
    websocket: WebSocket
):
    """Stream results directly to client."""
    
    async for event in agent.astream_events(input):
        # Send only relevant events
        if event["event"] in ["on_chat_model_stream", "on_tool_end"]:
            await websocket.send_json({
                "type": event["event"],
                "data": event["data"]
            })
```

## Testing Reference

### Mock Agent

```python
class MockDeepAgent(DeepAgent):
    """Mock agent for testing."""
    
    def __init__(self, responses: list[str]):
        self.responses = responses
        self.call_count = 0
    
    async def ainvoke(self, input: str) -> AIMessage:
        """Return pre-configured response."""
        response = self.responses[self.call_count]
        self.call_count += 1
        return AIMessage(content=response)
```

### Test Fixtures

```python
@pytest.fixture
def test_agent():
    """Create test agent."""
    return DeepAgent.create(
        model="claude-sonnet-4-5-20250929",
        planning=True,
        filesystem=True,
        filesystem_config={"storage_path": "/tmp/test"}
    )

@pytest.fixture
def mock_tools():
    """Mock tool set."""
    return [
        MockTool(name="tool1", result="result1"),
        MockTool(name="tool2", result="result2")
    ]
```
