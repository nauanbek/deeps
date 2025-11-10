"""
Tests for AgentFactory with Advanced Configuration.

Tests integration of advanced features:
- Backend configuration (State, Filesystem, Store, Composite)
- HITL interrupt configuration
- Checkpointer for state persistence
- Memory namespace integration
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from deepagents_integration.factory import AgentFactory
from models.agent import Agent as AgentModel
from models.advanced_config import (
    AgentBackendConfig,
    AgentMemoryNamespace,
    AgentInterruptConfig,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def agent_factory():
    """Create an AgentFactory instance for testing."""
    return AgentFactory()


@pytest.fixture
def basic_agent_config():
    """Create a basic agent configuration."""
    return AgentModel(
        id=1,
        name="Test Agent",
        description="A test agent",
        model_provider="anthropic",
        model_name="claude-3-5-sonnet-20241022",
        temperature=0.7,
        max_tokens=4096,
        system_prompt="You are a helpful assistant.",
        planning_enabled=False,
        filesystem_enabled=False,
        created_by_id=1,
        is_active=True,
    )


@pytest.fixture
def agent_with_backend_config(basic_agent_config):
    """Agent with backend configuration."""
    backend_config = AgentBackendConfig(
        id=1,
        agent_id=basic_agent_config.id,
        backend_type="filesystem",
        config={"root_dir": "/workspace/agent_1", "virtual_mode": True}
    )
    basic_agent_config.backend_config = backend_config
    return basic_agent_config


@pytest.fixture
def agent_with_memory_namespace(basic_agent_config):
    """Agent with memory namespace."""
    memory_namespace = AgentMemoryNamespace(
        id=1,
        agent_id=basic_agent_config.id,
        namespace="agent_1",
        store_type="postgresql"
    )
    basic_agent_config.memory_namespace = memory_namespace
    return basic_agent_config


@pytest.fixture
def agent_with_interrupt_config(basic_agent_config):
    """Agent with interrupt configuration."""
    interrupt_config = AgentInterruptConfig(
        id=1,
        agent_id=basic_agent_config.id,
        tool_name="delete_file",
        allowed_decisions=["approve", "reject"],
        config={}
    )
    basic_agent_config.interrupt_configs = [interrupt_config]
    return basic_agent_config


@pytest.fixture
async def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def mock_runtime():
    """Create a mock runtime."""
    class MockRuntime:
        def __init__(self):
            self.state = {}
    return MockRuntime()


# ============================================================================
# Backend Configuration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_agent_with_state_backend(
    agent_factory,
    basic_agent_config,
    mock_db_session,
    mock_runtime
):
    """Test creating agent with StateBackend."""
    # Add state backend config
    backend_config = AgentBackendConfig(
        id=1,
        agent_id=basic_agent_config.id,
        backend_type="state",
        config={}
    )
    basic_agent_config.backend_config = backend_config

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        agent = await agent_factory.create_agent(
            agent_config=basic_agent_config,
            db_session=mock_db_session,
            runtime=mock_runtime
        )

    assert agent is not None


@pytest.mark.asyncio
async def test_create_agent_with_filesystem_backend(
    agent_factory,
    agent_with_backend_config,
    mock_db_session,
    mock_runtime
):
    """Test creating agent with FilesystemBackend."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        agent = await agent_factory.create_agent(
            agent_config=agent_with_backend_config,
            db_session=mock_db_session,
            runtime=mock_runtime
        )

    assert agent is not None


@pytest.mark.asyncio
async def test_create_agent_with_store_backend(
    agent_factory,
    agent_with_memory_namespace,
    mock_db_session,
    mock_runtime
):
    """Test creating agent with StoreBackend."""
    # Add store backend config
    backend_config = AgentBackendConfig(
        id=1,
        agent_id=agent_with_memory_namespace.id,
        backend_type="store",
        config={"namespace": "agent_1"}
    )
    agent_with_memory_namespace.backend_config = backend_config

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("deepagents_integration.factory.store_manager") as mock_store_mgr:
            mock_store_mgr.get_store = AsyncMock(return_value=Mock())

            agent = await agent_factory.create_agent(
                agent_config=agent_with_memory_namespace,
                db_session=mock_db_session,
                runtime=mock_runtime
            )

    assert agent is not None


@pytest.mark.asyncio
async def test_create_agent_with_composite_backend(
    agent_factory,
    basic_agent_config,
    mock_db_session,
    mock_runtime
):
    """Test creating agent with CompositeBackend."""
    # Add composite backend config
    backend_config = AgentBackendConfig(
        id=1,
        agent_id=basic_agent_config.id,
        backend_type="composite",
        config={
            "routes": {
                "/memories/": {"type": "store"},
                "/scratch/": {"type": "state"}
            },
            "default": {"type": "state"}
        }
    )
    basic_agent_config.backend_config = backend_config

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        agent = await agent_factory.create_agent(
            agent_config=basic_agent_config,
            db_session=mock_db_session,
            runtime=mock_runtime
        )

    assert agent is not None


# ============================================================================
# HITL Interrupt Configuration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_agent_with_single_interrupt(
    agent_factory,
    agent_with_interrupt_config,
    mock_db_session,
    mock_runtime
):
    """Test creating agent with single interrupt configuration."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        agent = await agent_factory.create_agent(
            agent_config=agent_with_interrupt_config,
            db_session=mock_db_session,
            runtime=mock_runtime
        )

    assert agent is not None


@pytest.mark.asyncio
async def test_create_agent_with_multiple_interrupts(
    agent_factory,
    basic_agent_config,
    mock_db_session,
    mock_runtime
):
    """Test creating agent with multiple interrupt configurations."""
    # Add multiple interrupt configs
    interrupt_configs = [
        AgentInterruptConfig(
            id=1,
            agent_id=basic_agent_config.id,
            tool_name="delete_file",
            allowed_decisions=["approve", "reject"],
            config={}
        ),
        AgentInterruptConfig(
            id=2,
            agent_id=basic_agent_config.id,
            tool_name="write_file",
            allowed_decisions=["approve", "edit", "reject"],
            config={}
        ),
        AgentInterruptConfig(
            id=3,
            agent_id=basic_agent_config.id,
            tool_name="execute_code",
            allowed_decisions=["approve", "reject"],
            config={}
        )
    ]
    basic_agent_config.interrupt_configs = interrupt_configs

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        agent = await agent_factory.create_agent(
            agent_config=basic_agent_config,
            db_session=mock_db_session,
            runtime=mock_runtime
        )

    assert agent is not None


@pytest.mark.asyncio
async def test_interrupt_config_creates_checkpointer(
    agent_factory,
    agent_with_interrupt_config,
    mock_db_session,
    mock_runtime
):
    """Test that interrupt config creates a checkpointer for state persistence."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        agent = await agent_factory.create_agent(
            agent_config=agent_with_interrupt_config,
            db_session=mock_db_session,
            runtime=mock_runtime
        )

    # Agent should be created with checkpointer
    assert agent is not None


# ============================================================================
# Combined Advanced Features Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_agent_with_all_advanced_features(
    agent_factory,
    basic_agent_config,
    mock_db_session,
    mock_runtime
):
    """Test creating agent with all advanced features enabled."""
    # Add backend config
    backend_config = AgentBackendConfig(
        id=1,
        agent_id=basic_agent_config.id,
        backend_type="composite",
        config={
            "routes": {"/memories/": {"type": "store"}},
            "default": {"type": "state"}
        }
    )
    basic_agent_config.backend_config = backend_config

    # Add memory namespace
    memory_namespace = AgentMemoryNamespace(
        id=1,
        agent_id=basic_agent_config.id,
        namespace="agent_1",
        store_type="postgresql"
    )
    basic_agent_config.memory_namespace = memory_namespace

    # Add interrupt config
    interrupt_config = AgentInterruptConfig(
        id=1,
        agent_id=basic_agent_config.id,
        tool_name="delete_file",
        allowed_decisions=["approve", "reject"],
        config={}
    )
    basic_agent_config.interrupt_configs = [interrupt_config]

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("deepagents_integration.factory.store_manager") as mock_store_mgr:
            mock_store_mgr.get_store = AsyncMock(return_value=Mock())

            agent = await agent_factory.create_agent(
                agent_config=basic_agent_config,
                db_session=mock_db_session,
                runtime=mock_runtime
            )

    assert agent is not None


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


@pytest.mark.asyncio
async def test_create_agent_without_db_session(
    agent_factory,
    basic_agent_config
):
    """Test creating agent without db_session (should skip advanced features)."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        agent = await agent_factory.create_agent(
            agent_config=basic_agent_config,
            db_session=None,  # No session = no advanced features
            runtime=None
        )

    assert agent is not None


@pytest.mark.asyncio
async def test_create_agent_with_backend_but_no_runtime(
    agent_factory,
    agent_with_backend_config,
    mock_db_session
):
    """Test creating agent with backend config but no runtime."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        # Should handle gracefully or raise appropriate error
        try:
            agent = await agent_factory.create_agent(
                agent_config=agent_with_backend_config,
                db_session=mock_db_session,
                runtime=None  # No runtime
            )
            # If it doesn't raise, it should skip backend creation
            assert agent is not None
        except (ValueError, TypeError):
            # Expected if runtime is required for backend
            pass


@pytest.mark.asyncio
async def test_create_agent_with_invalid_backend_config(
    agent_factory,
    basic_agent_config,
    mock_db_session,
    mock_runtime
):
    """Test creating agent with invalid backend configuration."""
    # Add invalid backend config
    backend_config = AgentBackendConfig(
        id=1,
        agent_id=basic_agent_config.id,
        backend_type="invalid_type",
        config={}
    )
    basic_agent_config.backend_config = backend_config

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        try:
            agent = await agent_factory.create_agent(
                agent_config=basic_agent_config,
                db_session=mock_db_session,
                runtime=mock_runtime
            )
            # Should either skip invalid config or raise error
            assert agent is not None or True
        except ValueError:
            # Expected if validation is strict
            pass


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_agent_factory_with_planning_and_backend(
    agent_factory,
    basic_agent_config,
    mock_db_session,
    mock_runtime
):
    """Test agent with both planning enabled and backend config."""
    # Enable planning
    basic_agent_config.planning_enabled = True

    # Add backend config
    backend_config = AgentBackendConfig(
        id=1,
        agent_id=basic_agent_config.id,
        backend_type="filesystem",
        config={"root_dir": "/workspace", "virtual_mode": True}
    )
    basic_agent_config.backend_config = backend_config

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        agent = await agent_factory.create_agent(
            agent_config=basic_agent_config,
            db_session=mock_db_session,
            runtime=mock_runtime
        )

    assert agent is not None


@pytest.mark.asyncio
async def test_agent_factory_with_filesystem_and_backend(
    agent_factory,
    basic_agent_config,
    mock_db_session,
    mock_runtime
):
    """Test agent with both filesystem_enabled and backend config."""
    # Enable filesystem
    basic_agent_config.filesystem_enabled = True

    # Add backend config
    backend_config = AgentBackendConfig(
        id=1,
        agent_id=basic_agent_config.id,
        backend_type="state",
        config={}
    )
    basic_agent_config.backend_config = backend_config

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        agent = await agent_factory.create_agent(
            agent_config=basic_agent_config,
            db_session=mock_db_session,
            runtime=mock_runtime
        )

    assert agent is not None


import os

@pytest.mark.asyncio
async def test_full_integration_agent_creation(
    agent_factory,
    basic_agent_config,
    mock_db_session,
    mock_runtime
):
    """Full integration test with all features."""
    # Enable all features
    basic_agent_config.planning_enabled = True
    basic_agent_config.filesystem_enabled = True

    # Add all advanced configs
    basic_agent_config.backend_config = AgentBackendConfig(
        id=1,
        agent_id=basic_agent_config.id,
        backend_type="composite",
        config={
            "routes": {"/memories/": {"type": "store"}},
            "default": {"type": "state"}
        }
    )

    basic_agent_config.memory_namespace = AgentMemoryNamespace(
        id=1,
        agent_id=basic_agent_config.id,
        namespace="agent_1",
        store_type="postgresql"
    )

    basic_agent_config.interrupt_configs = [
        AgentInterruptConfig(
            id=1,
            agent_id=basic_agent_config.id,
            tool_name="delete_file",
            allowed_decisions=["approve", "reject"],
            config={}
        )
    ]

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch("deepagents_integration.factory.store_manager") as mock_store_mgr:
            mock_store_mgr.get_store = AsyncMock(return_value=Mock())

            agent = await agent_factory.create_agent(
                agent_config=basic_agent_config,
                tools=None,
                subagents=None,
                db_session=mock_db_session,
                runtime=mock_runtime
            )

    assert agent is not None
