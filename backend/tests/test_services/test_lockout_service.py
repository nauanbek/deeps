"""
Tests for account lockout service.

Comprehensive test coverage for brute force protection:
- Failed login attempt tracking
- Account locking after threshold
- Automatic unlock after timeout
- Manual unlock (admin function)
- Lockout status checking
"""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from services.lockout_service import LockoutService, get_lockout_service


@pytest.mark.asyncio
class TestLockoutService:
    """Test suite for LockoutService."""

    @pytest.fixture
    async def lockout_service(self, fake_redis):
        """Create a fresh lockout service instance for each test."""
        service = LockoutService()
        # Inject fake Redis client for testing
        service._redis = fake_redis
        yield service
        # No need to close fake_redis here, the fixture handles it

    async def test_is_locked_returns_false_for_unlocked_account(self, lockout_service: LockoutService):
        """Test that is_locked returns False for an account that is not locked."""
        is_locked = await lockout_service.is_locked("testuser")
        assert is_locked is False

    async def test_record_failed_attempt_increments_counter(self, lockout_service: LockoutService):
        """Test that failed login attempts are tracked correctly."""
        # First attempt
        result = await lockout_service.record_failed_attempt("testuser")
        assert result["locked"] is False
        assert result["attempts"] == 1
        assert result["remaining_attempts"] == 4

        # Second attempt
        result = await lockout_service.record_failed_attempt("testuser")
        assert result["locked"] is False
        assert result["attempts"] == 2
        assert result["remaining_attempts"] == 3

    async def test_account_locks_after_max_attempts(self, lockout_service: LockoutService):
        """Test that account locks after reaching max failed attempts (5)."""
        username = "brute_force_user"

        # Attempt 4 failed logins (should not lock)
        for i in range(4):
            result = await lockout_service.record_failed_attempt(username)
            assert result["locked"] is False
            assert result["attempts"] == i + 1

        # 5th attempt should trigger lockout
        result = await lockout_service.record_failed_attempt(username)
        assert result["locked"] is True
        assert result["attempts"] == 5
        assert result["remaining_attempts"] == 0
        assert result["lockout_duration"] == 900  # 15 minutes in seconds

        # Verify account is locked
        is_locked = await lockout_service.is_locked(username)
        assert is_locked is True

    async def test_is_locked_returns_true_for_locked_account(self, lockout_service: LockoutService):
        """Test that is_locked correctly identifies locked accounts."""
        username = "locked_user"

        # Lock the account
        for _ in range(5):
            await lockout_service.record_failed_attempt(username)

        is_locked = await lockout_service.is_locked(username)
        assert is_locked is True

    async def test_get_remaining_lockout_time(self, lockout_service: LockoutService):
        """Test that remaining lockout time is calculated correctly."""
        username = "locked_time_user"

        # Lock the account
        for _ in range(5):
            await lockout_service.record_failed_attempt(username)

        remaining_time = await lockout_service.get_remaining_lockout_time(username)
        assert remaining_time is not None
        assert remaining_time > 0
        assert remaining_time <= 900  # Should be <= 15 minutes

    async def test_get_remaining_lockout_time_returns_none_for_unlocked(
        self, lockout_service: LockoutService
    ):
        """Test that remaining time is None for unlocked accounts."""
        remaining_time = await lockout_service.get_remaining_lockout_time("unlocked_user")
        assert remaining_time is None

    async def test_record_successful_login_clears_failed_attempts(
        self, lockout_service: LockoutService
    ):
        """Test that successful login clears failed attempt counter."""
        username = "success_user"

        # Record 3 failed attempts
        for _ in range(3):
            await lockout_service.record_failed_attempt(username)

        # Successful login should clear attempts
        await lockout_service.record_successful_login(username)

        # New failed attempt should start at 1, not 4
        result = await lockout_service.record_failed_attempt(username)
        assert result["attempts"] == 1
        assert result["remaining_attempts"] == 4

    async def test_unlock_account_manually(self, lockout_service: LockoutService):
        """Test manual account unlock (admin function)."""
        username = "admin_unlock_user"

        # Lock the account
        for _ in range(5):
            await lockout_service.record_failed_attempt(username)

        # Verify locked
        assert await lockout_service.is_locked(username) is True

        # Manually unlock
        was_locked = await lockout_service.unlock_account(username)
        assert was_locked is True

        # Verify unlocked
        assert await lockout_service.is_locked(username) is False

    async def test_unlock_account_returns_false_if_not_locked(
        self, lockout_service: LockoutService
    ):
        """Test that unlock returns False for accounts that weren't locked."""
        was_locked = await lockout_service.unlock_account("never_locked_user")
        assert was_locked is False

    async def test_get_lockout_status_for_unlocked_account(
        self, lockout_service: LockoutService
    ):
        """Test lockout status for an account with no failed attempts."""
        status = await lockout_service.get_lockout_status("clean_user")

        assert status["locked"] is False
        assert status["failed_attempts"] == 0
        assert status["remaining_attempts"] == 5
        assert status["unlocks_in_seconds"] == 0
        assert status["max_attempts"] == 5

    async def test_get_lockout_status_with_failed_attempts(
        self, lockout_service: LockoutService
    ):
        """Test lockout status for account with failed attempts but not locked."""
        username = "partial_fail_user"

        # Record 2 failed attempts
        await lockout_service.record_failed_attempt(username)
        await lockout_service.record_failed_attempt(username)

        status = await lockout_service.get_lockout_status(username)

        assert status["locked"] is False
        assert status["failed_attempts"] == 2
        assert status["remaining_attempts"] == 3
        assert status["max_attempts"] == 5

    async def test_get_lockout_status_for_locked_account(
        self, lockout_service: LockoutService
    ):
        """Test lockout status for a locked account."""
        username = "locked_status_user"

        # Lock the account
        for _ in range(5):
            await lockout_service.record_failed_attempt(username)

        status = await lockout_service.get_lockout_status(username)

        assert status["locked"] is True
        assert status["failed_attempts"] == 0  # Counter resets after lock
        assert status["remaining_attempts"] == 0
        assert status["unlocks_in_seconds"] > 0
        assert status["max_attempts"] == 5

    async def test_failed_attempts_expire_after_window(
        self, lockout_service: LockoutService
    ):
        """Test that failed attempts expire after the lockout window (10 minutes).

        Note: This test uses a mock to speed up testing rather than waiting 10 minutes.
        """
        username = "expiry_test_user"

        # Record 2 failed attempts
        await lockout_service.record_failed_attempt(username)
        await lockout_service.record_failed_attempt(username)

        # Mock Redis TTL expiration by manually deleting the key
        redis_client = await lockout_service._get_redis()
        attempt_key = lockout_service._attempt_key(username)
        await redis_client.delete(attempt_key)

        # Next attempt should start fresh at 1, not 3
        result = await lockout_service.record_failed_attempt(username)
        assert result["attempts"] == 1
        assert result["remaining_attempts"] == 4

    async def test_lockout_prevents_even_correct_password(
        self, lockout_service: LockoutService
    ):
        """Test that locked accounts cannot login even with correct password."""
        username = "correct_pass_locked"

        # Lock the account
        for _ in range(5):
            await lockout_service.record_failed_attempt(username)

        # Verify locked
        is_locked = await lockout_service.is_locked(username)
        assert is_locked is True

        # Even correct password attempt should be blocked by is_locked check
        # (This would be handled in auth_service.authenticate_user)

    async def test_concurrent_failed_attempts(self, lockout_service: LockoutService):
        """Test that concurrent failed login attempts are handled correctly."""
        username = "concurrent_user"

        # Simulate 10 concurrent failed attempts
        tasks = [
            lockout_service.record_failed_attempt(username)
            for _ in range(10)
        ]
        results = await asyncio.gather(*tasks)

        # Should eventually lock the account
        # Due to race conditions, exact attempt counts may vary, but account should lock
        is_locked = await lockout_service.is_locked(username)
        assert is_locked is True

    async def test_different_users_tracked_independently(
        self, lockout_service: LockoutService
    ):
        """Test that different users have independent lockout tracking."""
        user1 = "user_one"
        user2 = "user_two"

        # Lock user1
        for _ in range(5):
            await lockout_service.record_failed_attempt(user1)

        # User1 should be locked, user2 should not
        assert await lockout_service.is_locked(user1) is True
        assert await lockout_service.is_locked(user2) is False

        # User2 can still fail logins independently
        result = await lockout_service.record_failed_attempt(user2)
        assert result["attempts"] == 1

    async def test_redis_unavailable_returns_safe_defaults(self):
        """Test that service handles Redis unavailability gracefully."""
        # Create service with invalid Redis URL
        service = LockoutService()

        # Mock _get_redis to return None (simulating Redis unavailable)
        async def mock_get_redis():
            return None

        service._get_redis = mock_get_redis

        # is_locked should return False (fail open for availability)
        is_locked = await service.is_locked("anyuser")
        assert is_locked is False

        # record_failed_attempt should return safe defaults
        result = await service.record_failed_attempt("anyuser")
        assert result["locked"] is False
        assert result["attempts"] == 0
        assert result["remaining_attempts"] == 5

    async def test_get_lockout_service_singleton(self):
        """Test that get_lockout_service returns a singleton instance."""
        service1 = get_lockout_service()
        service2 = get_lockout_service()
        assert service1 is service2


@pytest.mark.asyncio
class TestLockoutServiceEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    async def lockout_service(self, fake_redis):
        """Create a fresh lockout service instance for each test."""
        service = LockoutService()
        # Inject fake Redis client for testing
        service._redis = fake_redis
        yield service
        # No need to close fake_redis here, the fixture handles it

    async def test_empty_username(self, lockout_service: LockoutService):
        """Test handling of empty username."""
        result = await lockout_service.record_failed_attempt("")
        assert isinstance(result, dict)
        assert "locked" in result

    async def test_special_characters_in_username(self, lockout_service: LockoutService):
        """Test usernames with special characters."""
        username = "user@example.com"
        result = await lockout_service.record_failed_attempt(username)
        assert result["attempts"] == 1

        # Verify it can be locked
        for _ in range(4):
            await lockout_service.record_failed_attempt(username)

        is_locked = await lockout_service.is_locked(username)
        assert is_locked is True

    async def test_very_long_username(self, lockout_service: LockoutService):
        """Test handling of very long usernames."""
        username = "a" * 1000
        result = await lockout_service.record_failed_attempt(username)
        assert isinstance(result, dict)

    async def test_unicode_username(self, lockout_service: LockoutService):
        """Test usernames with Unicode characters."""
        username = "用户名"
        result = await lockout_service.record_failed_attempt(username)
        assert result["attempts"] == 1
