"""
Authentication API endpoints.

This module provides endpoints for:
- User registration
- User login (JWT token generation)
- Current user information
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.database import get_db
from core.dependencies import get_current_active_user, get_current_admin_user
from core.security import create_access_token
from models.user import User
from schemas.auth import (
    Token,
    UserLogin,
    UserRegister,
    UserResponse,
)
from services.auth_service import AuthService
from services.lockout_service import get_lockout_service
from core.password_validator import calculate_password_strength
from pydantic import BaseModel


router = APIRouter(prefix="/auth", tags=["authentication"])
settings = get_settings()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user and automatically log them in.

    Args:
        user_data: User registration data (username, email, password)
        db: Database session

    Returns:
        JWT access token (user is automatically logged in after registration)

    Raises:
        HTTPException: 400 if username or email already exists
    """
    try:
        user = await AuthService.create_user(db, user_data)

        # Auto-login: Generate JWT token for the newly registered user
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id},
            expires_delta=access_token_expires
        )

        return {"access_token": access_token, "token_type": "bearer"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """
    Login and get JWT access token.

    Includes account lockout protection:
    - Returns 429 if account is locked
    - Returns 401 if credentials are invalid

    Args:
        credentials: Username and password
        db: Database session

    Returns:
        JWT access token

    Raises:
        HTTPException: 401 if credentials are invalid
        HTTPException: 429 if account is locked
    """
    try:
        user = await AuthService.authenticate_user(
            db, credentials.username, credentials.password
        )
    except ValueError as e:
        # Account is locked
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
            headers={"Retry-After": "900"},  # 15 minutes in seconds
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    # Create JWT token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user from JWT token

    Returns:
        Current user information
    """
    return current_user


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: User = Depends(get_current_active_user),
):
    """
    Logout (placeholder endpoint for client-side token removal).

    Note: JWT tokens are stateless, so logout is handled client-side
    by removing the token. This endpoint exists for API consistency.

    Args:
        current_user: Current authenticated user

    Returns:
        Success message
    """
    return {"message": "Successfully logged out"}


@router.get("/lockout-status/{username}", status_code=status.HTTP_200_OK)
async def get_lockout_status(
    username: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get account lockout status for a user.

    Returns detailed information about failed login attempts and lockout state.
    Requires authentication.

    Args:
        username: Username to check lockout status for
        current_user: Current authenticated user (admin access recommended)

    Returns:
        Dictionary with:
            - locked (bool): Whether account is currently locked
            - failed_attempts (int): Number of failed attempts in current window
            - remaining_attempts (int): Attempts until lockout
            - unlocks_in_seconds (int): Seconds until automatic unlock (0 if not locked)
            - max_attempts (int): Maximum allowed failed attempts
    """
    lockout_service = get_lockout_service()
    status_info = await lockout_service.get_lockout_status(username)
    return status_info


@router.post("/unlock-account/{username}", status_code=status.HTTP_200_OK)
async def unlock_account(
    username: str,
    current_user: User = Depends(get_current_admin_user),
):
    """
    Manually unlock a locked account (admin-only function).

    Clears both the lockout flag and failed attempts counter.
    **Requires admin privileges.** Non-admin users will receive 403 Forbidden.

    Args:
        username: Username to unlock
        current_user: Current authenticated admin user

    Returns:
        Success message indicating if account was unlocked

    Raises:
        HTTPException: 403 if user is not an admin

    Example:
        POST /api/v1/auth/unlock-account/johndoe
        Response: {"message": "Account 'johndoe' has been unlocked", "was_locked": true}
    """
    lockout_service = get_lockout_service()
    was_locked = await lockout_service.unlock_account(username)

    if was_locked:
        return {
            "message": f"Account '{username}' has been unlocked",
            "was_locked": True
        }
    else:
        return {
            "message": f"Account '{username}' was not locked",
            "was_locked": False
        }


# ============================================================================
# Password Strength Check
# ============================================================================


class PasswordStrengthRequest(BaseModel):
    """Request model for password strength check."""
    password: str


@router.post("/check-password-strength", status_code=status.HTTP_200_OK)
async def check_password_strength(request: PasswordStrengthRequest):
    """
    Check password strength and get improvement suggestions.

    This endpoint does NOT require authentication and can be called
    during registration or password change to provide real-time feedback.

    Args:
        request: Password strength check request

    Returns:
        Dictionary with:
            - strength (str): Strength level (very_weak, weak, medium, strong, very_strong)
            - score (int): Numeric strength score (0-120+)
            - suggestions (list): List of improvement suggestions

    Example:
        POST /api/v1/auth/check-password-strength
        Body: {"password": "MyP@ssw0rd!"}
        Response: {
            "strength": "strong",
            "score": 75,
            "suggestions": ["Use at least 12 characters for better security"]
        }
    """
    result = calculate_password_strength(request.password)
    return result
