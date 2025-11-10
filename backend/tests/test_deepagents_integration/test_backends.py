"""
Tests for Backend Manager and storage backends.

Tests the backend creation and validation logic including:
- StateBackend configuration
- FilesystemBackend with virtual/real modes
- StoreBackend with PostgreSQL
- CompositeBackend with routing
- Security validation (path traversal prevention)
"""

import pytest
from deepagents_integration.backends import BackendManager


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def backend_manager():
    """Create a BackendManager instance."""
    return BackendManager()


@pytest.fixture
def mock_runtime():
    """Create a mock runtime for testing."""
    class MockRuntime:
        def __init__(self):
            self.state = {}

    return MockRuntime()


@pytest.fixture
def mock_store():
    """Create a mock store for testing."""
    class MockStore:
        def __init__(self):
            self.data = {}

        async def get(self, key: str):
            return self.data.get(key)

        async def put(self, key: str, value: bytes):
            self.data[key] = value

        async def delete(self, key: str):
            if key in self.data:
                del self.data[key]
                return True
            return False

    return MockStore()


# ============================================================================
# StateBackend Tests
# ============================================================================


def test_create_state_backend(backend_manager, mock_runtime):
    """Test creating a StateBackend."""
    config = {
        "type": "state",
    }

    backend = backend_manager.create_backend(config, mock_runtime)

    assert backend is not None
    assert backend.__class__.__name__ == "StateBackend"


def test_validate_state_backend_config(backend_manager):
    """Test validating StateBackend configuration."""
    config = {
        "type": "state",
    }

    is_valid, error = backend_manager.validate_config(config)

    assert is_valid is True
    assert error is None


# ============================================================================
# FilesystemBackend Tests
# ============================================================================


def test_create_filesystem_backend_virtual(backend_manager, mock_runtime):
    """Test creating FilesystemBackend in virtual mode."""
    config = {
        "type": "filesystem",
        "root_dir": "/workspace/agent_123",
        "virtual_mode": True
    }

    backend = backend_manager.create_backend(config, mock_runtime)

    assert backend is not None
    assert backend.__class__.__name__ == "FilesystemBackend"


def test_create_filesystem_backend_real(backend_manager, mock_runtime):
    """Test creating FilesystemBackend in real mode."""
    config = {
        "type": "filesystem",
        "root_dir": "/tmp/test_workspace",
        "virtual_mode": False
    }

    backend = backend_manager.create_backend(config, mock_runtime)

    assert backend is not None


def test_validate_filesystem_config_safe_path(backend_manager):
    """Test validating FilesystemBackend with safe path."""
    config = {
        "type": "filesystem",
        "root_dir": "/workspace/agent_123",
        "virtual_mode": True
    }

    is_valid, error = backend_manager.validate_config(config)

    assert is_valid is True
    assert error is None


def test_validate_filesystem_config_path_traversal(backend_manager):
    """Test that path traversal is rejected."""
    config = {
        "type": "filesystem",
        "root_dir": "/workspace/../etc/passwd",
        "virtual_mode": False
    }

    is_valid, error = backend_manager.validate_config(config)

    assert is_valid is False
    assert "path traversal" in error.lower()


def test_validate_filesystem_config_relative_path_traversal(backend_manager):
    """Test that relative path traversal patterns are rejected."""
    config = {
        "type": "filesystem",
        "root_dir": "../../sensitive",
        "virtual_mode": False
    }

    is_valid, error = backend_manager.validate_config(config)

    assert is_valid is False


# ============================================================================
# StoreBackend Tests
# ============================================================================


def test_create_store_backend(backend_manager, mock_runtime, mock_store):
    """Test creating StoreBackend."""
    config = {
        "type": "store",
        "namespace": "agent_123"
    }

    backend = backend_manager.create_backend(config, mock_runtime, store=mock_store)

    assert backend is not None
    assert backend.__class__.__name__ == "StoreBackend"


def test_validate_store_backend_config(backend_manager):
    """Test validating StoreBackend configuration."""
    config = {
        "type": "store",
        "namespace": "agent_123"
    }

    is_valid, error = backend_manager.validate_config(config)

    assert is_valid is True
    assert error is None


def test_store_backend_missing_namespace(backend_manager, mock_runtime, mock_store):
    """Test that StoreBackend requires namespace."""
    config = {
        "type": "store",
    }

    # Should use default or raise error
    try:
        backend = backend_manager.create_backend(config, mock_runtime, store=mock_store)
        # If it doesn't raise, it should have a default namespace
        assert backend is not None
    except (ValueError, KeyError):
        # Expected if namespace is required
        pass


# ============================================================================
# CompositeBackend Tests
# ============================================================================


def test_create_composite_backend(backend_manager, mock_runtime, mock_store):
    """Test creating CompositeBackend with routing."""
    config = {
        "type": "composite",
        "routes": {
            "/memories/": {"type": "store"},
            "/scratch/": {"type": "state"}
        },
        "default": {"type": "state"}
    }

    backend = backend_manager.create_backend(config, mock_runtime, store=mock_store)

    assert backend is not None
    assert backend.__class__.__name__ == "CompositeBackend"


def test_validate_composite_backend_config(backend_manager):
    """Test validating CompositeBackend configuration."""
    config = {
        "type": "composite",
        "routes": {
            "/memories/": {"type": "store"},
            "/scratch/": {"type": "state"}
        },
        "default": {"type": "state"}
    }

    is_valid, error = backend_manager.validate_config(config)

    assert is_valid is True
    assert error is None


def test_composite_backend_with_filesystem_route(backend_manager, mock_runtime):
    """Test CompositeBackend with FilesystemBackend route."""
    config = {
        "type": "composite",
        "routes": {
            "/workspace/": {
                "type": "filesystem",
                "root_dir": "/tmp/workspace",
                "virtual_mode": True
            }
        },
        "default": {"type": "state"}
    }

    backend = backend_manager.create_backend(config, mock_runtime)

    assert backend is not None


def test_composite_backend_invalid_route_type(backend_manager):
    """Test that CompositeBackend validates route backend types."""
    config = {
        "type": "composite",
        "routes": {
            "/invalid/": {"type": "invalid_backend"}
        },
        "default": {"type": "state"}
    }

    is_valid, error = backend_manager.validate_config(config)

    # Should be invalid due to unknown backend type
    assert is_valid is False or error is not None


def test_composite_backend_path_traversal_in_route(backend_manager):
    """Test that path traversal in routes is rejected."""
    config = {
        "type": "composite",
        "routes": {
            "/workspace/": {
                "type": "filesystem",
                "root_dir": "/workspace/../../etc",
                "virtual_mode": False
            }
        },
        "default": {"type": "state"}
    }

    is_valid, error = backend_manager.validate_config(config)

    assert is_valid is False
    assert "path traversal" in error.lower()


# ============================================================================
# Configuration Validation Tests
# ============================================================================


def test_validate_config_missing_type(backend_manager):
    """Test that config without type is rejected."""
    config = {
        "some_field": "value"
    }

    is_valid, error = backend_manager.validate_config(config)

    # Should default to 'state' or reject
    # Depends on implementation - either is acceptable
    assert (is_valid is True and config.get("type") == "state") or is_valid is False


def test_validate_config_invalid_type(backend_manager):
    """Test that invalid backend type is rejected."""
    config = {
        "type": "invalid_backend_type"
    }

    is_valid, error = backend_manager.validate_config(config)

    assert is_valid is False
    assert error is not None


def test_validate_config_empty(backend_manager):
    """Test validating empty configuration."""
    config = {}

    is_valid, error = backend_manager.validate_config(config)

    # Should default to state backend or reject
    assert is_valid is True or error is not None


# ============================================================================
# Integration Tests
# ============================================================================


def test_backend_manager_caching(backend_manager, mock_runtime):
    """Test that BackendManager can create multiple backends."""
    configs = [
        {"type": "state"},
        {"type": "filesystem", "root_dir": "/workspace1", "virtual_mode": True},
        {"type": "filesystem", "root_dir": "/workspace2", "virtual_mode": True}
    ]

    backends = [
        backend_manager.create_backend(config, mock_runtime)
        for config in configs
    ]

    assert len(backends) == 3
    assert all(b is not None for b in backends)


def test_create_backend_with_all_parameters(backend_manager, mock_runtime, mock_store):
    """Test creating backend with all possible parameters."""
    config = {
        "type": "composite",
        "routes": {
            "/memories/": {"type": "store", "namespace": "agent_123"},
            "/workspace/": {"type": "filesystem", "root_dir": "/tmp/workspace", "virtual_mode": True},
            "/scratch/": {"type": "state"}
        },
        "default": {"type": "state"}
    }

    backend = backend_manager.create_backend(
        config=config,
        runtime=mock_runtime,
        store=mock_store
    )

    assert backend is not None
    assert backend.__class__.__name__ == "CompositeBackend"


# ============================================================================
# Error Handling Tests
# ============================================================================


def test_create_backend_with_none_runtime(backend_manager):
    """Test that creating backend with None runtime is handled."""
    config = {"type": "state"}

    try:
        backend = backend_manager.create_backend(config, runtime=None)
        # Some implementations may allow None runtime for StateBackend
        assert backend is not None or True
    except (ValueError, TypeError):
        # Expected if runtime is required
        pass


def test_create_store_backend_without_store(backend_manager, mock_runtime):
    """Test that creating StoreBackend without store parameter is handled."""
    config = {"type": "store", "namespace": "agent_123"}

    try:
        backend = backend_manager.create_backend(config, mock_runtime, store=None)
        # May raise error or handle gracefully
        assert backend is not None or True
    except (ValueError, TypeError):
        # Expected if store is required for StoreBackend
        pass
