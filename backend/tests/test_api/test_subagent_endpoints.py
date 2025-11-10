"""
Comprehensive tests for Subagent API endpoints.

Tests all REST endpoints for subagent orchestration:
- POST /api/v1/agents/{agent_id}/subagents - Add subagent
- GET /api/v1/agents/{agent_id}/subagents - List subagents
- DELETE /api/v1/agents/{agent_id}/subagents/{subagent_id} - Remove subagent
- PUT /api/v1/agents/{agent_id}/subagents/{subagent_id} - Update subagent
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent import Agent
from models.user import User


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


# ============================================================================
# POST /agents/{agent_id}/subagents - Add Subagent Tests
# ============================================================================


def test_add_subagent_success(
    client: TestClient,
    parent_agent: Agent,
    child_agent: Agent,
):
    """Test successfully adding a subagent via API."""
    response = client.post(
        f"/api/v1/agents/{parent_agent.id}/subagents",
        json={
            "subagent_id": child_agent.id,
            "delegation_prompt": "You are a specialized helper",
            "priority": 10,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["agent_id"] == parent_agent.id
    assert data["subagent_id"] == child_agent.id
    assert data["delegation_prompt"] == "You are a specialized helper"
    assert data["priority"] == 10
    assert "id" in data
    assert "created_at" in data


def test_add_subagent_minimal_data(
    client: TestClient,
    parent_agent: Agent,
    child_agent: Agent,
):
    """Test adding subagent with only required fields."""
    response = client.post(
        f"/api/v1/agents/{parent_agent.id}/subagents",
        json={
            "subagent_id": child_agent.id,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["agent_id"] == parent_agent.id
    assert data["subagent_id"] == child_agent.id
    assert data["delegation_prompt"] is None
    assert data["priority"] == 0


def test_add_subagent_parent_not_found(
    client: TestClient,
    child_agent: Agent,
):
    """Test adding subagent fails when parent agent doesn't exist."""
    response = client.post(
        "/api/v1/agents/99999/subagents",
        json={
            "subagent_id": child_agent.id,
        },
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_add_subagent_child_not_found(
    client: TestClient,
    parent_agent: Agent,
):
    """Test adding subagent fails when subagent doesn't exist."""
    response = client.post(
        f"/api/v1/agents/{parent_agent.id}/subagents",
        json={
            "subagent_id": 99999,
        },
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_add_subagent_self_reference(
    client: TestClient,
    parent_agent: Agent,
):
    """Test adding agent as its own subagent fails."""
    response = client.post(
        f"/api/v1/agents/{parent_agent.id}/subagents",
        json={
            "subagent_id": parent_agent.id,
        },
    )

    assert response.status_code == 400
    assert "cannot be its own subagent" in response.json()["detail"].lower()


def test_add_subagent_duplicate(
    client: TestClient,
    parent_agent: Agent,
    child_agent: Agent,
):
    """Test adding same subagent twice fails."""
    # Add subagent first time
    response1 = client.post(
        f"/api/v1/agents/{parent_agent.id}/subagents",
        json={
            "subagent_id": child_agent.id,
        },
    )
    assert response1.status_code == 201

    # Try to add again
    response2 = client.post(
        f"/api/v1/agents/{parent_agent.id}/subagents",
        json={
            "subagent_id": child_agent.id,
        },
    )

    assert response2.status_code == 409
    assert "already exists" in response2.json()["detail"].lower()


def test_add_subagent_circular_dependency(
    client: TestClient,
    parent_agent: Agent,
    child_agent: Agent,
):
    """Test circular dependency detection via API."""
    # Add A -> B
    response1 = client.post(
        f"/api/v1/agents/{parent_agent.id}/subagents",
        json={
            "subagent_id": child_agent.id,
        },
    )
    assert response1.status_code == 201

    # Try to add B -> A (should fail)
    response2 = client.post(
        f"/api/v1/agents/{child_agent.id}/subagents",
        json={
            "subagent_id": parent_agent.id,
        },
    )

    assert response2.status_code == 400
    assert "circular dependency" in response2.json()["detail"].lower()


def test_add_subagent_invalid_data(
    client: TestClient,
    parent_agent: Agent,
):
    """Test adding subagent with invalid data fails validation."""
    response = client.post(
        f"/api/v1/agents/{parent_agent.id}/subagents",
        json={
            "subagent_id": "not_an_integer",  # Invalid type
        },
    )

    assert response.status_code == 422  # Unprocessable Entity


# ============================================================================
# GET /agents/{agent_id}/subagents - List Subagents Tests
# ============================================================================


def test_list_subagents_empty(
    client: TestClient,
    parent_agent: Agent,
):
    """Test listing subagents returns empty list when none exist."""
    response = client.get(f"/api/v1/agents/{parent_agent.id}/subagents")

    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_list_subagents_single(
    client: TestClient,
    parent_agent: Agent,
    child_agent: Agent,
):
    """Test listing subagents with one subagent."""
    # Add subagent
    client.post(
        f"/api/v1/agents/{parent_agent.id}/subagents",
        json={
            "subagent_id": child_agent.id,
            "priority": 5,
        },
    )

    # List subagents
    response = client.get(f"/api/v1/agents/{parent_agent.id}/subagents")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["agent_id"] == parent_agent.id
    assert data[0]["subagent_id"] == child_agent.id
    assert data[0]["priority"] == 5


@pytest.mark.asyncio
async def test_list_subagents_multiple_ordered_by_priority(
    client: TestClient,
    parent_agent: Agent,
    db_session: AsyncSession,
    test_user: User,
):
    """Test listing multiple subagents ordered by priority."""
    # Create 3 child agents
    children = []
    for i, priority in enumerate([5, 10, 3]):
        agent = Agent(
            name=f"Child {i}",
            model_provider="anthropic",
            model_name="claude-3-haiku-20241022",
            temperature=0.5,
            created_by_id=test_user.id,
            is_active=True,
        )
        db_session.add(agent)
        await db_session.commit()
        await db_session.refresh(agent)
        children.append((agent, priority))

    # Add subagents with different priorities
    for child, priority in children:
        client.post(
            f"/api/v1/agents/{parent_agent.id}/subagents",
            json={
                "subagent_id": child.id,
                "priority": priority,
            },
        )

    # List subagents
    response = client.get(f"/api/v1/agents/{parent_agent.id}/subagents")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    # Should be ordered by priority descending
    assert data[0]["priority"] == 10
    assert data[1]["priority"] == 5
    assert data[2]["priority"] == 3


def test_list_subagents_agent_not_found(client: TestClient):
    """Test listing subagents fails for non-existent agent."""
    response = client.get("/api/v1/agents/99999/subagents")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ============================================================================
# DELETE /agents/{agent_id}/subagents/{subagent_id} - Remove Subagent Tests
# ============================================================================


def test_remove_subagent_success(
    client: TestClient,
    parent_agent: Agent,
    child_agent: Agent,
):
    """Test successfully removing a subagent."""
    # Add subagent
    client.post(
        f"/api/v1/agents/{parent_agent.id}/subagents",
        json={
            "subagent_id": child_agent.id,
        },
    )

    # Remove subagent
    response = client.delete(
        f"/api/v1/agents/{parent_agent.id}/subagents/{child_agent.id}"
    )

    assert response.status_code == 204

    # Verify it's gone
    list_response = client.get(f"/api/v1/agents/{parent_agent.id}/subagents")
    assert list_response.json() == []


def test_remove_subagent_not_found(
    client: TestClient,
    parent_agent: Agent,
    child_agent: Agent,
):
    """Test removing non-existent subagent fails."""
    response = client.delete(
        f"/api/v1/agents/{parent_agent.id}/subagents/{child_agent.id}"
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_remove_subagent_agent_not_found(
    client: TestClient,
    child_agent: Agent,
):
    """Test removing subagent fails for non-existent parent agent."""
    response = client.delete(f"/api/v1/agents/99999/subagents/{child_agent.id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ============================================================================
# PUT /agents/{agent_id}/subagents/{subagent_id} - Update Subagent Tests
# ============================================================================


def test_update_subagent_success(
    client: TestClient,
    parent_agent: Agent,
    child_agent: Agent,
):
    """Test successfully updating subagent configuration."""
    # Add subagent
    client.post(
        f"/api/v1/agents/{parent_agent.id}/subagents",
        json={
            "subagent_id": child_agent.id,
            "delegation_prompt": "Original prompt",
            "priority": 5,
        },
    )

    # Update configuration
    response = client.put(
        f"/api/v1/agents/{parent_agent.id}/subagents/{child_agent.id}",
        json={
            "delegation_prompt": "Updated prompt",
            "priority": 10,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["delegation_prompt"] == "Updated prompt"
    assert data["priority"] == 10


def test_update_subagent_partial(
    client: TestClient,
    parent_agent: Agent,
    child_agent: Agent,
):
    """Test partial update of subagent configuration."""
    # Add subagent
    client.post(
        f"/api/v1/agents/{parent_agent.id}/subagents",
        json={
            "subagent_id": child_agent.id,
            "delegation_prompt": "Original prompt",
            "priority": 5,
        },
    )

    # Update only priority
    response = client.put(
        f"/api/v1/agents/{parent_agent.id}/subagents/{child_agent.id}",
        json={
            "priority": 15,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["delegation_prompt"] == "Original prompt"  # Unchanged
    assert data["priority"] == 15  # Updated


def test_update_subagent_not_found(
    client: TestClient,
    parent_agent: Agent,
    child_agent: Agent,
):
    """Test updating non-existent subagent fails."""
    response = client.put(
        f"/api/v1/agents/{parent_agent.id}/subagents/{child_agent.id}",
        json={
            "priority": 10,
        },
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_subagent_agent_not_found(
    client: TestClient,
    child_agent: Agent,
):
    """Test updating subagent fails for non-existent parent agent."""
    response = client.put(
        f"/api/v1/agents/99999/subagents/{child_agent.id}",
        json={
            "priority": 10,
        },
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
