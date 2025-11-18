"""
Mock deepagents.backends.store module.

Provides StoreBackend for PostgreSQL-backed persistent storage.
"""

from typing import Any, Optional


class StoreBackend:
    """
    Mock implementation of store backend.

    Provides persistent storage backed by PostgreSQL.
    """

    def __init__(self, connection_string: str, namespace: str = "default"):
        """
        Initialize store backend.

        Args:
            connection_string: PostgreSQL connection string
            namespace: Namespace for isolation
        """
        self.connection_string = connection_string
        self.namespace = namespace
        # Mock storage
        self._storage = {}

    def get(self, key: str) -> Optional[Any]:
        """Get value by key."""
        full_key = f"{self.namespace}:{key}"
        return self._storage.get(full_key)

    def set(self, key: str, value: Any) -> None:
        """Set value by key."""
        full_key = f"{self.namespace}:{key}"
        self._storage[full_key] = value

    def delete(self, key: str) -> None:
        """Delete value by key."""
        full_key = f"{self.namespace}:{key}"
        self._storage.pop(full_key, None)

    def list_keys(self, prefix: str = "") -> list[str]:
        """List all keys with optional prefix."""
        full_prefix = f"{self.namespace}:{prefix}"
        return [
            k[len(self.namespace) + 1:]
            for k in self._storage.keys()
            if k.startswith(full_prefix)
        ]


__all__ = ["StoreBackend"]
