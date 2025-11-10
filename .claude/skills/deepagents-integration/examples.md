# deepagents Integration Examples (2025)

Comprehensive examples organized by difficulty level, demonstrating deepagents framework with latest 2025 patterns.

## Table of Contents

### Basics (Getting Started)
- [Simple Q&A Agent](#simple-qa-agent)
- [Agent with Custom Tools](#agent-with-custom-tools)
- [Basic Planning](#basic-planning)
- [Simple Filesystem Operations](#simple-filesystem-operations)

### Intermediate (Production Features)
- [State Management with TypedDict](#state-management-with-typeddict)
- [Advanced Planning with Dependencies](#advanced-planning-with-dependencies)
- [Subagent Delegation](#subagent-delegation)
- [Event Streaming and Progress Tracking](#event-streaming-and-progress-tracking)
- [Error Handling and Retry Logic](#error-handling-and-retry-logic)
- [Middleware Integration](#middleware-integration)

### Advanced (Enterprise Patterns)
- [Multi-Agent Collaborative Workflows](#multi-agent-collaborative-workflows)
- [RAG Integration with Vector Stores](#rag-integration-with-vector-stores)
- [MCP Server Integration](#mcp-server-integration)
- [Production Deployment with FastAPI](#production-deployment-with-fastapi)
- [Horizontal Scaling with Celery](#horizontal-scaling-with-celery)
- [LangSmith Tracing and Evaluation](#langsmith-tracing-and-evaluation)
- [Context-Aware Adaptive Agents](#context-aware-adaptive-agents)
- [Streaming with Iterative Refinement](#streaming-with-iterative-refinement)

---

# Basic Examples

## Simple Q&A Agent

```python
from deepagents import DeepAgent
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

async def simple_qa_example():
    """Basic question answering agent with 2025 API."""
    
    # Define state schema (optional for simple agents)
    class SimpleState(TypedDict):
        messages: Annotated[list[BaseMessage], add_messages]
    
    agent = DeepAgent.create(
        model="claude-sonnet-4-5-20250929",
        system_prompt="You are a helpful assistant that provides clear, concise answers.",
        state_schema=SimpleState
    )
    
    result = await agent.ainvoke("What is Python?")
    print(result.content)
    # Output: "Python is a high-level, interpreted programming language..."

if __name__ == "__main__":
    import asyncio
    asyncio.run(simple_qa_example())
```

## Agent with Custom Tools

```python
from deepagents import DeepAgent
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Annotated

# Modern tool definition with full typing (2025)
class DiscountInput(BaseModel):
    """Input schema for discount calculator."""
    price: float = Field(gt=0, description="Original price in dollars")
    discount_percent: float = Field(ge=0, le=100, description="Discount percentage (0-100)")

@tool("calculate_discount", args_schema=DiscountInput)
async def calculate_discount(price: float, discount_percent: float) -> dict:
    """Calculate discounted price with validation.
    
    Use this tool when the user asks about pricing with discounts.
    Returns the final price and amount saved.
    """
    discount_amount = price * (discount_percent / 100)
    final_price = price - discount_amount
    
    return {
        "original_price": price,
        "discount_percent": discount_percent,
        "discount_amount": round(discount_amount, 2),
        "final_price": round(final_price, 2)
    }

async def agent_with_tools():
    """Agent with custom calculation tool."""
    
    agent = DeepAgent.create(
        model="claude-sonnet-4-5-20250929",
        tools=[calculate_discount],
        system_prompt="""You are a pricing assistant.
        
        Use the calculate_discount tool to help with pricing questions.
        Always show the breakdown of calculations clearly.
        """
    )
    
    result = await agent.ainvoke(
        "If a product costs $100 and has a 20% discount, what's the final price?"
    )
    print(result.content)
    # Output: "The final price would be $80.00. You save $20.00 (20% off the original $100.00)."

if __name__ == "__main__":
    import asyncio
    asyncio.run(agent_with_tools())
```

## Basic Planning

```python
async def basic_planning_example():
    """Agent that creates project plans."""
    
    agent = DeepAgent.create(
        model="claude-sonnet-4-5-20250929",
        planning=True,
        system_prompt="""You are a project planning expert.
        
        When given a project:
        1. Use write_todos to break it into phases
        2. Create specific, actionable tasks
        3. Set up dependencies between tasks
        4. Update status as you analyze requirements
        """
    )
    
    result = await agent.ainvoke("""
    Create a plan for building a REST API for a todo application with:
    - User authentication
    - CRUD operations for todos
    - PostgreSQL database
    - Docker deployment
    """)
    
    # Agent will use write_todos to create structured plan
    print(result.content)
    print("\nTodos created:", result.metadata.get("todos", []))
```

**Expected Output:**
```python
[
    {
        "description": "Set up project structure and dependencies",
        "status": "pending",
        "dependencies": []
    },
    {
        "description": "Implement database models with SQLAlchemy",
        "status": "pending",
        "dependencies": [0]
    },
    {
        "description": "Create authentication system with JWT",
        "status": "pending",
        "dependencies": [1]
    },
    {
        "description": "Implement CRUD endpoints for todos",
        "status": "pending",
        "dependencies": [2]
    },
    {
        "description": "Write API tests",
        "status": "pending",
        "dependencies": [3]
    },
    {
        "description": "Create Dockerfile and docker-compose.yml",
        "status": "pending",
        "dependencies": [4]
    }
]
```

### Iterative Planning with Status Updates

```python
async def iterative_planning_example():
    """Agent updates plan as work progresses."""
    
    agent = DeepAgent.create(
        model="claude-sonnet-4-5-20250929",
        planning=True,
        system_prompt="""You are a development assistant.
        
        For each task:
        1. Create initial todos
        2. Mark current task as 'in_progress'
        3. Complete the work
        4. Mark as 'completed'
        5. Move to next task
        """
    )
    
    # First execution creates plan
    result1 = await agent.ainvoke("Build a simple web scraper")
    
    # Subsequent executions update plan
    result2 = await agent.ainvoke("I've set up the project. What's next?")
    
    # Agent will update todo status automatically
```

## Filesystem Operations

### Document Processing Agent

```python
async def document_processor_example():
    """Agent that processes and stores documents."""
    
    agent = DeepAgent.create(
        model="claude-sonnet-4-5-20250929",
        filesystem=True,
        filesystem_config={
            "storage_path": "./document_storage",
            "max_file_size": 10_000_000
        },
        system_prompt="""You are a document processing assistant.
        
        When analyzing documents:
        1. Extract key information
        2. Create summaries
        3. Save results using file_write
        4. Reference saved files in responses
        """
    )
    
    result = await agent.ainvoke("""
    Analyze this meeting transcript and create:
    1. A summary (save as summary.txt)
    2. Action items (save as actions.txt)
    3. Key decisions (save as decisions.txt)
    
    Transcript:
    "We discussed the Q4 roadmap. Decision: prioritize mobile app.
    Action: John to create wireframes by Friday.
    Action: Sarah to research competitor features."
    """)
    
    print(result.content)
    # Agent saved three files and references them in response
```

### Data Analysis with Context Offloading

```python
async def data_analysis_example():
    """Agent offloads large analysis to files."""
    
    agent = DeepAgent.create(
        model="claude-sonnet-4-5-20250929",
        filesystem=True,
        planning=True,
        system_prompt="""You are a data analyst.
        
        For large datasets:
        1. Save intermediate results to files
        2. Reference files instead of repeating data
        3. Build on previous analysis
        """
    )
    
    # First analysis
    result1 = await agent.ainvoke("""
    Analyze this sales data and save detailed breakdown:
    Q1: $150k, Q2: $180k, Q3: $220k, Q4: $280k
    """)
    
    # Later analysis references saved work
    result2 = await agent.ainvoke("""
    Based on the previous analysis you saved,
    what's the growth rate trend?
    """)
    
    # Agent reads from previously saved file
```

## Subagent Delegation

### Research and Development Team

```python
from deepagents import DeepAgent, Subagent

async def research_dev_team_example():
    """Main agent coordinates researcher and developer."""
    
    main_agent = DeepAgent.create(
        model="claude-sonnet-4-5-20250929",
        planning=True,
        system_prompt="""You are a project coordinator.
        
        You have two specialists:
        - researcher: Gathers information and best practices
        - developer: Implements solutions
        
        Delegate tasks to appropriate specialists.
        """,
        subagents={
            "researcher": Subagent(
                model="claude-sonnet-4-5-20250929",
                system_prompt="""You are a research specialist.
                
                When assigned research:
                1. Identify key concepts
                2. Find best practices
                3. Provide comprehensive findings
                4. Include examples and references
                """,
                planning=True
            ),
            "developer": Subagent(
                model="claude-sonnet-4-5-20250929",
                system_prompt="""You are a senior developer.
                
                When implementing:
                1. Follow best practices from research
                2. Write clean, tested code
                3. Add documentation
                4. Consider edge cases
                """,
                filesystem=True,
                planning=True
            )
        }
    )
    
    result = await main_agent.ainvoke("""
    Create an authentication system for our API.
    
    Steps:
    1. Research: Find best practices for JWT authentication
    2. Develop: Implement the auth system
    3. Document: Create usage guide
    """)
    
    print(result.content)
```

### Specialized Agent Pipeline

```python
async def agent_pipeline_example():
    """Chain of specialized agents."""
    
    coordinator = DeepAgent.create(
        model="claude-sonnet-4-5-20250929",
        system_prompt="You coordinate a pipeline of specialists.",
        subagents={
            "analyzer": Subagent(
                model="claude-sonnet-4-5-20250929",
                system_prompt="Analyze requirements and identify components.",
                planning=True
            ),
            "architect": Subagent(
                model="claude-sonnet-4-5-20250929",
                system_prompt="Design system architecture based on analysis.",
                planning=True,
                filesystem=True
            ),
            "implementer": Subagent(
                model="claude-sonnet-4-5-20250929",
                system_prompt="Implement the designed architecture.",
                filesystem=True
            ),
            "tester": Subagent(
                model="claude-sonnet-4-5-20250929",
                system_prompt="Create comprehensive tests.",
                filesystem=True
            )
        }
    )
    
    result = await coordinator.ainvoke("""
    Build a real-time chat application.
    
    Process:
    1. analyzer: Break down requirements
    2. architect: Design the system (save architecture.md)
    3. implementer: Build based on architecture
    4. tester: Create test suite
    """)
```

## Platform Integration

### Agent Factory with Database Config

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AgentConfig
from app.services.tool_registry import ToolRegistry

class AgentFactory:
    """Create agents from database configurations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tool_registry = ToolRegistry()
    
    async def create_from_db(self, agent_id: int) -> DeepAgent:
        """Build agent from database configuration."""
        
        # Load configuration
        config = await self.db.get(AgentConfig, agent_id)
        
        # Resolve tools
        tools = []
        for tool_name in config.tool_names:
            tool = self.tool_registry.get(tool_name)
            tools.append(tool)
        
        # Build subagents
        subagents = {}
        for sub_config in config.subagent_configs:
            sub_tools = [
                self.tool_registry.get(name) 
                for name in sub_config.tool_names
            ]
            
            subagents[sub_config.name] = Subagent(
                model=sub_config.model,
                system_prompt=sub_config.system_prompt,
                tools=sub_tools,
                planning=sub_config.enable_planning
            )
        
        # Create agent
        agent = DeepAgent.create(
            model=config.model_name,
            system_prompt=config.system_prompt,
            tools=tools,
            planning=config.enable_planning,
            filesystem=config.enable_filesystem,
            filesystem_config={
                "storage_path": f"./storage/agent_{agent_id}"
            },
            subagents=subagents
        )
        
        return agent

# Usage
async def use_factory_example(db: AsyncSession):
    factory = AgentFactory(db)
    agent = await factory.create_from_db(agent_id=1)
    result = await agent.ainvoke("Execute task")
```

### Execution Service with Tracing

```python
from datetime import datetime
from app.models import Execution, Trace

class ExecutionService:
    """Manage agent executions with full tracing."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def execute_agent(
        self,
        agent: DeepAgent,
        user_input: str,
        agent_id: int,
        user_id: int
    ) -> Execution:
        """Execute agent with comprehensive tracking."""
        
        # Create execution record
        execution = Execution(
            agent_id=agent_id,
            user_id=user_id,
            input=user_input,
            status="running",
            started_at=datetime.utcnow()
        )
        self.db.add(execution)
        await self.db.commit()
        
        try:
            # Stream execution
            async for event in agent.astream_events(user_input):
                # Store trace
                trace = Trace(
                    execution_id=execution.id,
                    event_type=event["event"],
                    event_name=event.get("name"),
                    data=event.get("data", {}),
                    timestamp=datetime.utcnow()
                )
                self.db.add(trace)
                
                # Commit incrementally for real-time updates
                await self.db.flush()
            
            # Update execution
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            
        except Exception as e:
            execution.status = "failed"
            execution.error = str(e)
            execution.completed_at = datetime.utcnow()
            raise
        
        finally:
            await self.db.commit()
        
        return execution

# Usage
async def execute_with_tracing_example(db: AsyncSession):
    factory = AgentFactory(db)
    service = ExecutionService(db)
    
    agent = await factory.create_from_db(agent_id=1)
    
    execution = await service.execute_agent(
        agent=agent,
        user_input="Analyze quarterly sales",
        agent_id=1,
        user_id=42
    )
    
    print(f"Execution {execution.id}: {execution.status}")
```

### WebSocket Streaming

```python
from fastapi import WebSocket

class StreamingExecutionService:
    """Stream agent execution to WebSocket clients."""
    
    async def stream_to_websocket(
        self,
        agent: DeepAgent,
        user_input: str,
        websocket: WebSocket
    ):
        """Stream execution events to connected client."""
        
        try:
            async for event in agent.astream_events(user_input):
                # Filter relevant events
                if event["event"] == "on_chat_model_stream":
                    # Stream tokens
                    await websocket.send_json({
                        "type": "token",
                        "content": event["data"]["chunk"]["content"]
                    })
                
                elif event["event"] == "on_tool_start":
                    # Notify tool usage
                    await websocket.send_json({
                        "type": "tool_start",
                        "tool": event["name"],
                        "input": event["data"]["input"]
                    })
                
                elif event["event"] == "on_tool_end":
                    # Send tool result
                    await websocket.send_json({
                        "type": "tool_end",
                        "tool": event["name"],
                        "output": event["data"]["output"]
                    })
            
            # Send completion
            await websocket.send_json({
                "type": "complete"
            })
        
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })

# FastAPI endpoint
@router.websocket("/agents/{agent_id}/execute")
async def execute_agent_ws(
    websocket: WebSocket,
    agent_id: int,
    db: AsyncSession = Depends(get_db)
):
    await websocket.accept()
    
    factory = AgentFactory(db)
    service = StreamingExecutionService()
    
    agent = await factory.create_from_db(agent_id)
    
    # Receive input
    data = await websocket.receive_json()
    user_input = data["input"]
    
    # Stream execution
    await service.stream_to_websocket(agent, user_input, websocket)
```

## Advanced Patterns

### Retry with Fallback

```python
async def execute_with_retry_and_fallback():
    """Execute with automatic retry and fallback agent."""
    
    # Primary agent with advanced features
    primary = DeepAgent.create(
        model="claude-sonnet-4-5-20250929",
        planning=True,
        filesystem=True,
        system_prompt="You are an advanced assistant with planning and file operations."
    )
    
    # Fallback agent with simpler config
    fallback = DeepAgent.create(
        model="claude-sonnet-4-5-20250929",
        system_prompt="You are a basic assistant."
    )
    
    async def execute_with_fallback(input: str, max_retries: int = 3):
        """Try primary, retry on failure, use fallback if needed."""
        
        last_error = None
        
        # Try primary agent
        for attempt in range(max_retries):
            try:
                result = await primary.ainvoke(input)
                return result
            except Exception as e:
                last_error = e
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # Use fallback
        try:
            return await fallback.ainvoke(input)
        except Exception as e:
            raise Exception(
                f"Both primary and fallback failed. Last error: {e}"
            ) from last_error
    
    result = await execute_with_fallback("Process this complex task")
    return result
```

### Parallel Agent Execution

```python
import asyncio

async def parallel_agents_example():
    """Execute multiple agents in parallel."""
    
    # Create specialized agents
    agents = {
        "summarizer": DeepAgent.create(
            model="claude-sonnet-4-5-20250929",
            system_prompt="You create concise summaries."
        ),
        "analyzer": DeepAgent.create(
            model="claude-sonnet-4-5-20250929",
            system_prompt="You perform detailed analysis."
        ),
        "critic": DeepAgent.create(
            model="claude-sonnet-4-5-20250929",
            system_prompt="You provide constructive criticism."
        )
    }
    
    document = "Long document text here..."
    
    # Execute all agents in parallel
    tasks = {
        name: agent.ainvoke(f"{prompt}\n\n{document}")
        for name, (agent, prompt) in {
            "summarizer": (agents["summarizer"], "Summarize this:"),
            "analyzer": (agents["analyzer"], "Analyze this:"),
            "critic": (agents["critic"], "Review this:")
        }.items()
    }
    
    results = await asyncio.gather(*tasks.values())
    
    # Combine results
    return {
        name: result 
        for name, result in zip(tasks.keys(), results)
    }
```

### Conditional Subagent Selection

```python
async def smart_delegation_example():
    """Agent selects appropriate subagent based on task type."""
    
    coordinator = DeepAgent.create(
        model="claude-sonnet-4-5-20250929",
        system_prompt="""You are a smart coordinator.
        
        Analyze the task type and delegate:
        - code_tasks -> developer
        - research_tasks -> researcher
        - design_tasks -> designer
        - data_tasks -> analyst
        
        Choose the best specialist for each task.
        """,
        subagents={
            "developer": Subagent(
                model="claude-sonnet-4-5-20250929",
                system_prompt="Expert in software development.",
                filesystem=True
            ),
            "researcher": Subagent(
                model="claude-sonnet-4-5-20250929",
                system_prompt="Expert in research and information gathering.",
                planning=True
            ),
            "designer": Subagent(
                model="claude-sonnet-4-5-20250929",
                system_prompt="Expert in UX/UI design.",
                planning=True
            ),
            "analyst": Subagent(
                model="claude-sonnet-4-5-20250929",
                system_prompt="Expert in data analysis.",
                filesystem=True
            )
        }
    )
    
    # Agent automatically selects appropriate subagent
    tasks = [
        "Implement a binary search function",  # -> developer
        "Research best practices for API design",  # -> researcher
        "Design a user onboarding flow",  # -> designer
        "Analyze this sales dataset"  # -> analyst
    ]
    
    for task in tasks:
        result = await coordinator.ainvoke(task)
        print(f"Task: {task}\nResult: {result.content}\n")
```

### State Persistence with Checkpointing

```python
from langgraph.checkpoint.memory import MemorySaver

async def stateful_agent_example():
    """Agent maintains state across executions."""
    
    # Create checkpointer
    checkpointer = MemorySaver()
    
    agent = DeepAgent.create(
        model="claude-sonnet-4-5-20250929",
        planning=True,
        checkpointer=checkpointer,
        system_prompt="""You maintain conversation context.
        
        Remember:
        - Previous user requests
        - Work you've completed
        - Ongoing projects
        """
    )
    
    # Session configuration
    config = {"configurable": {"thread_id": "user_123"}}
    
    # First interaction
    result1 = await agent.ainvoke(
        "Create a plan for building a blog platform",
        config=config
    )
    
    # Later interaction - agent remembers context
    result2 = await agent.ainvoke(
        "What was the first step in the plan we discussed?",
        config=config
    )
    
    # Agent recalls previous plan
    print(result2.content)
```

## Testing Examples

### Unit Testing Agents

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_planning_agent():
    """Test agent uses planning correctly."""
    
    agent = DeepAgent.create(
        model="claude-sonnet-4-5-20250929",
        planning=True,
        system_prompt="You create detailed plans."
    )
    
    result = await agent.ainvoke("Plan a web application")
    
    # Verify planning was used
    assert any(
        call.get("name") == "write_todos" 
        for call in result.additional_kwargs.get("tool_calls", [])
    )

@pytest.mark.asyncio
async def test_subagent_delegation():
    """Test main agent delegates to subagent."""
    
    # Mock subagent
    mock_subagent = AsyncMock()
    mock_subagent.ainvoke.return_value = MagicMock(
        content="Subagent result"
    )
    
    agent = DeepAgent.create(
        model="claude-sonnet-4-5-20250929",
        subagents={"specialist": mock_subagent}
    )
    
    result = await agent.ainvoke("Use specialist subagent for this task")
    
    # Verify subagent was called
    mock_subagent.ainvoke.assert_called_once()
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_full_execution_flow(db_session):
    """Test complete execution with database."""
    
    # Setup
    agent_config = AgentConfig(
        name="Test Agent",
        model_name="claude-sonnet-4-5-20250929",
        enable_planning=True,
        user_id=1
    )
    db_session.add(agent_config)
    await db_session.commit()
    
    # Create and execute
    factory = AgentFactory(db_session)
    service = ExecutionService(db_session)
    
    agent = await factory.create_from_db(agent_config.id)
    execution = await service.execute_agent(
        agent=agent,
        user_input="Create a test plan",
        agent_id=agent_config.id,
        user_id=1
    )
    
    # Verify
    assert execution.status == "completed"
    assert execution.completed_at is not None
    
    # Check traces were created
    traces = await db_session.execute(
        select(Trace).where(Trace.execution_id == execution.id)
    )
    assert len(traces.scalars().all()) > 0
```

---

# Intermediate Examples

## State Management with TypedDict

```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from deepagents import DeepAgent

class AgentState(TypedDict):
    """Type-safe agent state with custom reducers."""
    messages: Annotated[list[BaseMessage], add_messages]  # Append messages
    todos: Annotated[list[dict], lambda x, y: y]  # Replace strategy
    context: dict
    user_preferences: Annotated[dict, lambda x, y: {**x, **y}]  # Merge strategy

async def stateful_agent_example():
    agent = DeepAgent.create(
        model="claude-sonnet-4-5-20250929",
        state_schema=AgentState,
        planning=True
    )
    
    result1 = await agent.ainvoke(
        "My name is Alice and I prefer dark mode",
        config={"configurable": {"thread_id": "user_123"}}
    )
    
    result2 = await agent.ainvoke(
        "What's my name?",
        config={"configurable": {"thread_id": "user_123"}}
    )
    print(result2.content)  # "Your name is Alice"
```

## Advanced Planning with Dependencies

```python
async def advanced_planning():
    agent = DeepAgent.create(
        model="claude-sonnet-4-5-20250929",
        planning=True,
        system_prompt="""Planning Guidelines:
        1. Break tasks into < 20 actionable todos
        2. Use dependencies [0, 1] for ordering
        3. Update status: pending -> in_progress -> completed"""
    )
    
    result = await agent.ainvoke("Build e-commerce platform with auth, catalog, cart, payment")
    todos = result.metadata.get("todos", [])
    for i, todo in enumerate(todos):
        print(f"{i}. {todo['description']} (deps: {todo.get('dependencies', [])})")
```

## Error Handling and Retry

```python
async def execute_with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)

async def resilient_agent():
    primary = DeepAgent.create(model="claude-sonnet-4-5-20250929", planning=True)
    fallback = DeepAgent.create(model="claude-haiku-4-5-20250929")
    
    try:
        return await execute_with_retry(lambda: primary.ainvoke("Complex task"))
    except:
        return await fallback.ainvoke("Simple guidance")
```

## Middleware Integration

```python
from deepagents.middleware import LLMToolSelectorMiddleware

async def middleware_example():
    tool_selector = LLMToolSelectorMiddleware(
        all_tools=all_100_tools,
        max_tools=10,
        selection_model="claude-haiku-4-5-20250929"
    )
    
    agent = DeepAgent.create(
        model="claude-sonnet-4-5-20250929",
        middleware=[tool_selector],
        tools=[]  # Injected by middleware
    )
```

---

# Advanced Examples

## Multi-Agent Workflows

```python
async def multi_agent_workflow():
    agents = {
        "analyzer": DeepAgent.create(model="claude-sonnet-4-5-20250929", planning=True),
        "designer": DeepAgent.create(model="claude-sonnet-4-5-20250929", filesystem=True),
        "implementer": DeepAgent.create(model="claude-sonnet-4-5-20250929", filesystem=True)
    }
    
    results = await asyncio.gather(
        agents["analyzer"].ainvoke("Analyze requirements"),
        agents["designer"].ainvoke("Design architecture"),
        agents["implementer"].ainvoke("Plan implementation")
    )
    
    coordinator = DeepAgent.create(model="claude-sonnet-4-5-20250929", filesystem=True)
    return await coordinator.ainvoke(f"Integrate: {results}")
```

## RAG Integration

```python
from langchain_community.vectorstores import FAISS
from langchain_core.tools import tool

vector_store = FAISS.from_texts(["doc1", "doc2"], embeddings)

@tool("search_kb")
async def search_kb(query: str) -> list[dict]:
    """Search knowledge base."""
    results = await vector_store.asimilarity_search_with_score(query, k=5)
    return [{"content": doc.page_content, "score": score} for doc, score in results]

agent = DeepAgent.create(
    model="claude-sonnet-4-5-20250929",
    tools=[search_kb],
    system_prompt="ALWAYS search KB before answering. Cite sources."
)
```

## MCP Integration

```python
from deepagents import async_create_deep_agent

agent = await async_create_deep_agent(
    model="claude-sonnet-4-5-20250929",
    mcp_servers={
        "playwright": {"command": "npx", "args": ["-y", "@executeautomation/playwright-mcp-server"]},
        "memory": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-memory"]}
    }
)
```

## LangSmith Evaluation

```python
import os
from langsmith import Client

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-key"
client = Client()

agent = DeepAgent.create(model="claude-sonnet-4-5-20250929", planning=True)
result = await agent.ainvoke("Task", config={"run_name": "eval", "tags": ["prod"]})

client.create_feedback(run_id=result.run_id, key="quality", score=0.95)
```
