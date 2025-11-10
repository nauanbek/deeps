"""
Store Manager for deepagents persistent storage.

Manages Store instances for long-term memory persistence across
agent executions and threads.
"""

import base64
from typing import Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.advanced_config import AgentMemoryFile


class PostgreSQLStore:
    """
    PostgreSQL-backed Store for persistent agent memory.

    Stores files in the agent_memory_files table, keyed by
    namespace and file path.

    Thread Safety:
        This class is designed to work with a single SQLAlchemy AsyncSession.
        SQLAlchemy sessions are NOT safe for concurrent write operations
        (simultaneous commits). In production, each HTTP request receives its
        own database session via dependency injection, which naturally provides
        isolation for concurrent requests.

        For concurrent operations within the same application context, create
        separate PostgreSQLStore instances with different sessions.

    Usage:
        store = PostgreSQLStore(namespace="agent_123", db_session=session)
        await store.put("context.md", b"content here")
        content = await store.get("context.md")
    """

    def __init__(self, namespace: str, db_session: Optional[AsyncSession] = None):
        """
        Initialize PostgreSQL store.

        Args:
            namespace: Unique namespace for this store
            db_session: Optional async database session (if None, creates new)
        """
        self.namespace = namespace
        self.db_session = db_session

    async def _get_session(self) -> AsyncSession:
        """Get or create database session."""
        if self.db_session:
            return self.db_session
        # Create new session (for standalone usage)
        async for session in get_db():
            return session

    async def get(self, key: str) -> Optional[bytes]:
        """
        Retrieve value from store.

        Args:
            key: File key (path)

        Returns:
            bytes: File content, or None if not found
        """
        session = await self._get_session()

        # Query for file
        from sqlalchemy import select
        stmt = select(AgentMemoryFile).where(
            AgentMemoryFile.namespace == self.namespace,
            AgentMemoryFile.key == key
        )
        result = await session.execute(stmt)
        file_record = result.scalar_one_or_none()

        if file_record:
            # Decode from base64 (for binary data) or UTF-8 (for text data)
            try:
                # Try base64 decode first (for binary data)
                return base64.b64decode(file_record.value)
            except Exception:
                # Fall back to UTF-8 (for legacy text data)
                return file_record.value.encode('utf-8')
        return None

    async def put(self, key: str, value: bytes) -> None:
        """
        Store value in store.

        Args:
            key: File key (path)
            value: File content (bytes or None)
        """
        session = await self._get_session()

        # Handle None value
        if value is None:
            value_str = ""
            size_bytes = 0
        else:
            # Encode to base64 for TEXT storage (works for both binary and text)
            if isinstance(value, bytes):
                value_str = base64.b64encode(value).decode('ascii')
                size_bytes = len(value)
            else:
                # Convert non-bytes to string, then encode
                value_bytes = str(value).encode('utf-8')
                value_str = base64.b64encode(value_bytes).decode('ascii')
                size_bytes = len(value_bytes)

        # Check if file exists
        from sqlalchemy import select
        stmt = select(AgentMemoryFile).where(
            AgentMemoryFile.namespace == self.namespace,
            AgentMemoryFile.key == key
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing file
            existing.value = value_str
            existing.size_bytes = size_bytes
        else:
            # Create new file
            new_file = AgentMemoryFile(
                namespace=self.namespace,
                key=key,
                value=value_str,
                size_bytes=size_bytes,
                content_type='text/plain'
            )
            session.add(new_file)

        await session.commit()

    async def delete(self, key: str) -> bool:
        """
        Delete value from store.

        Args:
            key: File key (path)

        Returns:
            bool: True if deleted, False if not found
        """
        session = await self._get_session()

        # Find and delete file
        from sqlalchemy import select, delete
        stmt = delete(AgentMemoryFile).where(
            AgentMemoryFile.namespace == self.namespace,
            AgentMemoryFile.key == key
        )
        result = await session.execute(stmt)
        await session.commit()

        return result.rowcount > 0

    async def list_keys(self, prefix: str = "") -> list[str]:
        """
        List all keys in store with optional prefix filter.

        Args:
            prefix: Optional key prefix to filter by

        Returns:
            list[str]: List of keys matching prefix
        """
        session = await self._get_session()

        from sqlalchemy import select
        stmt = select(AgentMemoryFile.key).where(
            AgentMemoryFile.namespace == self.namespace
        )

        if prefix:
            stmt = stmt.where(AgentMemoryFile.key.startswith(prefix))

        result = await session.execute(stmt)
        return [row[0] for row in result.all()]

    async def clear(self) -> int:
        """
        Clear all files in this namespace.

        Returns:
            int: Number of files deleted
        """
        session = await self._get_session()

        from sqlalchemy import delete
        stmt = delete(AgentMemoryFile).where(
            AgentMemoryFile.namespace == self.namespace
        )
        result = await session.execute(stmt)
        await session.commit()

        return result.rowcount


class StoreManager:
    """
    Manager for creating and caching Store instances.

    Handles store lifecycle and provides factory methods for
    different store types.

    Usage:
        manager = StoreManager()
        store = await manager.get_store(namespace="agent_123", store_type="postgresql")
    """

    def __init__(self):
        """Initialize store manager with cache."""
        self._store_cache: Dict[str, PostgreSQLStore] = {}

    async def get_store(
        self,
        namespace: str,
        store_type: str = "postgresql",
        db_session: Optional[AsyncSession] = None
    ) -> PostgreSQLStore:
        """
        Get or create a Store instance.

        Args:
            namespace: Unique namespace for the store
            store_type: Type of store (currently only 'postgresql' supported)
            db_session: Optional database session

        Returns:
            PostgreSQLStore: Store instance

        Raises:
            ValueError: If store_type is unsupported
        """
        if store_type != "postgresql":
            raise ValueError(f"Unsupported store type: {store_type}")

        # Check cache
        cache_key = f"{store_type}:{namespace}"
        if cache_key in self._store_cache:
            return self._store_cache[cache_key]

        # Create new store
        store = PostgreSQLStore(namespace=namespace, db_session=db_session)
        self._store_cache[cache_key] = store

        return store

    async def create_namespace(
        self,
        agent_id: int,
        db_session: AsyncSession
    ) -> str:
        """
        Create a memory namespace for an agent.

        Args:
            agent_id: Agent ID
            db_session: Database session

        Returns:
            str: Created namespace

        Raises:
            ValueError: If namespace already exists
        """
        from models.advanced_config import AgentMemoryNamespace
        from sqlalchemy import select

        # Generate namespace
        namespace = f"agent_{agent_id}"

        # Check if exists
        stmt = select(AgentMemoryNamespace).where(
            AgentMemoryNamespace.namespace == namespace
        )
        result = await db_session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError(f"Namespace {namespace} already exists")

        # Create namespace record
        namespace_record = AgentMemoryNamespace(
            agent_id=agent_id,
            namespace=namespace,
            store_type="postgresql",
            config={}
        )
        db_session.add(namespace_record)
        await db_session.commit()

        return namespace

    async def get_namespace(
        self,
        agent_id: int,
        db_session: AsyncSession
    ) -> Optional[str]:
        """
        Get memory namespace for an agent.

        Args:
            agent_id: Agent ID
            db_session: Database session

        Returns:
            str: Namespace if exists, None otherwise
        """
        from models.advanced_config import AgentMemoryNamespace
        from sqlalchemy import select

        stmt = select(AgentMemoryNamespace).where(
            AgentMemoryNamespace.agent_id == agent_id
        )
        result = await db_session.execute(stmt)
        namespace_record = result.scalar_one_or_none()

        if namespace_record:
            return namespace_record.namespace
        return None

    async def delete_namespace(
        self,
        namespace: str,
        db_session: AsyncSession
    ) -> bool:
        """
        Delete a memory namespace and all its files.

        Args:
            namespace: Namespace to delete
            db_session: Database session

        Returns:
            bool: True if deleted, False if not found
        """
        from models.advanced_config import AgentMemoryNamespace
        from sqlalchemy import delete

        # Delete all files in namespace
        store = await self.get_store(namespace, db_session=db_session)
        await store.clear()

        # Delete namespace record
        stmt = delete(AgentMemoryNamespace).where(
            AgentMemoryNamespace.namespace == namespace
        )
        result = await db_session.execute(stmt)
        await db_session.commit()

        # Remove from cache
        cache_key = f"postgresql:{namespace}"
        if cache_key in self._store_cache:
            del self._store_cache[cache_key]

        return result.rowcount > 0


# Singleton instance
store_manager = StoreManager()
