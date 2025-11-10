"""
Tests for Planning Tool Integration.

Tests the deepagents planning feature integration, including:
- Agent creation with planning enabled
- Plan trace event detection
- Plan state updates
"""

import os
from unittest.mock import AsyncMock, Mock, patch

import pytest

from deepagents_integration.executor import AgentExecutor
from deepagents_integration.factory import AgentFactory
from models.agent import Agent as AgentModel


@pytest.fixture
def agent_factory():
    """Create an AgentFactory instance for testing."""
    return AgentFactory()


@pytest.fixture
def agent_executor():
    """Create an AgentExecutor instance for testing."""
    return AgentExecutor()


@pytest.fixture
def planning_agent_config():
    """Create an agent configuration with planning enabled."""
    return AgentModel(
        id=1,
        name="Planning Agent",
        description="An agent with planning enabled",
        model_provider="anthropic",
        model_name="claude-3-5-sonnet-20241022",
        temperature=0.7,
        max_tokens=4096,
        system_prompt="You are a helpful planning assistant.",
        planning_enabled=True,  # Enable planning
        filesystem_enabled=False,
        additional_config={},
        created_by_id=1,
        is_active=True,
    )


@pytest.fixture
def non_planning_agent_config():
    """Create an agent configuration with planning disabled."""
    return AgentModel(
        id=2,
        name="Non-Planning Agent",
        description="An agent without planning",
        model_provider="anthropic",
        model_name="claude-3-5-sonnet-20241022",
        temperature=0.7,
        max_tokens=4096,
        system_prompt="You are a helpful assistant.",
        planning_enabled=False,  # Disable planning
        filesystem_enabled=False,
        additional_config={},
        created_by_id=1,
        is_active=True,
    )


# Agent Factory Planning Tests


@pytest.mark.asyncio
async def test_create_agent_with_planning_enabled(agent_factory, planning_agent_config):
    """
    Test that agents are created when planning_enabled=True.

    Note: In deepagents, the write_todos planning tool is ALWAYS enabled by default.
    The planning_enabled flag is informational for the UI, not a runtime configuration.
    """
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("deepagents_integration.factory.create_deep_agent") as mock_create:
            mock_agent = AsyncMock()
            mock_create.return_value = mock_agent

            agent = await agent_factory.create_agent(planning_agent_config)

            # Verify create_deep_agent was called
            mock_create.assert_called_once()

            # Agent is created successfully (planning is always available)
            assert agent is not None


@pytest.mark.asyncio
async def test_create_agent_with_planning_disabled(
    agent_factory, non_planning_agent_config
):
    """
    Test that agents are created when planning_enabled=False.

    Note: In deepagents, the write_todos tool is always included by default.
    The planning_enabled flag is informational. To actually disable planning,
    the system_prompt could instruct the agent not to use write_todos.
    """
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("deepagents_integration.factory.create_deep_agent") as mock_create:
            mock_agent = AsyncMock()
            mock_create.return_value = mock_agent

            agent = await agent_factory.create_agent(non_planning_agent_config)

            # Verify create_deep_agent was called
            mock_create.assert_called_once()

            # Agent is created successfully (planning tools are always available)
            assert agent is not None


@pytest.mark.asyncio
async def test_planning_enabled_with_filesystem(agent_factory, planning_agent_config):
    """
    Test that agents can be created with both planning and filesystem enabled.

    Note: In deepagents, both features (write_todos and file editing tools)
    are ALWAYS enabled by default. These flags are informational.
    """
    planning_agent_config.filesystem_enabled = True

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("deepagents_integration.factory.create_deep_agent") as mock_create:
            mock_agent = AsyncMock()
            mock_create.return_value = mock_agent

            agent = await agent_factory.create_agent(planning_agent_config)

            # Verify agent was created (both features are always available)
            assert agent is not None


# Executor Planning Trace Tests


def test_determine_event_type_for_plan_update(agent_executor):
    """
    Test that plan update events are correctly identified.

    When the agent calls write_todos, the event should be classified
    as a 'plan_update' event type.
    """
    # Simulate a write_todos tool call event
    plan_event = {
        "tool": "write_todos",
        "todos": [
            {"id": 1, "description": "Research the topic", "status": "pending"},
            {"id": 2, "description": "Write the summary", "status": "pending"},
        ],
    }

    event_type = agent_executor._determine_event_type(plan_event)
    assert event_type == "plan_update"


def test_determine_event_type_for_plan_state(agent_executor):
    """
    Test that plan state events are correctly identified.

    deepagents may emit plan state updates with type='plan_state'.
    """
    plan_state_event = {
        "type": "plan_state",
        "todos": [
            {"id": 1, "description": "Task 1", "status": "completed"},
            {"id": 2, "description": "Task 2", "status": "in_progress"},
        ],
    }

    event_type = agent_executor._determine_event_type(plan_state_event)
    assert event_type == "plan_update"


def test_determine_event_type_for_tool_call(agent_executor):
    """
    Test that non-planning tool calls are correctly identified.

    Regular tool calls should not be classified as plan updates.
    """
    tool_call_event = {
        "tool_call": {
            "name": "search",
            "arguments": {"query": "test"},
        }
    }

    event_type = agent_executor._determine_event_type(tool_call_event)
    assert event_type == "tool_call"


def test_determine_event_type_for_llm_response(agent_executor):
    """
    Test that LLM responses are correctly identified.
    """
    llm_event = {"messages": [{"role": "assistant", "content": "Hello"}]}

    event_type = agent_executor._determine_event_type(llm_event)
    assert event_type == "llm_response"


# Integration Tests


@pytest.mark.asyncio
async def test_planning_agent_execution_flow(agent_factory, agent_executor):
    """
    Test the full flow of creating and executing a planning agent.

    This integration test verifies:
    1. Planning agent is created successfully
    2. Agent execution captures plan updates from write_todos tool
    3. Plan trace events are properly formatted

    Note: Planning tools are always available in deepagents by default.
    """
    planning_config = AgentModel(
        id=1,
        name="Test Planning Agent",
        model_provider="anthropic",
        model_name="claude-3-5-sonnet-20241022",
        temperature=0.7,
        max_tokens=4096,
        system_prompt="Break down tasks into steps.",
        planning_enabled=True,
        filesystem_enabled=False,
        additional_config={},
        created_by_id=1,
        is_active=True,
    )

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("deepagents_integration.factory.create_deep_agent") as mock_create:
            # Mock agent that returns plan events
            mock_agent = AsyncMock()

            # Simulate agent stream with plan update
            async def mock_stream(*args, **kwargs):
                """Simulate agent streaming with plan updates."""
                yield {
                    "tool": "write_todos",
                    "todos": [
                        {"id": 1, "description": "Analyze the problem", "status": "pending"},
                        {"id": 2, "description": "Design solution", "status": "pending"},
                        {"id": 3, "description": "Implement solution", "status": "pending"},
                    ],
                }
                yield {
                    "messages": [
                        {"role": "assistant", "content": "I've created a plan with 3 steps."}
                    ]
                }

            mock_agent.astream = mock_stream
            mock_create.return_value = mock_agent

            # Create agent
            agent = await agent_factory.create_agent(planning_config)

            # Verify agent was created
            assert agent is not None

            # Mock database operations
            mock_db = AsyncMock()

            # Execute agent and collect traces
            traces = []
            async for trace in agent_executor.execute_agent(
                agent, "Create a plan to solve this problem", execution_id=1, db=mock_db
            ):
                traces.append(trace)

            # Verify we got plan_update trace
            plan_traces = [t for t in traces if t["event_type"] == "plan_update"]
            assert len(plan_traces) > 0

            # Verify plan trace has correct structure
            plan_trace = plan_traces[0]
            assert "content" in plan_trace
            assert "todos" in plan_trace["content"]
            assert len(plan_trace["content"]["todos"]) == 3


@pytest.mark.asyncio
async def test_plan_trace_format(agent_executor):
    """
    Test that plan traces are formatted correctly.

    Plan traces should have:
    - sequence_number
    - timestamp
    - event_type = 'plan_update'
    - content with todos array
    """
    # Mock agent with plan update
    mock_agent = AsyncMock()

    async def mock_stream(*args, **kwargs):
        yield {
            "tool": "write_todos",
            "todos": [
                {"id": 1, "description": "Step 1", "status": "pending"},
            ],
        }

    mock_agent.astream = mock_stream

    # Mock database
    mock_db = AsyncMock()

    # Execute and collect traces
    traces = []
    async for trace in agent_executor.execute_agent(
        mock_agent, "Test prompt", execution_id=1, db=mock_db
    ):
        traces.append(trace)

    # Find plan trace
    plan_traces = [t for t in traces if t["event_type"] == "plan_update"]
    assert len(plan_traces) == 1

    plan_trace = plan_traces[0]

    # Verify structure
    assert "sequence_number" in plan_trace
    assert "timestamp" in plan_trace
    assert plan_trace["event_type"] == "plan_update"
    assert "content" in plan_trace
    assert "tool" in plan_trace["content"]
    assert plan_trace["content"]["tool"] == "write_todos"
    assert "todos" in plan_trace["content"]
    assert isinstance(plan_trace["content"]["todos"], list)


@pytest.mark.asyncio
async def test_plan_status_transitions():
    """
    Test that plan todo status transitions are tracked.

    Todos can transition through states:
    - pending -> in_progress -> completed
    - pending -> blocked
    """
    executor = AgentExecutor()

    # Initial plan
    initial_plan_event = {
        "tool": "write_todos",
        "todos": [
            {"id": 1, "description": "Task 1", "status": "pending"},
            {"id": 2, "description": "Task 2", "status": "pending"},
        ],
    }

    # Updated plan
    updated_plan_event = {
        "tool": "write_todos",
        "todos": [
            {"id": 1, "description": "Task 1", "status": "completed"},
            {"id": 2, "description": "Task 2", "status": "in_progress"},
        ],
    }

    # Both should be recognized as plan updates
    assert executor._determine_event_type(initial_plan_event) == "plan_update"
    assert executor._determine_event_type(updated_plan_event) == "plan_update"
