"""
Mock deepagents.backends module.

Provides mock implementations of backend protocols and classes.
"""

from typing import Any, Dict, Optional, Protocol


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
    Mock implementation of filesystem backend.

    Provides file system access (virtual or real).
    """

    def __init__(self, virtual_mode: bool = True, base_path: str = "/tmp"):
        self.virtual_mode = virtual_mode
        self.base_path = base_path
        self._virtual_fs: Dict[str, bytes] = {}

    def read_file(self, path: str) -> bytes:
        """Read file content."""
        if self.virtual_mode:
            return self._virtual_fs.get(path, b"")
        else:
            import os
            full_path = os.path.join(self.base_path, path.lstrip("/"))
            with open(full_path, "rb") as f:
                return f.read()

    def write_file(self, path: str, content: bytes) -> None:
        """Write file content."""
        if self.virtual_mode:
            self._virtual_fs[path] = content
        else:
            import os
            full_path = os.path.join(self.base_path, path.lstrip("/"))
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "wb") as f:
                f.write(content)

    def delete_file(self, path: str) -> None:
        """Delete file."""
        if self.virtual_mode:
            self._virtual_fs.pop(path, None)
        else:
            import os
            full_path = os.path.join(self.base_path, path.lstrip("/"))
            if os.path.exists(full_path):
                os.remove(full_path)

    def list_files(self, prefix: str = "") -> list[str]:
        """List all files with optional prefix."""
        if self.virtual_mode:
            if not prefix:
                return list(self._virtual_fs.keys())
            return [k for k in self._virtual_fs.keys() if k.startswith(prefix)]
        else:
            import os
            full_path = os.path.join(self.base_path, prefix.lstrip("/"))
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
