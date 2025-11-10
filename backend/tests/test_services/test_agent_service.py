"""
Comprehensive tests for Agent Service layer.

Tests all business logic for agent CRUD operations, including:
- Agent creation with validation
- Agent retrieval by ID and listing
- Agent updates (full and partial)
- Agent deletion (soft and hard)
- Agent-tool associations
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent import Agent, AgentTool
from models.tool import Tool
from models.user import User
from schemas.agent import AgentCreate, AgentUpdate
from services.agent_service import AgentService, AgentNotFoundError, AgentValidationError


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user for agent ownership."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password_here",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_tool(db_session: AsyncSession, test_user: User) -> Tool:
    """Create a test tool for agent-tool associations."""
    tool = Tool(
        name="test_tool",
        description="A test tool",
        tool_type="builtin",
        configuration={"api_key": "test"},
        schema_definition={"type": "object"},
        created_by_id=test_user.id,
        is_active=True,
    )
    db_session.add(tool)
    await db_session.commit()
    await db_session.refresh(tool)
    return tool


@pytest.fixture
async def sample_agent_data() -> AgentCreate:
    """Create sample agent data for testing."""
    return AgentCreate(
        name="Test Agent",
        description="A test agent",
        model_provider="anthropic",
        model_name="claude-3-5-sonnet-20241022",
        temperature=0.7,
        max_tokens=4096,
        system_prompt="You are a helpful assistant.",
        planning_enabled=True,
        filesystem_enabled=False,
        additional_config={"max_iterations": 10},
    )


@pytest.fixture
def agent_service() -> AgentService:
    """Create an instance of AgentService."""
    return AgentService()


# ============================================================================
# Create Agent Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_agent_success(
    db_session: AsyncSession,
    agent_service: AgentService,
    test_user: User,
    sample_agent_data: AgentCreate,
):
    """Test successful agent creation."""
    agent = await agent_service.create_agent(
        db=db_session,
        agent_data=sample_agent_data,
        created_by_id=test_user.id,
    )

    assert agent.id is not None
    assert agent.name == sample_agent_data.name
    assert agent.description == sample_agent_data.description
    assert agent.model_provider == sample_agent_data.model_provider
    assert agent.model_name == sample_agent_data.model_name
    assert agent.temperature == sample_agent_data.temperature
    assert agent.max_tokens == sample_agent_data.max_tokens
    assert agent.system_prompt == sample_agent_data.system_prompt
    assert agent.planning_enabled == sample_agent_data.planning_enabled
    assert agent.filesystem_enabled == sample_agent_data.filesystem_enabled
    assert agent.additional_config == sample_agent_data.additional_config
    assert agent.created_by_id == test_user.id
    assert agent.is_active is True
    assert agent.created_at is not None


@pytest.mark.asyncio
async def test_create_agent_with_invalid_temperature(
    db_session: AsyncSession,
    agent_service: AgentService,
    test_user: User,
    sample_agent_data: AgentCreate,
):
    """Test agent creation fails with invalid temperature."""
    sample_agent_data.temperature = 2.5  # Invalid: > 2.0

    with pytest.raises(AgentValidationError) as exc_info:
        await agent_service.create_agent(
            db=db_session,
            agent_data=sample_agent_data,
            created_by_id=test_user.id,
        )

    assert "temperature" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_create_agent_with_invalid_max_tokens(
    db_session: AsyncSession,
    agent_service: AgentService,
    test_user: User,
    sample_agent_data: AgentCreate,
):
    """Test agent creation fails with invalid max_tokens."""
    sample_agent_data.max_tokens = -100  # Invalid: must be positive

    with pytest.raises(AgentValidationError) as exc_info:
        await agent_service.create_agent(
            db=db_session,
            agent_data=sample_agent_data,
            created_by_id=test_user.id,
        )

    assert "max_tokens" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_create_agent_duplicate_name_same_user(
    db_session: AsyncSession,
    agent_service: AgentService,
    test_user: User,
    sample_agent_data: AgentCreate,
):
    """Test agent creation fails with duplicate name for same user."""
    # Create first agent
    await agent_service.create_agent(
        db=db_session,
        agent_data=sample_agent_data,
        created_by_id=test_user.id,
    )

    # Try to create second agent with same name
    with pytest.raises(AgentValidationError) as exc_info:
        await agent_service.create_agent(
            db=db_session,
            agent_data=sample_agent_data,
            created_by_id=test_user.id,
        )

    assert "name" in str(exc_info.value).lower()
    assert "already exists" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_create_agent_duplicate_name_different_users(
    db_session: AsyncSession,
    agent_service: AgentService,
    test_user: User,
    sample_agent_data: AgentCreate,
):
    """Test agent creation succeeds with duplicate name for different users."""
    # Create second user
    user2 = User(
        username="testuser2",
        email="test2@example.com",
        hashed_password="hashed_password_here",
        is_active=True,
    )
    db_session.add(user2)
    await db_session.commit()
    await db_session.refresh(user2)

    # Create agent for first user
    agent1 = await agent_service.create_agent(
        db=db_session,
        agent_data=sample_agent_data,
        created_by_id=test_user.id,
    )

    # Create agent with same name for second user (should succeed)
    agent2 = await agent_service.create_agent(
        db=db_session,
        agent_data=sample_agent_data,
        created_by_id=user2.id,
    )

    assert agent1.id != agent2.id
    assert agent1.name == agent2.name
    assert agent1.created_by_id != agent2.created_by_id


# ============================================================================
# Get Agent Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_agent_by_id_success(
    db_session: AsyncSession,
    agent_service: AgentService,
    test_user: User,
    sample_agent_data: AgentCreate,
):
    """Test successful agent retrieval by ID."""
    created_agent = await agent_service.create_agent(
        db=db_session,
        agent_data=sample_agent_data,
        created_by_id=test_user.id,
    )

    retrieved_agent = await agent_service.get_agent(
        db=db_session,
        agent_id=created_agent.id,
    )

    assert retrieved_agent is not None
    assert retrieved_agent.id == created_agent.id
    assert retrieved_agent.name == created_agent.name


@pytest.mark.asyncio
async def test_get_agent_by_id_not_found(
    db_session: AsyncSession,
    agent_service: AgentService,
):
    """Test agent retrieval fails for non-existent ID."""
    retrieved_agent = await agent_service.get_agent(
        db=db_session,
        agent_id=99999,
    )

    assert retrieved_agent is None


@pytest.mark.asyncio
async def test_get_agent_excludes_inactive_by_default(
    db_session: AsyncSession,
    agent_service: AgentService,
    test_user: User,
    sample_agent_data: AgentCreate,
):
    """Test that get_agent excludes inactive agents by default."""
    # Create and soft delete an agent
    agent = await agent_service.create_agent(
        db=db_session,
        agent_data=sample_agent_data,
        created_by_id=test_user.id,
    )

    await agent_service.delete_agent(
        db=db_session,
        agent_id=agent.id,
        hard_delete=False,
    )

    # Try to retrieve (should return None)
    retrieved_agent = await agent_service.get_agent(
        db=db_session,
        agent_id=agent.id,
    )

    assert retrieved_agent is None


@pytest.mark.asyncio
async def test_get_agent_includes_inactive_when_requested(
    db_session: AsyncSession,
    agent_service: AgentService,
    test_user: User,
    sample_agent_data: AgentCreate,
):
    """Test that get_agent can include inactive agents when requested."""
    # Create and soft delete an agent
    agent = await agent_service.create_agent(
        db=db_session,
        agent_data=sample_agent_data,
        created_by_id=test_user.id,
    )

    await agent_service.delete_agent(
        db=db_session,
        agent_id=agent.id,
        hard_delete=False,
    )

    # Try to retrieve with include_inactive=True
    retrieved_agent = await agent_service.get_agent(
        db=db_session,
        agent_id=agent.id,
        include_inactive=True,
    )

    assert retrieved_agent is not None
    assert retrieved_agent.id == agent.id
    assert retrieved_agent.is_active is False


# ============================================================================
# List Agents Tests
# ============================================================================


@pytest.mark.asyncio
async def test_list_agents_empty(
    db_session: AsyncSession,
    agent_service: AgentService,
):
    """Test listing agents returns empty list when no agents exist."""
    agents = await agent_service.list_agents(db=db_session)

    assert agents == []


@pytest.mark.asyncio
async def test_list_agents_with_pagination(
    db_session: AsyncSession,
    agent_service: AgentService,
    test_user: User,
):
    """Test listing agents with pagination parameters."""
    # Create 5 agents
    for i in range(5):
        agent_data = AgentCreate(
            name=f"Agent {i}",
            description=f"Test agent {i}",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
        )
        await agent_service.create_agent(
            db=db_session,
            agent_data=agent_data,
            created_by_id=test_user.id,
        )

    # Test pagination
    page1 = await agent_service.list_agents(db=db_session, skip=0, limit=2)
    assert len(page1) == 2

    page2 = await agent_service.list_agents(db=db_session, skip=2, limit=2)
    assert len(page2) == 2

    page3 = await agent_service.list_agents(db=db_session, skip=4, limit=2)
    assert len(page3) == 1

    # Verify no overlap
    page1_ids = {a.id for a in page1}
    page2_ids = {a.id for a in page2}
    assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.asyncio
async def test_list_agents_filter_by_is_active(
    db_session: AsyncSession,
    agent_service: AgentService,
    test_user: User,
):
    """Test filtering agents by is_active flag."""
    # Create 3 active agents
    for i in range(3):
        agent_data = AgentCreate(
            name=f"Active Agent {i}",
            description=f"Active agent {i}",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
        )
        await agent_service.create_agent(
            db=db_session,
            agent_data=agent_data,
            created_by_id=test_user.id,
        )

    # Create 2 inactive agents
    for i in range(2):
        agent_data = AgentCreate(
            name=f"Inactive Agent {i}",
            description=f"Inactive agent {i}",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
        )
        agent = await agent_service.create_agent(
            db=db_session,
            agent_data=agent_data,
            created_by_id=test_user.id,
        )
        await agent_service.delete_agent(
            db=db_session,
            agent_id=agent.id,
            hard_delete=False,
        )

    # Test filter for active only
    active_agents = await agent_service.list_agents(db=db_session, is_active=True)
    assert len(active_agents) == 3
    assert all(a.is_active for a in active_agents)

    # Test filter for inactive only
    inactive_agents = await agent_service.list_agents(db=db_session, is_active=False)
    assert len(inactive_agents) == 2
    assert all(not a.is_active for a in inactive_agents)

    # Test no filter (default: active only)
    all_active = await agent_service.list_agents(db=db_session)
    assert len(all_active) == 3


@pytest.mark.asyncio
async def test_list_agents_filter_by_created_by_id(
    db_session: AsyncSession,
    agent_service: AgentService,
    test_user: User,
):
    """Test filtering agents by creator user ID."""
    # Create second user
    user2 = User(
        username="testuser2",
        email="test2@example.com",
        hashed_password="hashed_password_here",
        is_active=True,
    )
    db_session.add(user2)
    await db_session.commit()
    await db_session.refresh(user2)

    # Create 2 agents for user1
    for i in range(2):
        agent_data = AgentCreate(
            name=f"User1 Agent {i}",
            description=f"Agent for user 1",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
        )
        await agent_service.create_agent(
            db=db_session,
            agent_data=agent_data,
            created_by_id=test_user.id,
        )

    # Create 3 agents for user2
    for i in range(3):
        agent_data = AgentCreate(
            name=f"User2 Agent {i}",
            description=f"Agent for user 2",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
        )
        await agent_service.create_agent(
            db=db_session,
            agent_data=agent_data,
            created_by_id=user2.id,
        )

    # Test filter by user1
    user1_agents = await agent_service.list_agents(
        db=db_session,
        created_by_id=test_user.id,
    )
    assert len(user1_agents) == 2
    assert all(a.created_by_id == test_user.id for a in user1_agents)

    # Test filter by user2
    user2_agents = await agent_service.list_agents(
        db=db_session,
        created_by_id=user2.id,
    )
    assert len(user2_agents) == 3
    assert all(a.created_by_id == user2.id for a in user2_agents)


# ============================================================================
# Update Agent Tests
# ============================================================================


@pytest.mark.asyncio
async def test_update_agent_success(
    db_session: AsyncSession,
    agent_service: AgentService,
    test_user: User,
    sample_agent_data: AgentCreate,
):
    """Test successful full agent update."""
    # Create agent
    agent = await agent_service.create_agent(
        db=db_session,
        agent_data=sample_agent_data,
        created_by_id=test_user.id,
    )

    # Update agent
    update_data = AgentUpdate(
        name="Updated Agent",
        description="Updated description",
        temperature=0.9,
        max_tokens=2048,
    )

    updated_agent = await agent_service.update_agent(
        db=db_session,
        agent_id=agent.id,
        agent_update=update_data,
    )

    assert updated_agent.id == agent.id
    assert updated_agent.name == "Updated Agent"
    assert updated_agent.description == "Updated description"
    assert updated_agent.temperature == 0.9
    assert updated_agent.max_tokens == 2048
    # Unchanged fields should remain the same
    assert updated_agent.model_provider == sample_agent_data.model_provider
    assert updated_agent.model_name == sample_agent_data.model_name


@pytest.mark.asyncio
async def test_update_agent_not_found(
    db_session: AsyncSession,
    agent_service: AgentService,
):
    """Test update fails for non-existent agent."""
    update_data = AgentUpdate(name="Updated Agent")

    with pytest.raises(AgentNotFoundError):
        await agent_service.update_agent(
            db=db_session,
            agent_id=99999,
            agent_update=update_data,
        )


@pytest.mark.asyncio
async def test_update_agent_partial_update(
    db_session: AsyncSession,
    agent_service: AgentService,
    test_user: User,
    sample_agent_data: AgentCreate,
):
    """Test partial agent update (only some fields)."""
    # Create agent
    agent = await agent_service.create_agent(
        db=db_session,
        agent_data=sample_agent_data,
        created_by_id=test_user.id,
    )

    original_name = agent.name
    original_temperature = agent.temperature

    # Update only description
    update_data = AgentUpdate(description="Only update description")

    updated_agent = await agent_service.update_agent(
        db=db_session,
        agent_id=agent.id,
        agent_update=update_data,
    )

    assert updated_agent.description == "Only update description"
    # Other fields should remain unchanged
    assert updated_agent.name == original_name
    assert updated_agent.temperature == original_temperature


@pytest.mark.asyncio
async def test_update_agent_with_invalid_temperature(
    db_session: AsyncSession,
    agent_service: AgentService,
    test_user: User,
    sample_agent_data: AgentCreate,
):
    """Test update fails with invalid temperature."""
    from pydantic import ValidationError as PydanticValidationError

    # Create agent
    agent = await agent_service.create_agent(
        db=db_session,
        agent_data=sample_agent_data,
        created_by_id=test_user.id,
    )

    # Try to create AgentUpdate with invalid temperature (should fail in Pydantic)
    with pytest.raises(PydanticValidationError):
        update_data = AgentUpdate(temperature=3.0)  # Invalid: > 1.0


@pytest.mark.asyncio
async def test_update_agent_duplicate_name(
    db_session: AsyncSession,
    agent_service: AgentService,
    test_user: User,
):
    """Test update fails when trying to use duplicate name."""
    # Create two agents
    agent1_data = AgentCreate(
        name="Agent 1",
        model_provider="anthropic",
        model_name="claude-3-5-sonnet-20241022",
        temperature=0.7,
    )
    agent1 = await agent_service.create_agent(
        db=db_session,
        agent_data=agent1_data,
        created_by_id=test_user.id,
    )

    agent2_data = AgentCreate(
        name="Agent 2",
        model_provider="anthropic",
        model_name="claude-3-5-sonnet-20241022",
        temperature=0.7,
    )
    agent2 = await agent_service.create_agent(
        db=db_session,
        agent_data=agent2_data,
        created_by_id=test_user.id,
    )

    # Try to update agent2 to have same name as agent1
    update_data = AgentUpdate(name="Agent 1")

    with pytest.raises(AgentValidationError) as exc_info:
        await agent_service.update_agent(
            db=db_session,
            agent_id=agent2.id,
            agent_update=update_data,
        )

    assert "name" in str(exc_info.value).lower()


# ============================================================================
# Delete Agent Tests
# ============================================================================


@pytest.mark.asyncio
async def test_delete_agent_soft_delete_success(
    db_session: AsyncSession,
    agent_service: AgentService,
    test_user: User,
    sample_agent_data: AgentCreate,
):
    """Test soft delete sets is_active to False."""
    # Create agent
    agent = await agent_service.create_agent(
        db=db_session,
        agent_data=sample_agent_data,
        created_by_id=test_user.id,
    )

    # Soft delete
    result = await agent_service.delete_agent(
        db=db_session,
        agent_id=agent.id,
        hard_delete=False,
    )

    assert result is True

    # Verify agent still exists but is inactive
    stmt = select(Agent).where(Agent.id == agent.id)
    result = await db_session.execute(stmt)
    deleted_agent = result.scalar_one_or_none()

    assert deleted_agent is not None
    assert deleted_agent.is_active is False


@pytest.mark.asyncio
async def test_delete_agent_hard_delete_success(
    db_session: AsyncSession,
    agent_service: AgentService,
    test_user: User,
    sample_agent_data: AgentCreate,
):
    """Test hard delete removes agent from database."""
    # Create agent
    agent = await agent_service.create_agent(
        db=db_session,
        agent_data=sample_agent_data,
        created_by_id=test_user.id,
    )

    # Hard delete
    result = await agent_service.delete_agent(
        db=db_session,
        agent_id=agent.id,
        hard_delete=True,
    )

    assert result is True

    # Verify agent no longer exists
    stmt = select(Agent).where(Agent.id == agent.id)
    result = await db_session.execute(stmt)
    deleted_agent = result.scalar_one_or_none()

    assert deleted_agent is None


@pytest.mark.asyncio
async def test_delete_agent_not_found(
    db_session: AsyncSession,
    agent_service: AgentService,
):
    """Test delete fails for non-existent agent."""
    with pytest.raises(AgentNotFoundError):
        await agent_service.delete_agent(
            db=db_session,
            agent_id=99999,
            hard_delete=False,
        )


# ============================================================================
# Agent-Tool Association Tests
# ============================================================================


@pytest.mark.asyncio
async def test_add_tools_to_agent(
    db_session: AsyncSession,
    agent_service: AgentService,
    test_user: User,
    sample_agent_data: AgentCreate,
    test_tool: Tool,
):
    """Test adding tools to an agent."""
    # Create agent
    agent = await agent_service.create_agent(
        db=db_session,
        agent_data=sample_agent_data,
        created_by_id=test_user.id,
    )

    # Add tool to agent
    updated_agent = await agent_service.add_tools_to_agent(
        db=db_session,
        agent_id=agent.id,
        tool_ids=[test_tool.id],
        configurations={test_tool.id: {"custom_param": "value"}},
    )

    # Verify tool was added
    stmt = select(AgentTool).where(
        AgentTool.agent_id == agent.id,
        AgentTool.tool_id == test_tool.id,
    )
    result = await db_session.execute(stmt)
    agent_tool = result.scalar_one_or_none()

    assert agent_tool is not None
    assert agent_tool.configuration_override == {"custom_param": "value"}


@pytest.mark.asyncio
async def test_add_multiple_tools_to_agent(
    db_session: AsyncSession,
    agent_service: AgentService,
    test_user: User,
    sample_agent_data: AgentCreate,
):
    """Test adding multiple tools to an agent."""
    # Create agent
    agent = await agent_service.create_agent(
        db=db_session,
        agent_data=sample_agent_data,
        created_by_id=test_user.id,
    )

    # Create 3 tools
    tool_ids = []
    for i in range(3):
        tool = Tool(
            name=f"Tool {i}",
            tool_type="builtin",
            configuration={},
            schema_definition={},
            created_by_id=test_user.id,
        )
        db_session.add(tool)
        await db_session.commit()
        await db_session.refresh(tool)
        tool_ids.append(tool.id)

    # Add all tools to agent
    updated_agent = await agent_service.add_tools_to_agent(
        db=db_session,
        agent_id=agent.id,
        tool_ids=tool_ids,
    )

    # Verify all tools were added
    stmt = select(AgentTool).where(AgentTool.agent_id == agent.id)
    result = await db_session.execute(stmt)
    agent_tools = result.scalars().all()

    assert len(agent_tools) == 3


@pytest.mark.asyncio
async def test_add_tools_to_nonexistent_agent(
    db_session: AsyncSession,
    agent_service: AgentService,
    test_tool: Tool,
):
    """Test adding tools fails for non-existent agent."""
    with pytest.raises(AgentNotFoundError):
        await agent_service.add_tools_to_agent(
            db=db_session,
            agent_id=99999,
            tool_ids=[test_tool.id],
        )


@pytest.mark.asyncio
async def test_remove_tools_from_agent(
    db_session: AsyncSession,
    agent_service: AgentService,
    test_user: User,
    sample_agent_data: AgentCreate,
    test_tool: Tool,
):
    """Test removing tools from an agent."""
    # Create agent
    agent = await agent_service.create_agent(
        db=db_session,
        agent_data=sample_agent_data,
        created_by_id=test_user.id,
    )

    # Add tool
    await agent_service.add_tools_to_agent(
        db=db_session,
        agent_id=agent.id,
        tool_ids=[test_tool.id],
    )

    # Remove tool
    updated_agent = await agent_service.remove_tools_from_agent(
        db=db_session,
        agent_id=agent.id,
        tool_ids=[test_tool.id],
    )

    # Verify tool was removed
    stmt = select(AgentTool).where(
        AgentTool.agent_id == agent.id,
        AgentTool.tool_id == test_tool.id,
    )
    result = await db_session.execute(stmt)
    agent_tool = result.scalar_one_or_none()

    assert agent_tool is None


@pytest.mark.asyncio
async def test_update_tool_configuration(
    db_session: AsyncSession,
    agent_service: AgentService,
    test_user: User,
    sample_agent_data: AgentCreate,
    test_tool: Tool,
):
    """Test updating tool configuration for an agent."""
    # Create agent
    agent = await agent_service.create_agent(
        db=db_session,
        agent_data=sample_agent_data,
        created_by_id=test_user.id,
    )

    # Add tool with initial configuration
    await agent_service.add_tools_to_agent(
        db=db_session,
        agent_id=agent.id,
        tool_ids=[test_tool.id],
        configurations={test_tool.id: {"param1": "value1"}},
    )

    # Update configuration
    updated_agent = await agent_service.update_tool_configuration(
        db=db_session,
        agent_id=agent.id,
        tool_id=test_tool.id,
        configuration={"param1": "updated_value", "param2": "value2"},
    )

    # Verify configuration was updated
    stmt = select(AgentTool).where(
        AgentTool.agent_id == agent.id,
        AgentTool.tool_id == test_tool.id,
    )
    result = await db_session.execute(stmt)
    agent_tool = result.scalar_one_or_none()

    assert agent_tool is not None
    assert agent_tool.configuration_override == {
        "param1": "updated_value",
        "param2": "value2",
    }
