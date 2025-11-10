"""
Tests for Auth service layer.

Tests user authentication, registration, password management,
and user account operations.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from schemas.auth import UserRegister, PasswordChange
from services.auth_service import AuthService
from core.security import get_password_hash, verify_password


# ============================================================================
# Get User Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_user_by_username_success(db_session: AsyncSession):
    """Test retrieving user by username."""
    # Create test user
    hashed_password = get_password_hash("TestPass123")
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hashed_password,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Retrieve user
    retrieved_user = await AuthService.get_user_by_username(db_session, "testuser")

    assert retrieved_user is not None
    assert retrieved_user.username == "testuser"
    assert retrieved_user.email == "test@example.com"
    assert retrieved_user.is_active is True


@pytest.mark.asyncio
async def test_get_user_by_username_not_found(db_session: AsyncSession):
    """Test retrieving non-existent user by username."""
    user = await AuthService.get_user_by_username(db_session, "nonexistent")
    assert user is None


@pytest.mark.asyncio
async def test_get_user_by_email_success(db_session: AsyncSession):
    """Test retrieving user by email."""
    # Create test user
    hashed_password = get_password_hash("TestPass123")
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hashed_password,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Retrieve user
    retrieved_user = await AuthService.get_user_by_email(db_session, "test@example.com")

    assert retrieved_user is not None
    assert retrieved_user.username == "testuser"
    assert retrieved_user.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(db_session: AsyncSession):
    """Test retrieving non-existent user by email."""
    user = await AuthService.get_user_by_email(db_session, "nonexistent@example.com")
    assert user is None


@pytest.mark.asyncio
async def test_get_user_by_id_success(db_session: AsyncSession):
    """Test retrieving user by ID."""
    # Create test user
    hashed_password = get_password_hash("TestPass123")
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hashed_password,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Retrieve user
    retrieved_user = await AuthService.get_user_by_id(db_session, user.id)

    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.username == "testuser"


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(db_session: AsyncSession):
    """Test retrieving non-existent user by ID."""
    user = await AuthService.get_user_by_id(db_session, 99999)
    assert user is None


# ============================================================================
# Create User Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_user_success(db_session: AsyncSession):
    """Test creating a new user successfully."""
    user_data = UserRegister(
        username="newuser",
        email="new@example.com",
        password="SecurePass123"
    )

    user = await AuthService.create_user(db_session, user_data)

    assert user.id is not None
    assert user.username == "newuser"
    assert user.email == "new@example.com"
    assert user.is_active is True
    assert verify_password("SecurePass123", user.hashed_password)


@pytest.mark.asyncio
async def test_create_user_duplicate_username_fails(db_session: AsyncSession):
    """Test that duplicate usernames are rejected."""
    user_data1 = UserRegister(
        username="testuser",
        email="test1@example.com",
        password="Password123"
    )
    user_data2 = UserRegister(
        username="testuser",
        email="test2@example.com",
        password="Password123"
    )

    # Create first user
    await AuthService.create_user(db_session, user_data1)

    # Attempt to create duplicate username should fail
    with pytest.raises(ValueError, match="Username already registered"):
        await AuthService.create_user(db_session, user_data2)


@pytest.mark.asyncio
async def test_create_user_duplicate_email_fails(db_session: AsyncSession):
    """Test that duplicate emails are rejected."""
    user_data1 = UserRegister(
        username="user1",
        email="test@example.com",
        password="Password123"
    )
    user_data2 = UserRegister(
        username="user2",
        email="test@example.com",
        password="Password123"
    )

    # Create first user
    await AuthService.create_user(db_session, user_data1)

    # Attempt to create duplicate email should fail
    with pytest.raises(ValueError, match="Email already registered"):
        await AuthService.create_user(db_session, user_data2)


# ============================================================================
# Authenticate User Tests
# ============================================================================


@pytest.mark.asyncio
async def test_authenticate_user_success(db_session: AsyncSession, clean_redis):
    """Test successful user authentication."""
    # Create test user
    user_data = UserRegister(
        username="authuser",
        email="auth@example.com",
        password="AuthPass123"
    )
    await AuthService.create_user(db_session, user_data)

    # Authenticate
    authenticated_user = await AuthService.authenticate_user(
        db_session, "authuser", "AuthPass123"
    )

    assert authenticated_user is not None
    assert authenticated_user.username == "authuser"


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(db_session: AsyncSession, clean_redis):
    """Test authentication with wrong password."""
    # Create test user
    user_data = UserRegister(
        username="authuser",
        email="auth@example.com",
        password="CorrectPass123"
    )
    await AuthService.create_user(db_session, user_data)

    # Authenticate with wrong password
    authenticated_user = await AuthService.authenticate_user(
        db_session, "authuser", "WrongPass123"
    )

    assert authenticated_user is None


@pytest.mark.asyncio
async def test_authenticate_user_nonexistent(db_session: AsyncSession, clean_redis):
    """Test authentication for non-existent user."""
    authenticated_user = await AuthService.authenticate_user(
        db_session, "nonexistent", "AnyPass123"
    )

    assert authenticated_user is None


@pytest.mark.asyncio
async def test_authenticate_user_account_lockout(db_session: AsyncSession, clean_redis):
    """Test that account gets locked after multiple failed login attempts."""
    # Create test user
    user_data = UserRegister(
        username="lockoutuser",
        email="lockout@example.com",
        password="CorrectPass123"
    )
    await AuthService.create_user(db_session, user_data)

    # First 4 attempts should return None (authentication failed)
    for i in range(4):
        authenticated_user = await AuthService.authenticate_user(
            db_session, "lockoutuser", "WrongPass123"
        )
        assert authenticated_user is None

    # 5th attempt should raise ValueError (account locked at threshold)
    with pytest.raises(ValueError, match="Account has been locked"):
        await AuthService.authenticate_user(
            db_session, "lockoutuser", "WrongPass123"
        )

    # Even with correct password, account should be locked
    with pytest.raises(ValueError, match="Account is temporarily locked"):
        await AuthService.authenticate_user(
            db_session, "lockoutuser", "CorrectPass123"
        )


# ============================================================================
# Update Password Tests
# ============================================================================


@pytest.mark.asyncio
async def test_update_user_password_success(db_session: AsyncSession):
    """Test updating user password."""
    # Create test user
    user_data = UserRegister(
        username="passuser",
        email="pass@example.com",
        password="OldPass123"
    )
    user = await AuthService.create_user(db_session, user_data)

    # Update password
    updated_user = await AuthService.update_user_password(
        db_session, user, "NewPass456"
    )

    assert updated_user is not None
    assert verify_password("NewPass456", updated_user.hashed_password)
    # Old password should not work
    assert not verify_password("OldPass123", updated_user.hashed_password)


# ============================================================================
# Update Email Tests
# ============================================================================


@pytest.mark.asyncio
async def test_update_user_email_success(db_session: AsyncSession):
    """Test updating user email."""
    # Create test user
    user_data = UserRegister(
        username="emailuser",
        email="old@example.com",
        password="Pass1234"
    )
    user = await AuthService.create_user(db_session, user_data)

    # Update email
    updated_user = await AuthService.update_user_email(
        db_session, user, "new@example.com"
    )

    assert updated_user is not None
    assert updated_user.email == "new@example.com"


@pytest.mark.asyncio
async def test_update_user_email_duplicate_fails(db_session: AsyncSession):
    """Test that duplicate email update is rejected."""
    # Create two users
    user_data1 = UserRegister(
        username="user1",
        email="user1@example.com",
        password="Pass1234"
    )
    user_data2 = UserRegister(
        username="user2",
        email="user2@example.com",
        password="Pass1234"
    )
    user1 = await AuthService.create_user(db_session, user_data1)
    await AuthService.create_user(db_session, user_data2)

    # Attempt to update user1's email to user2's email
    with pytest.raises(ValueError, match="Email already registered"):
        await AuthService.update_user_email(db_session, user1, "user2@example.com")


# ============================================================================
# Deactivate/Activate User Tests
# ============================================================================


@pytest.mark.asyncio
async def test_deactivate_user(db_session: AsyncSession):
    """Test deactivating a user account."""
    # Create test user
    user_data = UserRegister(
        username="activeuser",
        email="active@example.com",
        password="Pass1234"
    )
    user = await AuthService.create_user(db_session, user_data)
    assert user.is_active is True

    # Deactivate
    updated_user = await AuthService.deactivate_user(db_session, user)

    assert updated_user.is_active is False


@pytest.mark.asyncio
async def test_activate_user(db_session: AsyncSession):
    """Test activating a user account."""
    # Create test user
    user_data = UserRegister(
        username="inactiveuser",
        email="inactive@example.com",
        password="Pass1234"
    )
    user = await AuthService.create_user(db_session, user_data)

    # Deactivate first
    user = await AuthService.deactivate_user(db_session, user)
    assert user.is_active is False

    # Activate
    updated_user = await AuthService.activate_user(db_session, user)

    assert updated_user.is_active is True
