"""
Tests for StoreManager and PostgreSQL Store.

Tests the persistent storage functionality including:
- Store creation and caching
- Get/put/delete operations
- Namespace management
- Error handling
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from deepagents_integration.store import StoreManager, PostgreSQLStore
from models.advanced_config import AgentMemoryNamespace, AgentMemoryFile


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def store_manager():
    """Create a StoreManager instance."""
    return StoreManager()


@pytest.fixture
async def test_namespace(db_session: AsyncSession) -> AgentMemoryNamespace:
    """Create a test memory namespace."""
    namespace = AgentMemoryNamespace(
        agent_id=1,
        namespace="test_agent_1",
        store_type="postgresql"
    )
    db_session.add(namespace)
    await db_session.commit()
    await db_session.refresh(namespace)
    return namespace


# ============================================================================
# PostgreSQLStore Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_postgresql_store(db_session: AsyncSession):
    """Test creating PostgreSQLStore instance."""
    store = PostgreSQLStore(namespace="test_123", db_session=db_session)

    assert store is not None
    assert store.namespace == "test_123"


@pytest.mark.asyncio
async def test_store_put_and_get(db_session: AsyncSession):
    """Test storing and retrieving data."""
    store = PostgreSQLStore(namespace="test_123", db_session=db_session)

    # Put data
    test_data = b"Hello, World!"
    await store.put("test_key", test_data)

    # Get data
    retrieved_data = await store.get("test_key")

    assert retrieved_data == test_data


@pytest.mark.asyncio
async def test_store_get_nonexistent_key(db_session: AsyncSession):
    """Test getting non-existent key returns None."""
    store = PostgreSQLStore(namespace="test_123", db_session=db_session)

    result = await store.get("nonexistent_key")

    assert result is None


@pytest.mark.asyncio
async def test_store_update_existing_key(db_session: AsyncSession):
    """Test updating existing key with new value."""
    store = PostgreSQLStore(namespace="test_123", db_session=db_session)

    # Put initial data
    await store.put("test_key", b"Initial value")

    # Update with new data
    await store.put("test_key", b"Updated value")

    # Retrieve updated data
    retrieved = await store.get("test_key")

    assert retrieved == b"Updated value"


@pytest.mark.asyncio
async def test_store_delete(db_session: AsyncSession):
    """Test deleting a key."""
    store = PostgreSQLStore(namespace="test_123", db_session=db_session)

    # Put data
    await store.put("test_key", b"Test data")

    # Delete
    result = await store.delete("test_key")

    assert result is True

    # Verify deleted
    retrieved = await store.get("test_key")
    assert retrieved is None


@pytest.mark.asyncio
async def test_store_delete_nonexistent_key(db_session: AsyncSession):
    """Test deleting non-existent key returns False."""
    store = PostgreSQLStore(namespace="test_123", db_session=db_session)

    result = await store.delete("nonexistent_key")

    assert result is False


@pytest.mark.asyncio
async def test_store_multiple_keys(db_session: AsyncSession):
    """Test storing multiple keys independently."""
    store = PostgreSQLStore(namespace="test_123", db_session=db_session)

    # Put multiple keys
    await store.put("key1", b"Value 1")
    await store.put("key2", b"Value 2")
    await store.put("key3", b"Value 3")

    # Retrieve all
    val1 = await store.get("key1")
    val2 = await store.get("key2")
    val3 = await store.get("key3")

    assert val1 == b"Value 1"
    assert val2 == b"Value 2"
    assert val3 == b"Value 3"


@pytest.mark.asyncio
async def test_store_namespace_isolation(db_session: AsyncSession):
    """Test that different namespaces are isolated."""
    store1 = PostgreSQLStore(namespace="namespace_1", db_session=db_session)
    store2 = PostgreSQLStore(namespace="namespace_2", db_session=db_session)

    # Put same key in different namespaces
    await store1.put("shared_key", b"Value from namespace 1")
    await store2.put("shared_key", b"Value from namespace 2")

    # Retrieve from each namespace
    val1 = await store1.get("shared_key")
    val2 = await store2.get("shared_key")

    assert val1 == b"Value from namespace 1"
    assert val2 == b"Value from namespace 2"


@pytest.mark.asyncio
async def test_store_binary_data(db_session: AsyncSession):
    """Test storing binary data."""
    store = PostgreSQLStore(namespace="test_123", db_session=db_session)

    # Create binary data (e.g., image bytes)
    binary_data = bytes(range(256))

    await store.put("binary_key", binary_data)

    retrieved = await store.get("binary_key")

    assert retrieved == binary_data


@pytest.mark.asyncio
async def test_store_large_data(db_session: AsyncSession):
    """Test storing large data."""
    store = PostgreSQLStore(namespace="test_123", db_session=db_session)

    # Create large data (1 MB)
    large_data = b"X" * (1024 * 1024)

    await store.put("large_key", large_data)

    retrieved = await store.get("large_key")

    assert len(retrieved) == 1024 * 1024
    assert retrieved == large_data


# ============================================================================
# StoreManager Tests
# ============================================================================


@pytest.mark.asyncio
async def test_store_manager_get_store(store_manager: StoreManager, db_session: AsyncSession, test_namespace: AgentMemoryNamespace):
    """Test getting a store through StoreManager."""
    store = await store_manager.get_store(
        namespace=test_namespace.namespace,
        store_type="postgresql",
        db_session=db_session
    )

    assert store is not None
    assert isinstance(store, PostgreSQLStore)


@pytest.mark.asyncio
async def test_store_manager_caching(store_manager: StoreManager, db_session: AsyncSession, test_namespace: AgentMemoryNamespace):
    """Test that StoreManager caches store instances."""
    store1 = await store_manager.get_store(
        namespace=test_namespace.namespace,
        store_type="postgresql",
        db_session=db_session
    )

    store2 = await store_manager.get_store(
        namespace=test_namespace.namespace,
        store_type="postgresql",
        db_session=db_session
    )

    # Should return same instance (cached)
    assert store1 is store2


@pytest.mark.asyncio
async def test_store_manager_different_namespaces(store_manager: StoreManager, db_session: AsyncSession):
    """Test getting stores for different namespaces."""
    store1 = await store_manager.get_store(
        namespace="namespace_1",
        store_type="postgresql",
        db_session=db_session
    )

    store2 = await store_manager.get_store(
        namespace="namespace_2",
        store_type="postgresql",
        db_session=db_session
    )

    # Should be different instances
    assert store1 is not store2
    assert store1.namespace != store2.namespace


@pytest.mark.asyncio
async def test_store_manager_create_namespace(store_manager: StoreManager, db_session: AsyncSession):
    """Test creating a new namespace."""
    agent_id = 42

    namespace = await store_manager.create_namespace(
        agent_id=agent_id,
        db_session=db_session
    )

    assert namespace is not None
    assert namespace.startswith("agent_")
    assert str(agent_id) in namespace

    # Verify it was saved to database
    from sqlalchemy import select
    result = await db_session.execute(
        select(AgentMemoryNamespace).where(AgentMemoryNamespace.agent_id == agent_id)
    )
    db_namespace = result.scalar_one_or_none()

    assert db_namespace is not None
    assert db_namespace.namespace == namespace


@pytest.mark.asyncio
async def test_store_manager_create_namespace_duplicate(store_manager: StoreManager, db_session: AsyncSession):
    """Test that creating duplicate namespace is handled."""
    agent_id = 42

    # Create first namespace
    namespace1 = await store_manager.create_namespace(
        agent_id=agent_id,
        db_session=db_session
    )

    # Try to create again
    try:
        namespace2 = await store_manager.create_namespace(
            agent_id=agent_id,
            db_session=db_session
        )
        # If it doesn't raise, should return same namespace or different one
        assert namespace2 is not None
    except Exception as e:
        # Expected if duplicates not allowed
        assert "already exists" in str(e).lower() or "duplicate" in str(e).lower()


# ============================================================================
# Integration Tests with Models
# ============================================================================


@pytest.mark.asyncio
async def test_store_with_memory_files(db_session: AsyncSession, test_namespace: AgentMemoryNamespace):
    """Test store operations with AgentMemoryFile model."""
    store = PostgreSQLStore(namespace=test_namespace.namespace, db_session=db_session)

    # Store data
    await store.put("test.txt", b"Test content")

    # Verify it exists in database
    from sqlalchemy import select
    import base64
    result = await db_session.execute(
        select(AgentMemoryFile).where(
            AgentMemoryFile.namespace == test_namespace.namespace,
            AgentMemoryFile.key == "test.txt"
        )
    )
    file = result.scalar_one_or_none()

    assert file is not None
    # Value should be base64-encoded in database for SQLite compatibility
    assert file.value == base64.b64encode(b"Test content").decode('ascii')


@pytest.mark.asyncio
async def test_store_list_files(db_session: AsyncSession, test_namespace: AgentMemoryNamespace):
    """Test listing files in a namespace."""
    store = PostgreSQLStore(namespace=test_namespace.namespace, db_session=db_session)

    # Store multiple files
    await store.put("file1.txt", b"Content 1")
    await store.put("file2.txt", b"Content 2")
    await store.put("nested/file3.txt", b"Content 3")

    # Query files from database
    from sqlalchemy import select
    result = await db_session.execute(
        select(AgentMemoryFile).where(
            AgentMemoryFile.namespace == test_namespace.namespace
        )
    )
    files = result.scalars().all()

    assert len(files) == 3
    keys = [f.key for f in files]
    assert "file1.txt" in keys
    assert "file2.txt" in keys
    assert "nested/file3.txt" in keys


@pytest.mark.asyncio
async def test_store_delete_removes_from_database(db_session: AsyncSession, test_namespace: AgentMemoryNamespace):
    """Test that delete operation removes file from database."""
    store = PostgreSQLStore(namespace=test_namespace.namespace, db_session=db_session)

    # Store and delete
    await store.put("to_delete.txt", b"Delete me")
    await store.delete("to_delete.txt")

    # Verify removed from database
    from sqlalchemy import select
    result = await db_session.execute(
        select(AgentMemoryFile).where(
            AgentMemoryFile.namespace == test_namespace.namespace,
            AgentMemoryFile.key == "to_delete.txt"
        )
    )
    file = result.scalar_one_or_none()

    assert file is None


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.asyncio
async def test_store_empty_key(db_session: AsyncSession):
    """Test that empty key is handled."""
    store = PostgreSQLStore(namespace="test_123", db_session=db_session)

    try:
        await store.put("", b"Data")
        # If it doesn't raise, it should handle empty key
        result = await store.get("")
        assert result is not None
    except ValueError:
        # Expected if empty keys not allowed
        pass


@pytest.mark.asyncio
async def test_store_none_value(db_session: AsyncSession):
    """Test that None value is handled."""
    store = PostgreSQLStore(namespace="test_123", db_session=db_session)

    try:
        await store.put("test_key", None)
        # If it doesn't raise, verify behavior
        result = await store.get("test_key")
        assert result is None or result == b""
    except (ValueError, TypeError):
        # Expected if None values not allowed
        pass


@pytest.mark.asyncio
async def test_store_special_characters_in_key(db_session: AsyncSession):
    """Test handling special characters in keys."""
    store = PostgreSQLStore(namespace="test_123", db_session=db_session)

    special_keys = [
        "file with spaces.txt",
        "file/with/slashes.txt",
        "file-with-dashes.txt",
        "file_with_underscores.txt",
        "file.multiple.dots.txt"
    ]

    for key in special_keys:
        await store.put(key, b"Test data")
        retrieved = await store.get(key)
        assert retrieved == b"Test data", f"Failed for key: {key}"


@pytest.mark.asyncio
async def test_store_unicode_in_value(db_session: AsyncSession):
    """Test storing Unicode text as bytes."""
    store = PostgreSQLStore(namespace="test_123", db_session=db_session)

    # Unicode text
    unicode_text = "Hello 世界 🌍"
    unicode_bytes = unicode_text.encode("utf-8")

    await store.put("unicode_file.txt", unicode_bytes)

    retrieved = await store.get("unicode_file.txt")

    assert retrieved == unicode_bytes
    assert retrieved.decode("utf-8") == unicode_text


# ============================================================================
# Performance Tests
# ============================================================================


@pytest.mark.asyncio
async def test_store_many_small_files(db_session: AsyncSession):
    """Test storing many small files."""
    store = PostgreSQLStore(namespace="test_123", db_session=db_session)

    # Store 100 small files
    for i in range(100):
        await store.put(f"file_{i}.txt", f"Content {i}".encode())

    # Verify count
    from sqlalchemy import select, func
    result = await db_session.execute(
        select(func.count()).select_from(AgentMemoryFile).where(
            AgentMemoryFile.namespace == "test_123"
        )
    )
    count = result.scalar()

    assert count == 100


@pytest.mark.asyncio
async def test_store_concurrent_operations(db_session: AsyncSession):
    """Test concurrent read operations and sequential write operations.

    Note: SQLAlchemy sessions are not safe for concurrent write operations
    (multiple simultaneous commits on the same session). In production,
    each HTTP request gets its own database session, so concurrent requests
    naturally have separate sessions. This test verifies:
    1. Sequential writes work correctly
    2. Concurrent reads work correctly
    """
    import asyncio

    store = PostgreSQLStore(namespace="test_123", db_session=db_session)

    # Write operations sequentially (SQLAlchemy sessions require this)
    for i in range(10):
        await store.put(f"key_{i}", f"Value {i}".encode())

    # Test concurrent reads (safe because no commits involved)
    async def get_and_verify(key: str, expected: bytes):
        data = await store.get(key)
        assert data == expected

    # Run multiple concurrent read operations
    read_tasks = [
        get_and_verify(f"key_{i}", f"Value {i}".encode())
        for i in range(10)
    ]

    # Concurrent reads should work without issues
    await asyncio.gather(*read_tasks)

    # Verify all data one more time
    for i in range(10):
        data = await store.get(f"key_{i}")
        assert data == f"Value {i}".encode()
