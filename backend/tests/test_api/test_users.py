"""
Tests for User Management API endpoints.

Tests all user management REST API endpoints including:
- Getting user profile
- Updating user profile (email)
- Changing password
- Deleting user account
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from core.security import get_password_hash, create_access_token, verify_password
from datetime import timedelta


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user for API operations."""
    hashed_password = get_password_hash("TestPass123")
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hashed_password,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create authentication headers with valid JWT token."""
    token = create_access_token(
        data={"sub": test_user.username, "user_id": test_user.id},
        expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# GET /users/me - Get Profile Tests
# ============================================================================


def test_get_profile_success(client: TestClient, test_user: User, auth_headers: dict):
    """Test getting user profile successfully."""
    response = client.get(
        "/api/v1/users/me",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["is_active"] is True


def test_get_profile_without_auth(client_no_auth: TestClient):
    """Test that getting profile without auth fails."""
    response = client_no_auth.get("/api/v1/users/me")

    assert response.status_code == 403


# ============================================================================
# PUT /users/me - Update Profile Tests
# ============================================================================


def test_update_profile_email_success(client: TestClient, test_user: User, auth_headers: dict):
    """Test updating user email successfully."""
    response = client.put(
        "/api/v1/users/me",
        headers=auth_headers,
        json={"email": "newemail@example.com"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newemail@example.com"
    assert data["username"] == "testuser"  # Username unchanged


def test_update_profile_duplicate_email(client: TestClient, test_user: User, auth_headers: dict, db_session: AsyncSession):
    """Test that updating to existing email fails."""
    # Create another user
    hashed_password = get_password_hash("OtherPass123")
    other_user = User(
        username="otheruser",
        email="other@example.com",
        hashed_password=hashed_password,
        is_active=True,
    )
    db_session.add(other_user)

    import asyncio
    asyncio.get_event_loop().run_until_complete(db_session.commit())

    # Try to update to other user's email
    response = client.put(
        "/api/v1/users/me",
        headers=auth_headers,
        json={"email": "other@example.com"}
    )

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_update_profile_invalid_email(client: TestClient, auth_headers: dict):
    """Test that invalid email is rejected."""
    response = client.put(
        "/api/v1/users/me",
        headers=auth_headers,
        json={"email": "not-an-email"}
    )

    assert response.status_code == 422


# ============================================================================
# PUT /users/me/password - Change Password Tests
# ============================================================================


def test_change_password_success(client: TestClient, test_user: User, auth_headers: dict, db_session: AsyncSession):
    """Test changing password successfully."""
    response = client.put(
        "/api/v1/users/me/password",
        headers=auth_headers,
        json={
            "current_password": "TestPass123",
            "new_password": "NewSecure456",
            "confirm_password": "NewSecure456"
        }
    )

    assert response.status_code == 200

    # Verify new password works
    import asyncio
    asyncio.get_event_loop().run_until_complete(db_session.refresh(test_user))
    assert verify_password("NewSecure456", test_user.hashed_password)


def test_change_password_wrong_current(client: TestClient, auth_headers: dict):
    """Test that wrong current password is rejected."""
    response = client.put(
        "/api/v1/users/me/password",
        headers=auth_headers,
        json={
            "current_password": "WrongPass123",
            "new_password": "NewSecure456",
            "confirm_password": "NewSecure456"
        }
    )

    assert response.status_code == 400
    assert "Incorrect current password" in response.json()["detail"]


def test_change_password_mismatch(client: TestClient, auth_headers: dict):
    """Test that mismatched passwords are rejected."""
    response = client.put(
        "/api/v1/users/me/password",
        headers=auth_headers,
        json={
            "current_password": "TestPass123",
            "new_password": "NewSecure456",
            "confirm_password": "DifferentPass789"
        }
    )

    assert response.status_code == 400
    assert "do not match" in response.json()["detail"]


def test_change_password_same_as_current(client: TestClient, auth_headers: dict):
    """Test that using same password as current is rejected."""
    response = client.put(
        "/api/v1/users/me/password",
        headers=auth_headers,
        json={
            "current_password": "TestPass123",
            "new_password": "TestPass123",
            "confirm_password": "TestPass123"
        }
    )

    assert response.status_code == 400
    assert "different from current" in response.json()["detail"]


def test_change_password_weak_new_password(client: TestClient, auth_headers: dict):
    """Test that weak new password is rejected."""
    response = client.put(
        "/api/v1/users/me/password",
        headers=auth_headers,
        json={
            "current_password": "TestPass123",
            "new_password": "weak",
            "confirm_password": "weak"
        }
    )

    assert response.status_code == 422


# ============================================================================
# DELETE /users/me - Delete Account Tests
# ============================================================================


def test_delete_account_success(client: TestClient, test_user: User, auth_headers: dict, db_session: AsyncSession):
    """Test deleting user account successfully (soft delete)."""
    response = client.delete(
        "/api/v1/users/me",
        headers=auth_headers
    )

    assert response.status_code == 204

    # Verify user is deactivated
    import asyncio
    asyncio.get_event_loop().run_until_complete(db_session.refresh(test_user))
    assert test_user.is_active is False


def test_delete_account_without_auth(client_no_auth: TestClient):
    """Test that deleting account without auth fails."""
    response = client_no_auth.delete("/api/v1/users/me")

    assert response.status_code == 403
