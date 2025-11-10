"""
Comprehensive tests for Advanced Configuration API endpoints.

Tests all REST API endpoints for advanced agent configuration including:
- Backend configuration (State, Filesystem, Store, Composite)
- Memory namespace and file management
- HITL interrupt configuration
- Execution approval workflows
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent import Agent
from models.user import User
from models.advanced_config import (
    AgentBackendConfig,
    AgentMemoryNamespace,
    AgentMemoryFile,
    AgentInterruptConfig,
)
from models.execution import Execution


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
        created_by_id=test_user.id,
        is_active=True,
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    return agent


@pytest.fixture
async def sample_execution(db_session: AsyncSession, sample_agent: Agent) -> Execution:
    """Create a sample execution for testing approvals."""
    execution = Execution(
        agent_id=sample_agent.id,
        input_data={"prompt": "Test prompt"},
        status="running",
    )
    db_session.add(execution)
    await db_session.commit()
    await db_session.refresh(execution)
    return execution


# ============================================================================
# Backend Configuration Endpoints
# ============================================================================


def test_create_backend_config_state(client: TestClient, sample_agent: Agent):
    """Test creating StateBackend configuration."""
    config_data = {
        "backend_type": "state",
        "config": {}
    }

    response = client.post(
        f"/api/v1/agents/{sample_agent.id}/backend",
        json=config_data
    )

    assert response.status_code == 201
    data = response.json()
    assert data["backend_type"] == "state"
    assert data["agent_id"] == sample_agent.id


def test_create_backend_config_filesystem(client: TestClient, sample_agent: Agent):
    """Test creating FilesystemBackend configuration."""
    config_data = {
        "backend_type": "filesystem",
        "config": {
            "root_dir": "/workspace/agent_123",
            "virtual_mode": True
        }
    }

    response = client.post(
        f"/api/v1/agents/{sample_agent.id}/backend",
        json=config_data
    )

    assert response.status_code == 201
    data = response.json()
    assert data["backend_type"] == "filesystem"
    assert data["config"]["root_dir"] == "/workspace/agent_123"
    assert data["config"]["virtual_mode"] is True


def test_create_backend_config_store(client: TestClient, sample_agent: Agent):
    """Test creating StoreBackend configuration."""
    config_data = {
        "backend_type": "store",
        "config": {
            "namespace": "agent_123"
        }
    }

    response = client.post(
        f"/api/v1/agents/{sample_agent.id}/backend",
        json=config_data
    )

    assert response.status_code == 201
    data = response.json()
    assert data["backend_type"] == "store"
    assert data["config"]["namespace"] == "agent_123"


def test_create_backend_config_composite(client: TestClient, sample_agent: Agent):
    """Test creating CompositeBackend configuration."""
    config_data = {
        "backend_type": "composite",
        "config": {
            "routes": {
                "/memories/": {"type": "store"},
                "/scratch/": {"type": "state"}
            },
            "default": {"type": "state"}
        }
    }

    response = client.post(
        f"/api/v1/agents/{sample_agent.id}/backend",
        json=config_data
    )

    assert response.status_code == 201
    data = response.json()
    assert data["backend_type"] == "composite"
    assert "/memories/" in data["config"]["routes"]
    assert data["config"]["default"]["type"] == "state"


def test_create_backend_config_duplicate(client: TestClient, sample_agent: Agent):
    """Test that creating duplicate backend config returns 409."""
    config_data = {
        "backend_type": "state",
        "config": {}
    }

    # Create first config
    response1 = client.post(
        f"/api/v1/agents/{sample_agent.id}/backend",
        json=config_data
    )
    assert response1.status_code == 201

    # Try to create again
    response2 = client.post(
        f"/api/v1/agents/{sample_agent.id}/backend",
        json=config_data
    )
    assert response2.status_code == 409


def test_get_backend_config(client: TestClient, sample_agent: Agent):
    """Test retrieving backend configuration."""
    # Create config first
    config_data = {
        "backend_type": "state",
        "config": {}
    }
    client.post(f"/api/v1/agents/{sample_agent.id}/backend", json=config_data)

    # Get config
    response = client.get(f"/api/v1/agents/{sample_agent.id}/backend")

    assert response.status_code == 200
    data = response.json()
    assert data["backend_type"] == "state"


def test_get_backend_config_not_found(client: TestClient, sample_agent: Agent):
    """Test getting backend config when none exists returns 404."""
    response = client.get(f"/api/v1/agents/{sample_agent.id}/backend")
    assert response.status_code == 404


def test_update_backend_config(client: TestClient, sample_agent: Agent):
    """Test updating backend configuration."""
    # Create config first
    config_data = {
        "backend_type": "state",
        "config": {}
    }
    client.post(f"/api/v1/agents/{sample_agent.id}/backend", json=config_data)

    # Update to filesystem
    updated_data = {
        "backend_type": "filesystem",
        "config": {
            "root_dir": "/new/path",
            "virtual_mode": False
        }
    }

    response = client.put(
        f"/api/v1/agents/{sample_agent.id}/backend",
        json=updated_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["backend_type"] == "filesystem"
    assert data["config"]["root_dir"] == "/new/path"


def test_delete_backend_config(client: TestClient, sample_agent: Agent):
    """Test deleting backend configuration."""
    # Create config first
    config_data = {
        "backend_type": "state",
        "config": {}
    }
    client.post(f"/api/v1/agents/{sample_agent.id}/backend", json=config_data)

    # Delete config
    response = client.delete(f"/api/v1/agents/{sample_agent.id}/backend")

    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(f"/api/v1/agents/{sample_agent.id}/backend")
    assert get_response.status_code == 404


# ============================================================================
# Memory Namespace Endpoints
# ============================================================================


def test_create_memory_namespace(client: TestClient, sample_agent: Agent):
    """Test creating memory namespace."""
    response = client.post(
        f"/api/v1/agents/{sample_agent.id}/memory/namespace",
        json={}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["agent_id"] == sample_agent.id
    assert "namespace" in data
    assert data["store_type"] == "postgresql"


def test_create_memory_namespace_duplicate(client: TestClient, sample_agent: Agent):
    """Test that creating duplicate namespace returns 409."""
    # Create first namespace
    response1 = client.post(
        f"/api/v1/agents/{sample_agent.id}/memory/namespace",
        json={}
    )
    assert response1.status_code == 201

    # Try to create again
    response2 = client.post(
        f"/api/v1/agents/{sample_agent.id}/memory/namespace",
        json={}
    )
    assert response2.status_code == 409


def test_get_memory_namespace(client: TestClient, sample_agent: Agent):
    """Test retrieving memory namespace."""
    # Create namespace first
    client.post(f"/api/v1/agents/{sample_agent.id}/memory/namespace", json={})

    # Get namespace
    response = client.get(f"/api/v1/agents/{sample_agent.id}/memory/namespace")

    assert response.status_code == 200
    data = response.json()
    assert "namespace" in data


def test_get_memory_namespace_not_found(client: TestClient, sample_agent: Agent):
    """Test getting namespace when none exists returns 404."""
    response = client.get(f"/api/v1/agents/{sample_agent.id}/memory/namespace")
    assert response.status_code == 404


def test_delete_memory_namespace(client: TestClient, sample_agent: Agent):
    """Test deleting memory namespace."""
    # Create namespace first
    client.post(f"/api/v1/agents/{sample_agent.id}/memory/namespace", json={})

    # Delete namespace
    response = client.delete(f"/api/v1/agents/{sample_agent.id}/memory/namespace")

    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(f"/api/v1/agents/{sample_agent.id}/memory/namespace")
    assert get_response.status_code == 404


# ============================================================================
# Memory File Endpoints
# ============================================================================


def test_create_memory_file(client: TestClient, sample_agent: Agent):
    """Test creating a memory file."""
    # Create namespace first
    client.post(f"/api/v1/agents/{sample_agent.id}/memory/namespace", json={})

    # Create file
    file_data = {
        "key": "context.md",
        "value": "# Agent Context\nThis is test data"
    }

    response = client.post(
        f"/api/v1/agents/{sample_agent.id}/memory/files",
        json=file_data
    )

    assert response.status_code == 201
    data = response.json()
    assert data["key"] == "context.md"
    assert "Agent Context" in data["value"]


def test_create_memory_file_no_namespace(client: TestClient, sample_agent: Agent):
    """Test that creating file without namespace returns 404."""
    file_data = {
        "key": "context.md",
        "value": "# Test"
    }

    response = client.post(
        f"/api/v1/agents/{sample_agent.id}/memory/files",
        json=file_data
    )

    assert response.status_code == 404


def test_list_memory_files(client: TestClient, sample_agent: Agent):
    """Test listing memory files."""
    # Create namespace first
    client.post(f"/api/v1/agents/{sample_agent.id}/memory/namespace", json={})

    # Create multiple files
    files = [
        {"key": "file1.txt", "value": "content1"},
        {"key": "file2.txt", "value": "content2"},
        {"key": "nested/file3.txt", "value": "content3"}
    ]

    for file_data in files:
        client.post(
            f"/api/v1/agents/{sample_agent.id}/memory/files",
            json=file_data
        )

    # List all files
    response = client.get(f"/api/v1/agents/{sample_agent.id}/memory/files")

    assert response.status_code == 200
    data = response.json()
    assert data["total_files"] == 3
    assert len(data["files"]) == 3


def test_list_memory_files_with_prefix(client: TestClient, sample_agent: Agent):
    """Test listing memory files with prefix filter."""
    # Create namespace first
    client.post(f"/api/v1/agents/{sample_agent.id}/memory/namespace", json={})

    # Create multiple files
    files = [
        {"key": "nested/file1.txt", "value": "content1"},
        {"key": "nested/file2.txt", "value": "content2"},
        {"key": "other/file3.txt", "value": "content3"}
    ]

    for file_data in files:
        client.post(
            f"/api/v1/agents/{sample_agent.id}/memory/files",
            json=file_data
        )

    # List files with prefix
    response = client.get(
        f"/api/v1/agents/{sample_agent.id}/memory/files?prefix=nested/"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_files"] == 2


def test_read_memory_file(client: TestClient, sample_agent: Agent):
    """Test reading a specific memory file."""
    # Create namespace first
    client.post(f"/api/v1/agents/{sample_agent.id}/memory/namespace", json={})

    # Create file
    file_data = {
        "key": "test.txt",
        "value": "Test content"
    }
    client.post(
        f"/api/v1/agents/{sample_agent.id}/memory/files",
        json=file_data
    )

    # Read file
    response = client.get(
        f"/api/v1/agents/{sample_agent.id}/memory/files/test.txt"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["value"] == "Test content"


def test_read_memory_file_not_found(client: TestClient, sample_agent: Agent):
    """Test reading non-existent file returns 404."""
    # Create namespace first
    client.post(f"/api/v1/agents/{sample_agent.id}/memory/namespace", json={})

    # Try to read non-existent file
    response = client.get(
        f"/api/v1/agents/{sample_agent.id}/memory/files/nonexistent.txt"
    )

    assert response.status_code == 404


def test_delete_memory_file(client: TestClient, sample_agent: Agent):
    """Test deleting a memory file."""
    # Create namespace first
    client.post(f"/api/v1/agents/{sample_agent.id}/memory/namespace", json={})

    # Create file
    file_data = {
        "key": "to_delete.txt",
        "value": "Delete me"
    }
    client.post(
        f"/api/v1/agents/{sample_agent.id}/memory/files",
        json=file_data
    )

    # Delete file
    response = client.delete(
        f"/api/v1/agents/{sample_agent.id}/memory/files/to_delete.txt"
    )

    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(
        f"/api/v1/agents/{sample_agent.id}/memory/files/to_delete.txt"
    )
    assert get_response.status_code == 404


# ============================================================================
# HITL Interrupt Configuration Endpoints
# ============================================================================


def test_create_interrupt_config(client: TestClient, sample_agent: Agent):
    """Test creating HITL interrupt configuration."""
    config_data = {
        "tool_name": "delete_file",
        "allowed_decisions": ["approve", "reject"],
        "config": {}
    }

    response = client.post(
        f"/api/v1/agents/{sample_agent.id}/interrupt",
        json=config_data
    )

    assert response.status_code == 201
    data = response.json()
    assert data["tool_name"] == "delete_file"
    assert "approve" in data["allowed_decisions"]
    assert "reject" in data["allowed_decisions"]


def test_create_interrupt_config_with_edit(client: TestClient, sample_agent: Agent):
    """Test creating interrupt config with edit decision."""
    config_data = {
        "tool_name": "write_file",
        "allowed_decisions": ["approve", "edit", "reject"],
        "config": {}
    }

    response = client.post(
        f"/api/v1/agents/{sample_agent.id}/interrupt",
        json=config_data
    )

    assert response.status_code == 201
    data = response.json()
    assert "edit" in data["allowed_decisions"]


def test_create_interrupt_config_duplicate_tool(client: TestClient, sample_agent: Agent):
    """Test that creating duplicate config for same tool returns 409."""
    config_data = {
        "tool_name": "delete_file",
        "allowed_decisions": ["approve", "reject"],
        "config": {}
    }

    # Create first config
    response1 = client.post(
        f"/api/v1/agents/{sample_agent.id}/interrupt",
        json=config_data
    )
    assert response1.status_code == 201

    # Try to create again for same tool
    response2 = client.post(
        f"/api/v1/agents/{sample_agent.id}/interrupt",
        json=config_data
    )
    assert response2.status_code == 409


def test_list_interrupt_configs(client: TestClient, sample_agent: Agent):
    """Test listing all interrupt configurations."""
    # Create multiple configs
    tools = ["delete_file", "write_file", "execute_code"]

    for tool_name in tools:
        config_data = {
            "tool_name": tool_name,
            "allowed_decisions": ["approve", "reject"],
            "config": {}
        }
        client.post(
            f"/api/v1/agents/{sample_agent.id}/interrupt",
            json=config_data
        )

    # List configs
    response = client.get(f"/api/v1/agents/{sample_agent.id}/interrupt")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["configs"]) == 3


def test_get_interrupt_config_by_tool(client: TestClient, sample_agent: Agent):
    """Test getting interrupt config for specific tool."""
    # Create config
    config_data = {
        "tool_name": "delete_file",
        "allowed_decisions": ["approve", "reject"],
        "config": {}
    }
    client.post(
        f"/api/v1/agents/{sample_agent.id}/interrupt",
        json=config_data
    )

    # Get config by tool
    response = client.get(
        f"/api/v1/agents/{sample_agent.id}/interrupt/delete_file"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["tool_name"] == "delete_file"


def test_get_interrupt_config_not_found(client: TestClient, sample_agent: Agent):
    """Test getting config for non-existent tool returns 404."""
    response = client.get(
        f"/api/v1/agents/{sample_agent.id}/interrupt/nonexistent_tool"
    )
    assert response.status_code == 404


def test_update_interrupt_config(client: TestClient, sample_agent: Agent):
    """Test updating interrupt configuration."""
    # Create config
    config_data = {
        "tool_name": "delete_file",
        "allowed_decisions": ["approve", "reject"],
        "config": {}
    }
    client.post(
        f"/api/v1/agents/{sample_agent.id}/interrupt",
        json=config_data
    )

    # Update to add 'edit' decision
    updated_data = {
        "tool_name": "delete_file",
        "allowed_decisions": ["approve", "edit", "reject"],
        "config": {"require_reason": True}
    }

    response = client.put(
        f"/api/v1/agents/{sample_agent.id}/interrupt/delete_file",
        json=updated_data
    )

    assert response.status_code == 200
    data = response.json()
    assert "edit" in data["allowed_decisions"]
    assert data["config"]["require_reason"] is True


def test_delete_interrupt_config(client: TestClient, sample_agent: Agent):
    """Test deleting interrupt configuration."""
    # Create config
    config_data = {
        "tool_name": "delete_file",
        "allowed_decisions": ["approve", "reject"],
        "config": {}
    }
    client.post(
        f"/api/v1/agents/{sample_agent.id}/interrupt",
        json=config_data
    )

    # Delete config
    response = client.delete(
        f"/api/v1/agents/{sample_agent.id}/interrupt/delete_file"
    )

    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(
        f"/api/v1/agents/{sample_agent.id}/interrupt/delete_file"
    )
    assert get_response.status_code == 404


# ============================================================================
# Combined Advanced Configuration Endpoint
# ============================================================================


def test_get_all_advanced_configs(client: TestClient, sample_agent: Agent):
    """Test getting all advanced configurations at once."""
    # Create backend config
    backend_data = {
        "backend_type": "composite",
        "config": {
            "routes": {"/memories/": {"type": "store"}},
            "default": {"type": "state"}
        }
    }
    client.post(f"/api/v1/agents/{sample_agent.id}/backend", json=backend_data)

    # Create memory namespace
    client.post(f"/api/v1/agents/{sample_agent.id}/memory/namespace", json={})

    # Create memory file
    file_data = {"key": "context.md", "value": "# Context"}
    client.post(f"/api/v1/agents/{sample_agent.id}/memory/files", json=file_data)

    # Create interrupt config
    interrupt_data = {
        "tool_name": "delete_file",
        "allowed_decisions": ["approve", "reject"],
        "config": {}
    }
    client.post(f"/api/v1/agents/{sample_agent.id}/interrupt", json=interrupt_data)

    # Get all configs
    response = client.get(f"/api/v1/agents/{sample_agent.id}/advanced-config")

    assert response.status_code == 200
    data = response.json()

    # Verify all components are present
    assert "backend_config" in data
    assert data["backend_config"]["backend_type"] == "composite"

    assert "memory_namespace" in data
    assert "namespace" in data["memory_namespace"]

    assert "memory_files" in data
    assert data["memory_files"]["total_files"] == 1

    assert "interrupt_configs" in data
    assert data["interrupt_configs"]["total"] == 1


def test_get_all_advanced_configs_empty(client: TestClient, sample_agent: Agent):
    """Test getting configs when none are configured."""
    response = client.get(f"/api/v1/agents/{sample_agent.id}/advanced-config")

    assert response.status_code == 200
    data = response.json()

    # All should be null/empty
    assert data["backend_config"] is None
    assert data["memory_namespace"] is None
    assert data["memory_files"]["total_files"] == 0
    assert data["interrupt_configs"]["total"] == 0


# ============================================================================
# Error Handling and Validation Tests
# ============================================================================


def test_backend_config_invalid_type(client: TestClient, sample_agent: Agent):
    """Test that invalid backend type is rejected."""
    config_data = {
        "backend_type": "invalid_type",
        "config": {}
    }

    response = client.post(
        f"/api/v1/agents/{sample_agent.id}/backend",
        json=config_data
    )

    assert response.status_code == 422  # Validation error


def test_interrupt_config_invalid_decision(client: TestClient, sample_agent: Agent):
    """Test that invalid decision type is rejected."""
    config_data = {
        "tool_name": "delete_file",
        "allowed_decisions": ["approve", "invalid_decision"],
        "config": {}
    }

    response = client.post(
        f"/api/v1/agents/{sample_agent.id}/interrupt",
        json=config_data
    )

    assert response.status_code == 422  # Validation error


def test_memory_file_empty_key(client: TestClient, sample_agent: Agent):
    """Test that empty file key is rejected."""
    # Create namespace first
    client.post(f"/api/v1/agents/{sample_agent.id}/memory/namespace", json={})

    file_data = {
        "key": "",
        "value": "content"
    }

    response = client.post(
        f"/api/v1/agents/{sample_agent.id}/memory/files",
        json=file_data
    )

    assert response.status_code == 422


def test_agent_not_found(client: TestClient):
    """Test that operations on non-existent agent return 404."""
    non_existent_id = 99999

    response = client.get(f"/api/v1/agents/{non_existent_id}/backend")
    assert response.status_code == 404

    response = client.get(f"/api/v1/agents/{non_existent_id}/memory/namespace")
    assert response.status_code == 404

    response = client.get(f"/api/v1/agents/{non_existent_id}/interrupt")
    assert response.status_code == 404
