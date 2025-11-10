# DeepAgents Integration Module

Complete integration of the deepagents framework (v0.2.5+) with the DeepAgents Control Platform.

## Overview

This module provides production-ready integration between database-configured AI agents and the deepagents framework, enabling:

- **Agent Creation**: Instantiate deepagents from database configurations
- **Execution Management**: Run agents with streaming support and trace collection
- **Tool Management**: Register and attach custom tools to agents
- **Trace Processing**: Format, analyze, and display execution traces
- **Cost Tracking**: Estimate execution costs based on token usage

## Architecture

```
deepagents_integration/
├── factory.py      # AgentFactory - Create agents from DB config
├── executor.py     # AgentExecutor - Execute agents and collect traces
├── registry.py     # ToolRegistry - Manage LangChain tools
├── traces.py       # TraceFormatter - Process and analyze traces
└── __init__.py     # Module exports
```

## Components

### 1. AgentFactory

Creates deepagents instances from database Agent models.

```python
from deepagents_integration import agent_factory

# Create agent from database configuration
agent = await agent_factory.create_agent(
    agent_config=agent_model,
    tools=[search_tool, calculator_tool],
    subagents=[research_subagent]
)
```

**Features:**
- Multi-provider support (Anthropic, OpenAI)
- Automatic model configuration
- Tool and subagent attachment
- Feature flag handling (planning, filesystem)
- API key validation

**Supported Models:**
- Anthropic: Claude 3.5 Sonnet, Claude 3 Opus, etc.
- OpenAI: GPT-4, GPT-4 Turbo, GPT-3.5 Turbo

**Configuration:**
```python
agent_config = Agent(
    model_provider="anthropic",
    model_name="claude-3-5-sonnet-20241022",
    temperature=0.7,
    max_tokens=4096,
    system_prompt="You are a helpful assistant",
    planning_enabled=True,  # Enables write_todos tool
    filesystem_enabled=True  # Enables file operations
)
```

### 2. AgentExecutor

Executes agents and manages execution lifecycle.

```python
from deepagents_integration import agent_executor

# Execute with streaming
async for trace in agent_executor.execute_agent(
    agent=agent,
    prompt="Analyze this code",
    execution_id=123,
    db=db_session,
    stream=True
):
    print(trace)  # Stream to WebSocket or log
```

**Features:**
- Streaming and non-streaming execution
- Automatic trace collection and storage
- Status tracking (pending → running → completed/failed)
- Error handling and recovery
- Token usage calculation
- Cost estimation

**Execution Flow:**
1. Update execution status to "running"
2. Stream events from agent
3. Save each event as a trace
4. Update final status
5. Calculate token usage and cost

### 3. ToolRegistry

Manages tools available to agents.

```python
from deepagents_integration import tool_registry
from langchain.tools import Tool

# Register custom tool
search_tool = Tool(
    name="web_search",
    func=search_function,
    description="Search the web"
)
tool_registry.register_tool("web_search", search_tool)

# Get tools for agent
tools = tool_registry.create_tools_for_agent(["web_search", "calculator"])
```

**Built-in Tools (from deepagents):**
- `write_todos` - Planning and task decomposition
- `read_file` - Read files from filesystem
- `write_file` - Write files to filesystem
- `ls` - List directory contents
- `edit_file` - Edit existing files
- `glob_search` - Search files by pattern
- `grep_search` - Search file contents
- `task` - Delegate to subagents

### 4. TraceFormatter

Processes and analyzes execution traces.

```python
from deepagents_integration import TraceFormatter

formatter = TraceFormatter()

# Format for UI
ui_traces = [formatter.format_trace_for_ui(trace) for trace in traces]

# Extract specific events
tool_calls = formatter.extract_tool_calls(traces)
llm_responses = formatter.extract_llm_responses(traces)

# Calculate metrics
timeline = formatter.calculate_execution_timeline(traces)
summary = formatter.generate_execution_summary(traces)
```

**Trace Types:**
- `tool_call` - Agent calling a tool
- `tool_result` - Tool execution result
- `llm_call` - LLM API request
- `llm_response` - LLM response received
- `plan_update` - Planning tool updated tasks
- `state_update` - Agent state changed
- `error` - Error occurred

## Usage Examples

### Basic Agent Creation

```python
from deepagents_integration import agent_factory
from models.agent import Agent

# Configure agent
agent_config = Agent(
    name="Research Assistant",
    model_provider="anthropic",
    model_name="claude-3-5-sonnet-20241022",
    system_prompt="You are a research assistant",
    planning_enabled=True,
    filesystem_enabled=True
)

# Create agent
agent = await agent_factory.create_agent(agent_config)
```

### Agent Execution with Traces

```python
from deepagents_integration import agent_executor
from models.execution import Execution

# Create execution record
execution = Execution(
    agent_id=agent_config.id,
    input_prompt="Research Python async patterns",
    status="pending"
)
db.add(execution)
await db.commit()

# Execute with streaming
async for trace in agent_executor.execute_agent(
    agent=agent,
    prompt=execution.input_prompt,
    execution_id=execution.id,
    db=db
):
    # Stream to WebSocket clients
    await websocket.send_json(trace)
```

### Subagent Configuration

```python
from deepagents.middleware.subagents import SubAgent

# Define specialized subagent
research_subagent = SubAgent(
    name="deep-researcher",
    description="Conducts detailed research on topics",
    system_prompt="You are an expert researcher",
    tools=[tavily_search, wikipedia],
    model="claude-3-5-sonnet-20241022"
)

# Create main agent with subagent
agent = await agent_factory.create_agent(
    agent_config,
    subagents=[research_subagent]
)
```

### Cost Tracking

```python
from deepagents_integration import agent_executor

# Calculate token usage from traces
usage = await agent_executor.calculate_token_usage(db, execution_id)
# {'prompt_tokens': 1500, 'completion_tokens': 800, 'total_tokens': 2300}

# Estimate cost
cost = await agent_executor.estimate_cost(
    model_provider="anthropic",
    model_name="claude-3-5-sonnet-20241022",
    prompt_tokens=usage['prompt_tokens'],
    completion_tokens=usage['completion_tokens']
)
# 0.016500 (USD)
```

## Integration with FastAPI

### Agent Creation Endpoint

```python
from fastapi import APIRouter, Depends
from deepagents_integration import agent_factory

router = APIRouter()

@router.post("/agents")
async def create_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db)
):
    # Create database record
    agent_model = Agent(**agent_data.dict())
    db.add(agent_model)
    await db.commit()

    # Test agent creation
    try:
        agent = await agent_factory.create_agent(agent_model)
        return {"id": agent_model.id, "status": "ready"}
    except ValueError as e:
        return {"id": agent_model.id, "status": "error", "error": str(e)}
```

### Execution Endpoint with WebSocket

```python
from fastapi import WebSocket
from deepagents_integration import agent_factory, agent_executor

@router.websocket("/ws/executions/{execution_id}")
async def execute_agent_ws(
    websocket: WebSocket,
    execution_id: int,
    db: AsyncSession = Depends(get_db)
):
    await websocket.accept()

    # Get execution and agent
    execution = await db.get(Execution, execution_id)
    agent_config = await db.get(Agent, execution.agent_id)

    # Create agent
    agent = await agent_factory.create_agent(agent_config)

    # Execute with streaming
    try:
        async for trace in agent_executor.execute_agent(
            agent, execution.input_prompt, execution_id, db
        ):
            await websocket.send_json(trace)
    except Exception as e:
        await websocket.send_json({"error": str(e)})
    finally:
        await websocket.close()
```

## Testing

The factory module has comprehensive tests (21 tests, all passing):

```bash
cd backend
pytest tests/test_deepagents_integration/test_factory.py -v
```

**Test Coverage:**
- Basic agent creation
- Model provider configuration
- Tool and subagent attachment
- Error handling
- API key validation

## Configuration

### Environment Variables

```bash
# Required for Anthropic models
ANTHROPIC_API_KEY=sk-ant-...

# Required for OpenAI models
OPENAI_API_KEY=sk-...

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/deepagents_platform
```

### Database Models

The integration works with these database models:
- `Agent` - Agent configurations
- `Execution` - Execution records
- `Trace` - Individual execution events
- `Tool` - Tool definitions (optional)
- `Subagent` - Subagent configurations

## Performance Considerations

### Token Management
- deepagents agents automatically manage context windows
- Filesystem tools enable large context handling
- Subagents isolate context for efficiency

### Cost Optimization
- Use planning feature for complex tasks
- Leverage subagents for specialized work
- Monitor token usage per execution
- Set appropriate max_tokens limits

### Scalability
- Agents are stateless (can be recreated)
- Executions can run in parallel
- Traces stored in database for persistence
- WebSocket for real-time updates

## Troubleshooting

### "ANTHROPIC_API_KEY not configured"
Set the environment variable before creating agents:
```bash
export ANTHROPIC_API_KEY=your-key
```

### "Unsupported model provider"
Check that the provider is registered:
```python
factory.get_supported_providers()  # ['anthropic', 'openai']
```

### Missing Traces
Ensure database session is committed after saving traces:
```python
await db.commit()  # Commit after each trace save
```

### WebSocket Connection Issues
Verify the execution exists and agent is valid before streaming.

## Extending the Integration

### Adding New Model Providers

```python
from langchain_google_genai import ChatGoogleGenerativeAI

def create_google_model(model_name, temperature, max_tokens):
    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        max_output_tokens=max_tokens
    )

agent_factory.register_provider("google", create_google_model)
```

### Custom Trace Processing

```python
class CustomTraceFormatter(TraceFormatter):
    @staticmethod
    def format_trace_for_ui(trace):
        # Custom formatting logic
        formatted = super().format_trace_for_ui(trace)
        formatted['custom_field'] = process_custom_data(trace)
        return formatted
```

### Custom Tools

```python
from langchain.tools import Tool

def my_custom_function(input: str) -> str:
    # Your logic here
    return result

custom_tool = Tool(
    name="my_tool",
    func=my_custom_function,
    description="Description for the agent"
)

tool_registry.register_tool("my_tool", custom_tool)
```

## Additional Resources

- [deepagents Documentation](https://docs.langchain.com/oss/python/deepagents/overview)
- [LangChain Agents](https://python.langchain.com/docs/modules/agents/)
- [LangGraph Concepts](https://langchain-ai.github.io/langgraph/)
- [Product Requirements](../../docs/DCP.md)
- [Project Guidelines](../../.claude/PROJECT_CONTEXT.md)

## License

Part of the DeepAgents Control Platform project.
