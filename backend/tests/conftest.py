"""
Pytest configuration and shared fixtures for backend tests.

Provides:
- FastAPI test client
- Async database session for testing
- Override settings for test environment
"""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
import redis.asyncio as redis_async

from core.database import Base, get_db
from core.config import settings
from models.agent import Agent


# Test database URL (use in-memory SQLite for fast tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

# Create test session factory
TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create an event loop for the test session.

    Yields:
        Event loop for async tests
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session with automatic rollback.

    Creates all tables before each test and drops them after.
    All changes are rolled back to ensure test isolation.

    Yields:
        AsyncSession: Test database session
    """
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()

    # Drop all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> "User":
    """
    Create a test user for authentication.

    Args:
        db_session: Test database session

    Returns:
        User: Test user
    """
    from models.user import User

    user = User(
        username="testuser",
        email="testuser@example.com",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def client(db_session: AsyncSession, test_user: "User") -> Generator:
    """
    Create a FastAPI test client with dependency overrides.

    Overrides the database dependency to use the test database session.
    Also overrides authentication to automatically return test_user.

    Args:
        db_session: Test database session fixture
        test_user: Test user fixture

    Yields:
        TestClient: FastAPI test client with auth override
    """
    # Import app here to avoid circular imports
    from main import app
    from core.dependencies import get_current_active_user

    # Override database dependency
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    # Override authentication to return test user
    async def override_get_current_active_user() -> "User":
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user

    with TestClient(app) as test_client:
        yield test_client

    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_no_auth(db_session: AsyncSession) -> Generator:
    """
    Create a FastAPI test client WITHOUT authentication override.

    Only overrides the database dependency. Use this for testing
    authentication/authorization logic.

    Args:
        db_session: Test database session fixture

    Yields:
        TestClient: FastAPI test client without auth override
    """
    # Import app here to avoid circular imports
    from main import app

    # Override database dependency only
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_settings() -> dict:
    """
    Provide test settings that override default configuration.

    Returns:
        dict: Test configuration values
    """
    return {
        "DATABASE_URL": TEST_DATABASE_URL,
        "SECRET_KEY": "test-secret-key-for-testing-only",
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
        "CORS_ORIGINS_STR": "http://localhost:3000,http://testserver",
        "ENVIRONMENT": "testing",
    }


@pytest.fixture(autouse=True)
def setup_test_env(test_settings: dict) -> Generator:
    """
    Automatically set up test environment variables for all tests.

    Args:
        test_settings: Test configuration fixture

    Yields:
        None
    """
    # Store original env vars
    original_env = {}

    # Set test env vars
    for key, value in test_settings.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = str(value)

    yield

    # Restore original env vars
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture
def test_user_id() -> int:
    """
    Provide a test user ID for creating test data.

    Returns:
        int: Test user ID
    """
    return 1


@pytest.fixture
async def test_agent(db_session: AsyncSession, test_user_id: int) -> Agent:
    """
    Create a test agent for use in tests.

    Args:
        db_session: Test database session
        test_user_id: Test user ID

    Returns:
        Agent: Created test agent
    """
    agent = Agent(
        name="Test Agent",
        description="A test agent for unit testing",
        model_provider="openai",
        model_name="gpt-4",
        system_prompt="You are a helpful test assistant",
        temperature=0.7,
        max_tokens=1000,
        created_by_id=test_user_id,
        is_active=True
    )

    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)

    return agent


@pytest.fixture(scope="function")
async def clean_redis() -> AsyncGenerator[None, None]:
    """
    Clean Redis before each test to ensure test isolation.

    This fixture clears all lockout-related data from Redis before each test,
    preventing state from one test affecting another. This is particularly
    important for authentication tests that use the lockout service.

    Yields:
        None
    """
    try:
        # Connect to Redis
        redis_client = redis_async.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2,
        )

        # Clear all lockout-related keys
        # Use pattern matching to delete only lockout keys to avoid affecting other tests
        lockout_keys = []
        async for key in redis_client.scan_iter(match="login_attempts:*"):
            lockout_keys.append(key)
        async for key in redis_client.scan_iter(match="account_locked:*"):
            lockout_keys.append(key)

        if lockout_keys:
            await redis_client.delete(*lockout_keys)

        await redis_client.close()

    except Exception as e:
        # If Redis is unavailable, skip cleanup (tests will work without Redis)
        pass

    yield
