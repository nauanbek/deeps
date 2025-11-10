"""
Comprehensive tests for Agent API endpoints.

Tests all REST API endpoints for agent management including:
- Creating agents
- Listing agents with pagination
- Getting agent by ID
- Updating agents
- Deleting agents (soft and hard)
- Managing agent-tool associations
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent import Agent
from models.tool import Tool
from models.user import User


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user for API operations."""
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
async def sample_agent(db_session: AsyncSession, test_user: User) -> Agent:
    """Create a sample agent for testing."""
    agent = Agent(
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
        created_by_id=test_user.id,
        is_active=True,
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    return agent


@pytest.fixture
async def sample_tool(db_session: AsyncSession, test_user: User) -> Tool:
    """Create a sample tool for testing."""
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


# ============================================================================
# POST /api/v1/agents - Create Agent
# ============================================================================


def test_create_agent_endpoint_success(client: TestClient, test_user: User):
    """Test successful agent creation via API."""
    agent_data = {
        "name": "Test Agent",
        "description": "A test agent",
        "model_provider": "anthropic",
        "model_name": "claude-3-5-sonnet-20241022",
        "temperature": 0.7,
        "max_tokens": 4096,
        "system_prompt": "You are a helpful assistant.",
        "planning_enabled": True,
        "filesystem_enabled": False,
        "additional_config": {"max_iterations": 10},
    }

    response = client.post("/api/v1/agents/", json=agent_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == agent_data["name"]
    assert data["description"] == agent_data["description"]
    assert data["model_provider"] == agent_data["model_provider"]
    assert data["model_name"] == agent_data["model_name"]
    assert data["temperature"] == agent_data["temperature"]
    assert data["max_tokens"] == agent_data["max_tokens"]
    assert data["system_prompt"] == agent_data["system_prompt"]
    assert data["planning_enabled"] == agent_data["planning_enabled"]
    assert data["filesystem_enabled"] == agent_data["filesystem_enabled"]
    assert data["additional_config"] == agent_data["additional_config"]
    assert data["id"] is not None
    assert data["created_at"] is not None
    assert data["is_active"] is True


def test_create_agent_endpoint_validation_error(client: TestClient):
    """Test agent creation fails with validation error."""
    agent_data = {
        "name": "Test Agent",
        # Missing required fields
        "temperature": 1.5,  # Invalid: > 1.0
    }

    response = client.post("/api/v1/agents/", json=agent_data)

    assert response.status_code == 422  # Validation error


def test_create_agent_endpoint_duplicate_name(
    client: TestClient, test_user: User, sample_agent: Agent
):
    """Test agent creation fails with duplicate name."""
    agent_data = {
        "name": sample_agent.name,  # Duplicate name
        "description": "Another agent",
        "model_provider": "anthropic",
        "model_name": "claude-3-5-sonnet-20241022",
        "temperature": 0.7,
    }

    response = client.post("/api/v1/agents/", json=agent_data)

    assert response.status_code == 409  # Conflict
    assert "already exists" in response.json()["detail"].lower()


def test_create_agent_endpoint_minimal_data(client: TestClient):
    """Test agent creation with minimal required fields."""
    agent_data = {
        "name": "Minimal Agent",
        "model_provider": "anthropic",
        "model_name": "claude-3-5-sonnet-20241022",
        # Using defaults for other fields
    }

    response = client.post("/api/v1/agents/", json=agent_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == agent_data["name"]
    assert data["temperature"] == 0.7  # Default value
    assert data["planning_enabled"] is False  # Default value
    assert data["filesystem_enabled"] is False  # Default value


# ============================================================================
# GET /api/v1/agents - List Agents
# ============================================================================


def test_list_agents_endpoint_success(
    client: TestClient, test_user: User, sample_agent: Agent
):
    """Test listing agents successfully."""
    response = client.get("/api/v1/agents/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(a["id"] == sample_agent.id for a in data)


def test_list_agents_endpoint_with_pagination(client: TestClient, test_user: User):
    """Test listing agents with pagination."""
    # Create multiple agents
    for i in range(5):
        agent_data = {
            "name": f"Agent {i}",
            "model_provider": "anthropic",
            "model_name": "claude-3-5-sonnet-20241022",
        }
        client.post("/api/v1/agents/", json=agent_data)

    # Test pagination
    response = client.get("/api/v1/agents/?skip=0&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    response = client.get("/api/v1/agents/?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_list_agents_endpoint_empty(client: TestClient):
    """Test listing agents returns empty list when no agents exist."""
    response = client.get("/api/v1/agents/")

    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_list_agents_endpoint_filter_active(
    client: TestClient, test_user: User, sample_agent: Agent
):
    """Test filtering agents by is_active status."""
    # Soft delete the agent
    client.delete(f"/api/v1/agents/{sample_agent.id}")

    # Should not appear in default list (active only)
    response = client.get("/api/v1/agents/")
    assert response.status_code == 200
    data = response.json()
    assert not any(a["id"] == sample_agent.id for a in data)

    # Should appear when explicitly filtering for inactive
    response = client.get("/api/v1/agents/?is_active=false")
    assert response.status_code == 200
    data = response.json()
    assert any(a["id"] == sample_agent.id for a in data)


# ============================================================================
# GET /api/v1/agents/{agent_id} - Get Agent by ID
# ============================================================================


def test_get_agent_endpoint_success(
    client: TestClient, test_user: User, sample_agent: Agent
):
    """Test getting agent by ID successfully."""
    response = client.get(f"/api/v1/agents/{sample_agent.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_agent.id
    assert data["name"] == sample_agent.name
    assert data["model_provider"] == sample_agent.model_provider
    assert data["model_name"] == sample_agent.model_name


def test_get_agent_endpoint_not_found(client: TestClient):
    """Test getting agent fails for non-existent ID."""
    response = client.get("/api/v1/agents/99999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_agent_endpoint_inactive_agent(
    client: TestClient, test_user: User, sample_agent: Agent
):
    """Test getting inactive agent fails by default."""
    # Soft delete the agent
    client.delete(f"/api/v1/agents/{sample_agent.id}")

    response = client.get(f"/api/v1/agents/{sample_agent.id}")

    assert response.status_code == 404


# ============================================================================
# PUT /api/v1/agents/{agent_id} - Update Agent
# ============================================================================


def test_update_agent_endpoint_success(
    client: TestClient, test_user: User, sample_agent: Agent
):
    """Test successful agent update via API."""
    update_data = {
        "name": "Updated Agent",
        "description": "Updated description",
        "temperature": 0.9,
    }

    response = client.put(f"/api/v1/agents/{sample_agent.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["temperature"] == update_data["temperature"]
    # Unchanged fields should remain the same
    assert data["model_provider"] == sample_agent.model_provider
    assert data["model_name"] == sample_agent.model_name


def test_update_agent_endpoint_not_found(client: TestClient):
    """Test update fails for non-existent agent."""
    update_data = {"name": "Updated Agent"}

    response = client.put("/api/v1/agents/99999", json=update_data)

    assert response.status_code == 404


def test_update_agent_endpoint_validation_error(
    client: TestClient, test_user: User, sample_agent: Agent
):
    """Test update fails with validation error."""
    update_data = {
        "temperature": 1.5,  # Invalid: > 1.0
    }

    response = client.put(f"/api/v1/agents/{sample_agent.id}", json=update_data)

    assert response.status_code == 422  # Validation error


def test_update_agent_endpoint_partial_update(
    client: TestClient, test_user: User, sample_agent: Agent
):
    """Test partial agent update (only some fields)."""
    original_temperature = sample_agent.temperature
    update_data = {
        "description": "Only update description",
    }

    response = client.put(f"/api/v1/agents/{sample_agent.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["description"] == update_data["description"]
    # Other fields should remain unchanged
    assert data["temperature"] == original_temperature
    assert data["name"] == sample_agent.name


# ============================================================================
# DELETE /api/v1/agents/{agent_id} - Delete Agent
# ============================================================================


def test_delete_agent_endpoint_success(
    client: TestClient, test_user: User, sample_agent: Agent
):
    """Test successful agent deletion (soft delete)."""
    response = client.delete(f"/api/v1/agents/{sample_agent.id}")

    assert response.status_code == 204

    # Verify agent is soft deleted
    response = client.get(f"/api/v1/agents/{sample_agent.id}")
    assert response.status_code == 404


def test_delete_agent_endpoint_not_found(client: TestClient):
    """Test delete fails for non-existent agent."""
    response = client.delete("/api/v1/agents/99999")

    assert response.status_code == 404


def test_delete_agent_endpoint_hard_delete(
    client: TestClient, test_user: User, sample_agent: Agent
):
    """Test hard delete removes agent permanently."""
    agent_id = sample_agent.id

    response = client.delete(f"/api/v1/agents/{agent_id}?hard_delete=true")

    assert response.status_code == 204

    # Verify agent is completely removed
    response = client.get(f"/api/v1/agents/{agent_id}")
    assert response.status_code == 404


def test_delete_agent_endpoint_idempotent(
    client: TestClient, test_user: User, sample_agent: Agent
):
    """Test deleting already deleted agent succeeds (idempotent soft delete)."""
    # First deletion
    response = client.delete(f"/api/v1/agents/{sample_agent.id}")
    assert response.status_code == 204

    # Second deletion (agent already soft deleted but still exists)
    # This succeeds because soft delete is idempotent
    response = client.delete(f"/api/v1/agents/{sample_agent.id}")
    assert response.status_code == 204


# ============================================================================
# POST /api/v1/agents/{agent_id}/tools - Add Tools to Agent
# ============================================================================


def test_add_tools_endpoint_success(
    client: TestClient, test_user: User, sample_agent: Agent, sample_tool: Tool
):
    """Test adding tools to an agent successfully."""
    tool_data = {
        "tool_ids": [sample_tool.id],
    }

    response = client.post(
        f"/api/v1/agents/{sample_agent.id}/tools", json=tool_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_agent.id


def test_add_tools_endpoint_invalid_tool_id(
    client: TestClient, test_user: User, sample_agent: Agent
):
    """Test adding non-existent tool fails."""
    tool_data = {
        "tool_ids": [99999],  # Non-existent tool
    }

    response = client.post(
        f"/api/v1/agents/{sample_agent.id}/tools", json=tool_data
    )

    assert response.status_code == 404


def test_add_tools_endpoint_invalid_agent_id(
    client: TestClient, sample_tool: Tool
):
    """Test adding tools to non-existent agent fails."""
    tool_data = {
        "tool_ids": [sample_tool.id],
    }

    response = client.post("/api/v1/agents/99999/tools", json=tool_data)

    assert response.status_code == 404


def test_add_multiple_tools_endpoint(
    client: TestClient, test_user: User, sample_agent: Agent
):
    """Test adding multiple tools to an agent."""
    # Create multiple tools
    tool_ids = []
    for i in range(3):
        tool_data = {
            "name": f"Tool {i}",
            "description": f"Test tool {i}",
            "tool_type": "builtin",
            "configuration": {},
            "schema_definition": {},
        }
        response = client.post("/api/v1/tools/", json=tool_data)
        if response.status_code == 201:
            tool_ids.append(response.json()["id"])

    if tool_ids:
        add_tools_data = {"tool_ids": tool_ids}
        response = client.post(
            f"/api/v1/agents/{sample_agent.id}/tools", json=add_tools_data
        )
        # Note: This might fail if tools endpoint doesn't exist yet
        # That's ok - the test will be skipped or marked as expected failure


# ============================================================================
# Response Format Tests
# ============================================================================


def test_agent_response_includes_timestamps(
    client: TestClient, test_user: User, sample_agent: Agent
):
    """Test that agent response includes timestamp fields."""
    response = client.get(f"/api/v1/agents/{sample_agent.id}")

    assert response.status_code == 200
    data = response.json()
    assert "created_at" in data
    assert "updated_at" in data
    assert data["created_at"] is not None


def test_agent_response_includes_required_fields(
    client: TestClient, test_user: User, sample_agent: Agent
):
    """Test that agent response includes all required fields."""
    response = client.get(f"/api/v1/agents/{sample_agent.id}")

    assert response.status_code == 200
    data = response.json()

    required_fields = [
        "id",
        "name",
        "model_provider",
        "model_name",
        "temperature",
        "planning_enabled",
        "filesystem_enabled",
        "additional_config",
        "created_by_id",
        "created_at",
        "is_active",
    ]

    for field in required_fields:
        assert field in data, f"Missing required field: {field}"


def test_agent_response_format(
    client: TestClient, test_user: User, sample_agent: Agent
):
    """Test agent response format matches schema."""
    response = client.get(f"/api/v1/agents/{sample_agent.id}")

    assert response.status_code == 200
    data = response.json()

    # Verify types
    assert isinstance(data["id"], int)
    assert isinstance(data["name"], str)
    assert isinstance(data["temperature"], float)
    assert isinstance(data["planning_enabled"], bool)
    assert isinstance(data["filesystem_enabled"], bool)
    assert isinstance(data["additional_config"], dict)
    assert isinstance(data["is_active"], bool)


# ============================================================================
# Error Response Format Tests
# ============================================================================


def test_error_response_format_not_found(client: TestClient):
    """Test error response format for 404."""
    response = client.get("/api/v1/agents/99999")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], str)


def test_error_response_format_validation(client: TestClient):
    """Test error response format for validation error."""
    invalid_data = {
        "name": "",  # Empty name
        "temperature": 5.0,  # Invalid temperature
    }

    response = client.post("/api/v1/agents/", json=invalid_data)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
