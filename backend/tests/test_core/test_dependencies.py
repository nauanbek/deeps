"""
Tests for core dependencies (JWT middleware).

Tests authentication dependencies: get_current_user, get_current_active_user,
and get_optional_user functionality.
"""

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from core.dependencies import get_current_user, get_current_active_user, get_optional_user
from core.security import create_access_token, get_password_hash
from datetime import timedelta


# ============================================================================
# get_current_user Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_current_user_success(db_session: AsyncSession):
    """Test successful user extraction from valid JWT token."""
    # Create test user
    hashed_password = get_password_hash("TestPass123")
    user = User(
        username="jwtuser",
        email="jwt@example.com",
        hashed_password=hashed_password,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create valid token
    token = create_access_token(
        data={"sub": "jwtuser", "user_id": user.id},
        expires_delta=timedelta(minutes=30)
    )

    # Mock credentials
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    # Get current user
    current_user = await get_current_user(credentials=credentials, db=db_session)

    assert current_user is not None
    assert current_user.username == "jwtuser"
    assert current_user.email == "jwt@example.com"
    assert current_user.is_active is True


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(db_session: AsyncSession):
    """Test that invalid token raises 401 error."""
    # Create invalid token
    invalid_token = "invalid.token.here"
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=invalid_token)

    # Should raise 401 error
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=credentials, db=db_session)

    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_user_expired_token(db_session: AsyncSession):
    """Test that expired token raises 401 error."""
    # Create expired token (negative expiry)
    token = create_access_token(
        data={"sub": "expireduser", "user_id": 1},
        expires_delta=timedelta(minutes=-30)
    )
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    # Should raise 401 error
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=credentials, db=db_session)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_nonexistent_user(db_session: AsyncSession):
    """Test that token with non-existent user raises 401 error."""
    # Create token for non-existent user
    token = create_access_token(
        data={"sub": "nonexistent", "user_id": 99999},
        expires_delta=timedelta(minutes=30)
    )
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    # Should raise 401 error
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=credentials, db=db_session)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_missing_subject(db_session: AsyncSession):
    """Test that token without 'sub' claim raises 401 error."""
    # Create token without 'sub' claim
    token = create_access_token(
        data={"user_id": 1},  # Missing 'sub'
        expires_delta=timedelta(minutes=30)
    )
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    # Should raise 401 error
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=credentials, db=db_session)

    assert exc_info.value.status_code == 401


# ============================================================================
# get_current_active_user Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_current_active_user_success():
    """Test that active user passes through successfully."""
    # Create active user
    user = User(
        id=1,
        username="activeuser",
        email="active@example.com",
        hashed_password="hashed",
        is_active=True
    )

    # Should return user
    result = await get_current_active_user(current_user=user)

    assert result == user


@pytest.mark.asyncio
async def test_get_current_active_user_inactive_fails():
    """Test that inactive user raises 400 error."""
    # Create inactive user
    user = User(
        id=1,
        username="inactiveuser",
        email="inactive@example.com",
        hashed_password="hashed",
        is_active=False
    )

    # Should raise 400 error
    with pytest.raises(HTTPException) as exc_info:
        await get_current_active_user(current_user=user)

    assert exc_info.value.status_code == 400
    assert "Inactive user" in str(exc_info.value.detail)


# ============================================================================
# get_optional_user Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_optional_user_with_valid_token(db_session: AsyncSession):
    """Test optional user extraction with valid token."""
    # Create test user
    hashed_password = get_password_hash("TestPass123")
    user = User(
        username="optionaluser",
        email="optional@example.com",
        hashed_password=hashed_password,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create valid token
    token = create_access_token(
        data={"sub": "optionaluser", "user_id": user.id},
        expires_delta=timedelta(minutes=30)
    )
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    # Get optional user
    current_user = await get_optional_user(credentials=credentials, db=db_session)

    assert current_user is not None
    assert current_user.username == "optionaluser"


@pytest.mark.asyncio
async def test_get_optional_user_with_no_token(db_session: AsyncSession):
    """Test optional user extraction without token returns None."""
    # Get optional user without credentials
    current_user = await get_optional_user(credentials=None, db=db_session)

    assert current_user is None


@pytest.mark.asyncio
async def test_get_optional_user_with_invalid_token(db_session: AsyncSession):
    """Test optional user extraction with invalid token returns None."""
    # Create invalid token
    invalid_token = "invalid.token.here"
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=invalid_token)

    # Get optional user - should return None instead of raising error
    current_user = await get_optional_user(credentials=credentials, db=db_session)

    assert current_user is None
