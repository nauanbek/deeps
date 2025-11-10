"""
User management API endpoints.

This module provides endpoints for:
- User profile management
- Password changes
- User account settings
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_active_user
from core.security import verify_password
from models.user import User
from schemas.auth import (
    UserResponse,
    UserUpdate,
    PasswordChange,
)
from services.auth_service import AuthService


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get current user profile.

    Args:
        current_user: Current authenticated user

    Returns:
        User profile information
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update current user profile.

    Args:
        user_update: Updated user data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user profile

    Raises:
        HTTPException: 400 if email already exists
    """
    try:
        if user_update.email is not None:
            updated_user = await AuthService.update_user_email(
                db, current_user, user_update.email
            )
            return updated_user
        return current_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/me/password", response_model=UserResponse)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change current user password.

    Args:
        password_data: Current and new password
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user profile

    Raises:
        HTTPException: 400 if current password is incorrect or passwords don't match
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )

    # Check if new passwords match
    if not password_data.passwords_match():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match"
        )

    # Check if new password is different from current
    if password_data.new_password == password_data.current_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )

    # Update password
    updated_user = await AuthService.update_user_password(
        db, current_user, password_data.new_password
    )

    return updated_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_my_account(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Deactivate current user account (soft delete).

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        No content (204)
    """
    await AuthService.deactivate_user(db, current_user)
    return None
