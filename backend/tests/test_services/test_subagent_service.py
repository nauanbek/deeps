"""
Comprehensive tests for Subagent Service layer.

Tests all business logic for subagent orchestration, including:
- Adding subagents to agents
- Listing agent subagents
- Removing subagents from agents
- Updating subagent configurations
- Circular dependency prevention
- Self-reference prevention
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent import Agent, Subagent
from models.user import User
from schemas.subagent import SubagentCreate, SubagentUpdate
from services.subagent_service import (
    SubagentService,
    AgentNotFoundError,
    CircularDependencyError,
    SelfReferenceError,
    SubagentNotFoundError,
)


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
async def parent_agent(db_session: AsyncSession, test_user: User) -> Agent:
    """Create a parent agent for testing."""
    agent = Agent(
        name="Parent Agent",
        description="A parent agent",
        model_provider="anthropic",
        model_name="claude-3-5-sonnet-20241022",
        temperature=0.7,
        created_by_id=test_user.id,
        is_active=True,
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    return agent


@pytest.fixture
async def child_agent(db_session: AsyncSession, test_user: User) -> Agent:
    """Create a child agent for testing."""
    agent = Agent(
        name="Child Agent",
        description="A specialized child agent",
        model_provider="anthropic",
        model_name="claude-3-haiku-20241022",
        temperature=0.5,
        created_by_id=test_user.id,
        is_active=True,
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    return agent


@pytest.fixture
def subagent_service() -> SubagentService:
    """Create an instance of SubagentService."""
    return SubagentService()


# ============================================================================
# Add Subagent Tests
# ============================================================================


@pytest.mark.asyncio
async def test_add_subagent_success(
    db_session: AsyncSession,
    subagent_service: SubagentService,
    parent_agent: Agent,
    child_agent: Agent,
):
    """Test successfully adding a subagent to an agent."""
    subagent_data = SubagentCreate(
        subagent_id=child_agent.id,
        delegation_prompt="You are a specialized helper",
        priority=10,
    )

    result = await subagent_service.add_subagent_to_agent(
        db=db_session,
        agent_id=parent_agent.id,
        subagent_data=subagent_data,
    )

    assert result.agent_id == parent_agent.id
    assert result.subagent_id == child_agent.id
    assert result.delegation_prompt == "You are a specialized helper"
    assert result.priority == 10


@pytest.mark.asyncio
async def test_add_subagent_with_minimal_data(
    db_session: AsyncSession,
    subagent_service: SubagentService,
    parent_agent: Agent,
    child_agent: Agent,
):
    """Test adding a subagent with only required fields."""
    subagent_data = SubagentCreate(
        subagent_id=child_agent.id,
    )

    result = await subagent_service.add_subagent_to_agent(
        db=db_session,
        agent_id=parent_agent.id,
        subagent_data=subagent_data,
    )

    assert result.agent_id == parent_agent.id
    assert result.subagent_id == child_agent.id
    assert result.delegation_prompt is None
    assert result.priority == 0


@pytest.mark.asyncio
async def test_add_subagent_parent_not_found(
    db_session: AsyncSession,
    subagent_service: SubagentService,
    child_agent: Agent,
):
    """Test adding subagent fails when parent agent doesn't exist."""
    subagent_data = SubagentCreate(subagent_id=child_agent.id)

    with pytest.raises(AgentNotFoundError) as exc_info:
        await subagent_service.add_subagent_to_agent(
            db=db_session,
            agent_id=99999,
            subagent_data=subagent_data,
        )

    assert exc_info.value.agent_id == 99999


@pytest.mark.asyncio
async def test_add_subagent_child_not_found(
    db_session: AsyncSession,
    subagent_service: SubagentService,
    parent_agent: Agent,
):
    """Test adding subagent fails when subagent doesn't exist."""
    subagent_data = SubagentCreate(subagent_id=99999)

    with pytest.raises(AgentNotFoundError) as exc_info:
        await subagent_service.add_subagent_to_agent(
            db=db_session,
            agent_id=parent_agent.id,
            subagent_data=subagent_data,
        )

    assert exc_info.value.agent_id == 99999


@pytest.mark.asyncio
async def test_add_subagent_prevents_self_reference(
    db_session: AsyncSession,
    subagent_service: SubagentService,
    parent_agent: Agent,
):
    """Test that an agent cannot be its own subagent."""
    subagent_data = SubagentCreate(subagent_id=parent_agent.id)

    with pytest.raises(SelfReferenceError) as exc_info:
        await subagent_service.add_subagent_to_agent(
            db=db_session,
            agent_id=parent_agent.id,
            subagent_data=subagent_data,
        )

    assert "cannot be its own subagent" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_add_subagent_prevents_duplicate(
    db_session: AsyncSession,
    subagent_service: SubagentService,
    parent_agent: Agent,
    child_agent: Agent,
):
    """Test that the same subagent cannot be added twice."""
    subagent_data = SubagentCreate(subagent_id=child_agent.id, priority=5)

    # Add subagent first time
    await subagent_service.add_subagent_to_agent(
        db=db_session,
        agent_id=parent_agent.id,
        subagent_data=subagent_data,
    )

    # Try to add same subagent again
    with pytest.raises(ValueError) as exc_info:
        await subagent_service.add_subagent_to_agent(
            db=db_session,
            agent_id=parent_agent.id,
            subagent_data=subagent_data,
        )

    assert "already exists" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_add_subagent_prevents_circular_dependency_direct(
    db_session: AsyncSession,
    subagent_service: SubagentService,
    parent_agent: Agent,
    child_agent: Agent,
):
    """Test prevention of direct circular dependency (A -> B, B -> A)."""
    # Add A -> B
    await subagent_service.add_subagent_to_agent(
        db=db_session,
        agent_id=parent_agent.id,
        subagent_data=SubagentCreate(subagent_id=child_agent.id),
    )

    # Try to add B -> A (should fail)
    with pytest.raises(CircularDependencyError) as exc_info:
        await subagent_service.add_subagent_to_agent(
            db=db_session,
            agent_id=child_agent.id,
            subagent_data=SubagentCreate(subagent_id=parent_agent.id),
        )

    assert "circular dependency" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_add_subagent_prevents_circular_dependency_indirect(
    db_session: AsyncSession,
    subagent_service: SubagentService,
    test_user: User,
):
    """Test prevention of indirect circular dependency (A -> B -> C -> A)."""
    # Create three agents
    agent_a = Agent(
        name="Agent A",
        model_provider="anthropic",
        model_name="claude-3-5-sonnet-20241022",
        temperature=0.7,
        created_by_id=test_user.id,
        is_active=True,
    )
    agent_b = Agent(
        name="Agent B",
        model_provider="anthropic",
        model_name="claude-3-5-sonnet-20241022",
        temperature=0.7,
        created_by_id=test_user.id,
        is_active=True,
    )
    agent_c = Agent(
        name="Agent C",
        model_provider="anthropic",
        model_name="claude-3-5-sonnet-20241022",
        temperature=0.7,
        created_by_id=test_user.id,
        is_active=True,
    )

    db_session.add_all([agent_a, agent_b, agent_c])
    await db_session.commit()
    await db_session.refresh(agent_a)
    await db_session.refresh(agent_b)
    await db_session.refresh(agent_c)

    # Create chain: A -> B -> C
    await subagent_service.add_subagent_to_agent(
        db=db_session,
        agent_id=agent_a.id,
        subagent_data=SubagentCreate(subagent_id=agent_b.id),
    )
    await subagent_service.add_subagent_to_agent(
        db=db_session,
        agent_id=agent_b.id,
        subagent_data=SubagentCreate(subagent_id=agent_c.id),
    )

    # Try to close the loop: C -> A (should fail)
    with pytest.raises(CircularDependencyError) as exc_info:
        await subagent_service.add_subagent_to_agent(
            db=db_session,
            agent_id=agent_c.id,
            subagent_data=SubagentCreate(subagent_id=agent_a.id),
        )

    assert "circular dependency" in str(exc_info.value).lower()


# ============================================================================
# List Subagents Tests
# ============================================================================


@pytest.mark.asyncio
async def test_list_subagents_empty(
    db_session: AsyncSession,
    subagent_service: SubagentService,
    parent_agent: Agent,
):
    """Test listing subagents returns empty list when none exist."""
    result = await subagent_service.list_agent_subagents(
        db=db_session,
        agent_id=parent_agent.id,
    )

    assert result == []


@pytest.mark.asyncio
async def test_list_subagents_single(
    db_session: AsyncSession,
    subagent_service: SubagentService,
    parent_agent: Agent,
    child_agent: Agent,
):
    """Test listing subagents with a single subagent."""
    # Add subagent
    await subagent_service.add_subagent_to_agent(
        db=db_session,
        agent_id=parent_agent.id,
        subagent_data=SubagentCreate(
            subagent_id=child_agent.id,
            priority=5,
        ),
    )

    # List subagents
    result = await subagent_service.list_agent_subagents(
        db=db_session,
        agent_id=parent_agent.id,
    )

    assert len(result) == 1
    assert result[0].agent_id == parent_agent.id
    assert result[0].subagent_id == child_agent.id
    assert result[0].priority == 5


@pytest.mark.asyncio
async def test_list_subagents_multiple_ordered_by_priority(
    db_session: AsyncSession,
    subagent_service: SubagentService,
    parent_agent: Agent,
    test_user: User,
):
    """Test listing subagents returns them ordered by priority (descending)."""
    # Create 3 child agents
    child1 = Agent(
        name="Child 1",
        model_provider="anthropic",
        model_name="claude-3-haiku-20241022",
        temperature=0.5,
        created_by_id=test_user.id,
        is_active=True,
    )
    child2 = Agent(
        name="Child 2",
        model_provider="anthropic",
        model_name="claude-3-haiku-20241022",
        temperature=0.5,
        created_by_id=test_user.id,
        is_active=True,
    )
    child3 = Agent(
        name="Child 3",
        model_provider="anthropic",
        model_name="claude-3-haiku-20241022",
        temperature=0.5,
        created_by_id=test_user.id,
        is_active=True,
    )

    db_session.add_all([child1, child2, child3])
    await db_session.commit()
    await db_session.refresh(child1)
    await db_session.refresh(child2)
    await db_session.refresh(child3)

    # Add subagents with different priorities
    await subagent_service.add_subagent_to_agent(
        db=db_session,
        agent_id=parent_agent.id,
        subagent_data=SubagentCreate(subagent_id=child1.id, priority=5),
    )
    await subagent_service.add_subagent_to_agent(
        db=db_session,
        agent_id=parent_agent.id,
        subagent_data=SubagentCreate(subagent_id=child2.id, priority=10),
    )
    await subagent_service.add_subagent_to_agent(
        db=db_session,
        agent_id=parent_agent.id,
        subagent_data=SubagentCreate(subagent_id=child3.id, priority=3),
    )

    # List subagents
    result = await subagent_service.list_agent_subagents(
        db=db_session,
        agent_id=parent_agent.id,
    )

    assert len(result) == 3
    # Should be ordered by priority descending
    assert result[0].priority == 10
    assert result[1].priority == 5
    assert result[2].priority == 3


@pytest.mark.asyncio
async def test_list_subagents_agent_not_found(
    db_session: AsyncSession,
    subagent_service: SubagentService,
):
    """Test listing subagents fails for non-existent agent."""
    with pytest.raises(AgentNotFoundError):
        await subagent_service.list_agent_subagents(
            db=db_session,
            agent_id=99999,
        )


# ============================================================================
# Remove Subagent Tests
# ============================================================================


@pytest.mark.asyncio
async def test_remove_subagent_success(
    db_session: AsyncSession,
    subagent_service: SubagentService,
    parent_agent: Agent,
    child_agent: Agent,
):
    """Test successfully removing a subagent."""
    # Add subagent
    await subagent_service.add_subagent_to_agent(
        db=db_session,
        agent_id=parent_agent.id,
        subagent_data=SubagentCreate(subagent_id=child_agent.id),
    )

    # Remove subagent
    result = await subagent_service.remove_subagent_from_agent(
        db=db_session,
        agent_id=parent_agent.id,
        subagent_id=child_agent.id,
    )

    assert result is True

    # Verify it's gone
    stmt = select(Subagent).where(
        Subagent.agent_id == parent_agent.id,
        Subagent.subagent_id == child_agent.id,
    )
    result = await db_session.execute(stmt)
    subagent = result.scalar_one_or_none()

    assert subagent is None


@pytest.mark.asyncio
async def test_remove_subagent_not_found(
    db_session: AsyncSession,
    subagent_service: SubagentService,
    parent_agent: Agent,
    child_agent: Agent,
):
    """Test removing a non-existent subagent raises error."""
    with pytest.raises(SubagentNotFoundError):
        await subagent_service.remove_subagent_from_agent(
            db=db_session,
            agent_id=parent_agent.id,
            subagent_id=child_agent.id,
        )


@pytest.mark.asyncio
async def test_remove_subagent_agent_not_found(
    db_session: AsyncSession,
    subagent_service: SubagentService,
    child_agent: Agent,
):
    """Test removing subagent fails for non-existent parent agent."""
    with pytest.raises(AgentNotFoundError):
        await subagent_service.remove_subagent_from_agent(
            db=db_session,
            agent_id=99999,
            subagent_id=child_agent.id,
        )


# ============================================================================
# Update Subagent Configuration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_update_subagent_config_success(
    db_session: AsyncSession,
    subagent_service: SubagentService,
    parent_agent: Agent,
    child_agent: Agent,
):
    """Test successfully updating subagent configuration."""
    # Add subagent
    await subagent_service.add_subagent_to_agent(
        db=db_session,
        agent_id=parent_agent.id,
        subagent_data=SubagentCreate(
            subagent_id=child_agent.id,
            delegation_prompt="Original prompt",
            priority=5,
        ),
    )

    # Update configuration
    update_data = SubagentUpdate(
        delegation_prompt="Updated prompt",
        priority=10,
    )

    result = await subagent_service.update_subagent_config(
        db=db_session,
        agent_id=parent_agent.id,
        subagent_id=child_agent.id,
        update_data=update_data,
    )

    assert result.delegation_prompt == "Updated prompt"
    assert result.priority == 10


@pytest.mark.asyncio
async def test_update_subagent_config_partial(
    db_session: AsyncSession,
    subagent_service: SubagentService,
    parent_agent: Agent,
    child_agent: Agent,
):
    """Test partial update of subagent configuration."""
    # Add subagent
    await subagent_service.add_subagent_to_agent(
        db=db_session,
        agent_id=parent_agent.id,
        subagent_data=SubagentCreate(
            subagent_id=child_agent.id,
            delegation_prompt="Original prompt",
            priority=5,
        ),
    )

    # Update only priority
    update_data = SubagentUpdate(priority=15)

    result = await subagent_service.update_subagent_config(
        db=db_session,
        agent_id=parent_agent.id,
        subagent_id=child_agent.id,
        update_data=update_data,
    )

    assert result.delegation_prompt == "Original prompt"  # Unchanged
    assert result.priority == 15  # Updated


@pytest.mark.asyncio
async def test_update_subagent_config_not_found(
    db_session: AsyncSession,
    subagent_service: SubagentService,
    parent_agent: Agent,
    child_agent: Agent,
):
    """Test updating non-existent subagent configuration raises error."""
    update_data = SubagentUpdate(priority=10)

    with pytest.raises(SubagentNotFoundError):
        await subagent_service.update_subagent_config(
            db=db_session,
            agent_id=parent_agent.id,
            subagent_id=child_agent.id,
            update_data=update_data,
        )


@pytest.mark.asyncio
async def test_update_subagent_config_agent_not_found(
    db_session: AsyncSession,
    subagent_service: SubagentService,
    child_agent: Agent,
):
    """Test updating subagent config fails for non-existent parent agent."""
    update_data = SubagentUpdate(priority=10)

    with pytest.raises(AgentNotFoundError):
        await subagent_service.update_subagent_config(
            db=db_session,
            agent_id=99999,
            subagent_id=child_agent.id,
            update_data=update_data,
        )
