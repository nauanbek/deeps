"""
Mock deepagents.backends module.

Provides mock implementations of backend protocols and classes.
"""

from typing import Any, Dict, Optional, Protocol
import sys
from pathlib import Path

# Add parent directory to path to import core modules
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from core.path_validator import PathValidator, PathTraversalError
except ImportError:
    # Fallback if core module not available (shouldn't happen in production)
    PathValidator = None  # type: ignore
    PathTraversalError = ValueError


class BackendProtocol(Protocol):
    """
    Protocol defining the backend interface for deepagents.

    Backends provide storage for agent state and data.
    """

    def get(self, key: str) -> Optional[Any]:
        """Get value by key."""
        ...

    def set(self, key: str, value: Any) -> None:
        """Set value by key."""
        ...

    def delete(self, key: str) -> None:
        """Delete value by key."""
        ...

    def list_keys(self, prefix: str = "") -> list[str]:
        """List all keys with optional prefix."""
        ...


class StateBackend:
    """
    Mock implementation of in-memory state backend.

    Provides ephemeral storage using a Python dictionary.
    """

    def __init__(self):
        self._storage: Dict[str, Any] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get value by key."""
        return self._storage.get(key)

    def set(self, key: str, value: Any) -> None:
        """Set value by key."""
        self._storage[key] = value

    def delete(self, key: str) -> None:
        """Delete value by key."""
        self._storage.pop(key, None)

    def list_keys(self, prefix: str = "") -> list[str]:
        """List all keys with optional prefix."""
        if not prefix:
            return list(self._storage.keys())
        return [k for k in self._storage.keys() if k.startswith(prefix)]


class FilesystemBackend:
    """
    Mock implementation of filesystem backend with path traversal protection.

    Provides file system access (virtual or real) with security validation.
    All paths are validated to prevent path traversal attacks.
    """

    def __init__(self, virtual_mode: bool = True, base_path: str = "/tmp"):
        self.virtual_mode = virtual_mode
        self.base_path = base_path
        self._virtual_fs: Dict[str, bytes] = {}

        # Initialize path validator for security (only in real mode)
        if not virtual_mode and PathValidator is not None:
            import os
            # Create base_path if it doesn't exist
            os.makedirs(base_path, exist_ok=True)
            self._validator = PathValidator(base_path)
        else:
            self._validator = None

    def read_file(self, path: str) -> bytes:
        """
        Read file content with path traversal protection.

        Args:
            path: Relative path to file

        Returns:
            File content as bytes

        Raises:
            PathTraversalError: If path attempts to escape sandbox
            FileNotFoundError: If file doesn't exist
        """
        if self.virtual_mode:
            return self._virtual_fs.get(path, b"")
        else:
            # Validate and sanitize path
            if self._validator:
                safe_path = self._validator.get_safe_path(path)
                with open(safe_path, "rb") as f:
                    return f.read()
            else:
                # Fallback (legacy, less secure)
                import os
                full_path = os.path.join(self.base_path, path.lstrip("/"))
                with open(full_path, "rb") as f:
                    return f.read()

    def write_file(self, path: str, content: bytes) -> None:
        """
        Write file content with path traversal protection.

        Args:
            path: Relative path to file
            content: Content to write as bytes

        Raises:
            PathTraversalError: If path attempts to escape sandbox
        """
        if self.virtual_mode:
            self._virtual_fs[path] = content
        else:
            # Validate and sanitize path
            if self._validator:
                safe_path = self._validator.get_safe_path(path, create_parents=True)
                with open(safe_path, "wb") as f:
                    f.write(content)
            else:
                # Fallback (legacy, less secure)
                import os
                full_path = os.path.join(self.base_path, path.lstrip("/"))
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "wb") as f:
                    f.write(content)

    def delete_file(self, path: str) -> None:
        """
        Delete file with path traversal protection.

        Args:
            path: Relative path to file

        Raises:
            PathTraversalError: If path attempts to escape sandbox
        """
        if self.virtual_mode:
            self._virtual_fs.pop(path, None)
        else:
            # Validate and sanitize path
            if self._validator:
                safe_path = self._validator.get_safe_path(path)
                if safe_path.exists():
                    safe_path.unlink()
            else:
                # Fallback (legacy, less secure)
                import os
                full_path = os.path.join(self.base_path, path.lstrip("/"))
                if os.path.exists(full_path):
                    os.remove(full_path)

    def list_files(self, prefix: str = "") -> list[str]:
        """
        List all files with optional prefix and path traversal protection.

        Args:
            prefix: Optional prefix to filter files

        Returns:
            List of file paths within sandbox

        Raises:
            PathTraversalError: If prefix attempts to escape sandbox
        """
        if self.virtual_mode:
            if not prefix:
                return list(self._virtual_fs.keys())
            return [k for k in self._virtual_fs.keys() if k.startswith(prefix)]
        else:
            import os
            # Validate prefix if provided
            if prefix and self._validator:
                safe_prefix_path = self._validator.get_safe_path(prefix)
                if not safe_prefix_path.exists():
                    return []
                return [
                    str(p.relative_to(self.base_path))
                    for p in safe_prefix_path.rglob("*")
                    if p.is_file()
                ]
            else:
                # Fallback (legacy, less secure)
                full_path = os.path.join(self.base_path, prefix.lstrip("/")) if prefix else self.base_path
                if not os.path.exists(full_path):
                    return []
                return [
                    os.path.join(root, file)
                    for root, _, files in os.walk(full_path)
                    for file in files
                ]


class CompositeBackend:
    """
    Mock implementation of composite backend.

    Routes operations to different backends based on path prefixes.
    """

    def __init__(self, routes: Dict[str, Any], default: Optional[Any] = None):
        self.routes = routes
        self.default = default or StateBackend()

    def _get_backend(self, key: str) -> Any:
        """Get appropriate backend for key."""
        for prefix, backend in self.routes.items():
            if key.startswith(prefix):
                return backend
        return self.default

    def get(self, key: str) -> Optional[Any]:
        """Get value by key."""
        backend = self._get_backend(key)
        return backend.get(key)

    def set(self, key: str, value: Any) -> None:
        """Set value by key."""
        backend = self._get_backend(key)
        backend.set(key, value)

    def delete(self, key: str) -> None:
        """Delete value by key."""
        backend = self._get_backend(key)
        backend.delete(key)

    def list_keys(self, prefix: str = "") -> list[str]:
        """List all keys with optional prefix."""
        all_keys = []
        for backend in list(self.routes.values()) + [self.default]:
            all_keys.extend(backend.list_keys(prefix))
        return all_keys


__all__ = [
    "BackendProtocol",
    "StateBackend",
    "FilesystemBackend",
    "CompositeBackend",
]
