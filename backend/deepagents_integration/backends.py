"""
Backend Manager for deepagents storage backends.

Manages creation and configuration of different storage backends:
- StateBackend: Ephemeral in-state storage (default)
- FilesystemBackend: Real or virtual filesystem access
- StoreBackend: Persistent cross-thread storage
- CompositeBackend: Hybrid storage with routing rules
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Add mock deepagents to path for development/testing
mock_path = Path(__file__).parent.parent / "deepagents_mock"
if mock_path.exists() and str(mock_path) not in sys.path:
    sys.path.insert(0, str(mock_path.parent))

try:
    from deepagents.backends import (
        BackendProtocol,
        CompositeBackend,
        FilesystemBackend,
        StateBackend,
    )
    from deepagents.backends.store import StoreBackend
except ImportError:
    # Fallback to mock if deepagents not installed
    from deepagents_mock.backends import (
        BackendProtocol,
        CompositeBackend,
        FilesystemBackend,
        StateBackend,
    )
    from deepagents_mock.backends.store import StoreBackend


class BackendManager:
    """
    Factory for creating and configuring storage backends.

    Handles the creation of different backend types from configuration
    dictionaries, enabling flexible storage strategies for agents.

    Usage:
        manager = BackendManager()
        backend = manager.create_backend(config, runtime)
    """

    def create_backend(
        self,
        config: Dict[str, Any],
        runtime: Any,
        store: Optional[Any] = None
    ) -> BackendProtocol:
        """
        Create a backend from configuration.

        Args:
            config: Backend configuration dictionary
            runtime: Runtime instance for StateBackend
            store: Optional Store instance for StoreBackend

        Returns:
            BackendProtocol: Configured backend instance

        Raises:
            ValueError: If backend type is unsupported or config is invalid

        Examples:
            # StateBackend (ephemeral, in-memory)
            config = {"type": "state"}
            backend = manager.create_backend(config, runtime)

            # FilesystemBackend (real or virtual filesystem)
            config = {
                "type": "filesystem",
                "root_dir": "/workspace/agent_123",
                "virtual_mode": False
            }
            backend = manager.create_backend(config, runtime)

            # StoreBackend (persistent cross-thread storage)
            config = {"type": "store"}
            backend = manager.create_backend(config, runtime, store=store)

            # CompositeBackend (hybrid with routing)
            config = {
                "type": "composite",
                "routes": {
                    "/memories/": {"type": "store"},
                    "/scratch/": {"type": "state"}
                },
                "default": {"type": "state"}
            }
            backend = manager.create_backend(config, runtime, store=store)
        """
        backend_type = config.get("type", "state")

        if backend_type == "state":
            return self._create_state_backend(runtime)

        elif backend_type == "filesystem":
            return self._create_filesystem_backend(config)

        elif backend_type == "store":
            # Store is obtained from runtime, not passed explicitly
            return self._create_store_backend(runtime, store)

        elif backend_type == "composite":
            return self._create_composite_backend(config, runtime, store)

        else:
            raise ValueError(f"Unsupported backend type: {backend_type}")

    def _create_state_backend(self, runtime: Any) -> StateBackend:
        """
        Create StateBackend (ephemeral in-state storage).

        Args:
            runtime: Runtime instance

        Returns:
            StateBackend: Configured state backend
        """
        return StateBackend(runtime)

    def _create_filesystem_backend(self, config: Dict[str, Any]) -> FilesystemBackend:
        """
        Create FilesystemBackend (real or virtual filesystem).

        Args:
            config: Configuration with:
                - root_dir: Root directory for filesystem (default: ".")
                - virtual_mode: If True, uses virtual FS; if False, real FS (default: True)

        Returns:
            FilesystemBackend: Configured filesystem backend

        Security Notes:
            - virtual_mode=False provides real filesystem access
            - root_dir should be carefully sandboxed to prevent path traversal
            - Consider using chroot-like isolation for production
        """
        root_dir = config.get("root_dir", ".")
        virtual_mode = config.get("virtual_mode", True)

        return FilesystemBackend(
            root_dir=root_dir,
            virtual_mode=virtual_mode
        )

    def _create_store_backend(self, runtime: Any, store: Any) -> StoreBackend:
        """
        Create StoreBackend (persistent cross-thread storage).

        Args:
            runtime: Runtime instance with store configured
            store: Store instance (PostgreSQL, Redis, etc.) - not used, kept for API compatibility

        Returns:
            StoreBackend: Configured store backend
        """
        return StoreBackend(runtime)

    def _create_composite_backend(
        self,
        config: Dict[str, Any],
        runtime: Any,
        store: Optional[Any] = None
    ) -> CompositeBackend:
        """
        Create CompositeBackend (hybrid storage with routing).

        Routes different paths to different backends based on configuration.

        Args:
            config: Configuration with:
                - routes: Dict mapping paths to backend configs
                  Example: {"/memories/": {"type": "store"}, "/scratch/": {"type": "state"}}
                - default: Default backend config (optional, defaults to StateBackend)
            runtime: Runtime instance
            store: Optional Store instance for StoreBackend routes

        Returns:
            CompositeBackend: Configured composite backend

        Example:
            config = {
                "type": "composite",
                "routes": {
                    "/memories/": {"type": "store"},  # Persistent memory
                    "/workspace/": {"type": "filesystem", "root_dir": "/tmp/agent"}
                },
                "default": {"type": "state"}  # Ephemeral by default
            }
        """
        # === COMPOSITE BACKEND ROUTING ALGORITHM ===
        # This creates a hybrid storage system that routes file operations to different
        # backends based on path prefixes, enabling sophisticated storage strategies.
        #
        # How routing works:
        # 1. Agent writes to "/memories/context.md"
        #    → Checks routes for "/memories/" prefix
        #    → Routes to StoreBackend (persistent PostgreSQL storage)
        #
        # 2. Agent writes to "/scratch/temp.txt"
        #    → Checks routes for "/scratch/" prefix
        #    → Routes to StateBackend (ephemeral in-memory storage)
        #
        # 3. Agent writes to "/output/result.json"
        #    → No matching route found
        #    → Falls back to default backend
        #
        # This enables patterns like:
        # - Long-term memory in PostgreSQL (/memories/)
        # - Temporary files in RAM (/scratch/, /tmp/)
        # - Working directory on real filesystem (/workspace/)
        # === END ALGORITHM DESCRIPTION ===

        # Extract configuration sections
        routes_config = config.get("routes", {})
        default_config = config.get("default", {"type": "state"})

        # STEP 1: Create the default (fallback) backend
        # This backend handles all paths that don't match any route
        # Defaults to StateBackend (ephemeral) if not specified
        default_backend = self.create_backend(default_config, runtime, store)

        # STEP 2: Create routed backends for each path prefix
        # Each route maps a path prefix (e.g., "/memories/") to a specific backend type
        # The CompositeBackend will use these for matching paths
        routes = {}
        for path, backend_config in routes_config.items():
            # Recursively create backend for this route
            # This allows nested configuration (e.g., composite routes within composite)
            routes[path] = self.create_backend(backend_config, runtime, store)

        # STEP 3: Assemble the CompositeBackend with default + routes
        # The CompositeBackend class handles the actual routing logic at runtime
        return CompositeBackend(
            default=default_backend,
            routes=routes
        )

    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate backend configuration.

        Args:
            config: Backend configuration to validate

        Returns:
            tuple: (is_valid, error_message)

        Example:
            is_valid, error = manager.validate_config(config)
            if not is_valid:
                raise ValueError(error)
        """
        backend_type = config.get("type")

        if not backend_type:
            return False, "Backend type is required"

        if backend_type not in ["state", "filesystem", "store", "composite"]:
            return False, f"Unsupported backend type: {backend_type}"

        # Type-specific validation
        if backend_type == "filesystem":
            root_dir = config.get("root_dir")
            if root_dir and ".." in root_dir:
                return False, "root_dir cannot contain '..' (path traversal)"

        elif backend_type == "composite":
            routes = config.get("routes")
            if not routes or not isinstance(routes, dict):
                return False, "Composite backend requires 'routes' dictionary"

            # Validate each route's backend config
            for path, route_config in routes.items():
                is_valid, error = self.validate_config(route_config)
                if not is_valid:
                    return False, f"Invalid route '{path}': {error}"

        return True, None


# Singleton instance
backend_manager = BackendManager()
