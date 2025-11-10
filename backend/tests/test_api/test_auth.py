"""
Tests for Authentication API endpoints.

Tests all auth REST API endpoints including:
- User registration
- User login
- Getting current user info
- User logout
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from core.security import get_password_hash, create_access_token
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
# POST /auth/register - Register Tests
# ============================================================================


def test_register_success(client: TestClient):
    """Test successful user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "SecurePass123"
        }
    )

    assert response.status_code == 201
    data = response.json()
    # Register endpoint now returns a Token instead of User
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "hashed_password" not in data
    assert "password" not in data


def test_register_duplicate_username(client: TestClient, test_user: User):
    """Test that duplicate username is rejected."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",  # Same as test_user
            "email": "different@example.com",
            "password": "AnyPass123"
        }
    )

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_register_duplicate_email(client: TestClient, test_user: User):
    """Test that duplicate email is rejected."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "differentuser",
            "email": "test@example.com",  # Same as test_user
            "password": "AnyPass123"
        }
    )

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_register_invalid_username(client: TestClient):
    """Test that invalid username is rejected."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "ab",  # Too short (min 3 chars)
            "email": "test@example.com",
            "password": "ValidPass123"
        }
    )

    assert response.status_code == 422


def test_register_invalid_email(client: TestClient):
    """Test that invalid email is rejected."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "validuser",
            "email": "not-an-email",  # Invalid email format
            "password": "ValidPass123"
        }
    )

    assert response.status_code == 422


def test_register_weak_password(client: TestClient):
    """Test that weak password is rejected."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "validuser",
            "email": "valid@example.com",
            "password": "weak"  # Too short, no number
        }
    )

    assert response.status_code == 422


def test_register_username_with_special_chars(client: TestClient):
    """Test that username with special characters is rejected."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "user@name",  # Contains @ (not allowed)
            "email": "test@example.com",
            "password": "ValidPass123"
        }
    )

    assert response.status_code == 422


# ============================================================================
# POST /auth/login - Login Tests
# ============================================================================


def test_login_success(client: TestClient, test_user: User):
    """Test successful user login."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "TestPass123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


def test_login_wrong_password(client: TestClient, test_user: User):
    """Test login with wrong password."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "WrongPass123"
        }
    )

    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_login_nonexistent_user(client: TestClient):
    """Test login with non-existent username."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "nonexistent",
            "password": "AnyPass123"
        }
    )

    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_login_inactive_user(client: TestClient, db_session: AsyncSession):
    """Test that inactive user cannot login."""
    # Create inactive user
    hashed_password = get_password_hash("InactivePass123")
    inactive_user = User(
        username="inactiveuser",
        email="inactive@example.com",
        hashed_password=hashed_password,
        is_active=False
    )
    db_session.add(inactive_user)

    import asyncio
    asyncio.get_event_loop().run_until_complete(db_session.commit())

    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "inactiveuser",
            "password": "InactivePass123"
        }
    )

    assert response.status_code == 400
    assert "Inactive user" in response.json()["detail"]


# ============================================================================
# GET /auth/me - Get Current User Tests
# ============================================================================


def test_get_current_user_success(client: TestClient, test_user: User, auth_headers: dict):
    """Test getting current user info with valid token."""
    response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["is_active"] is True
    assert "hashed_password" not in data


def test_get_current_user_without_token(client_no_auth: TestClient):
    """Test that accessing /me without token fails."""
    response = client_no_auth.get("/api/v1/auth/me")

    assert response.status_code == 403  # No auth header


def test_get_current_user_invalid_token(client_no_auth: TestClient):
    """Test that invalid token is rejected."""
    response = client_no_auth.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"}
    )

    assert response.status_code == 401


def test_get_current_user_expired_token(client_no_auth: TestClient, test_user: User):
    """Test that expired token is rejected."""
    # Create expired token
    expired_token = create_access_token(
        data={"sub": test_user.username, "user_id": test_user.id},
        expires_delta=timedelta(minutes=-30)  # Expired 30 minutes ago
    )

    response = client_no_auth.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )

    assert response.status_code == 401


# ============================================================================
# POST /auth/logout - Logout Tests
# ============================================================================


def test_logout_success(client: TestClient, auth_headers: dict):
    """Test successful logout."""
    response = client.post(
        "/api/v1/auth/logout",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_logout_without_token(client: TestClient):
    """Test that logout without token returns success (client-side operation)."""
    response = client.post("/api/v1/auth/logout")

    # Should still succeed since JWT is stateless
    assert response.status_code == 200
