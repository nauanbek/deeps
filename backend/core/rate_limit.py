"""
Rate limiting middleware for API protection.

Implements token bucket algorithm using Redis for distributed rate limiting.
Prevents abuse, DDoS attacks, and ensures fair resource allocation.
"""

import time
from typing import Callable, Optional

import redis.asyncio as redis
from fastapi import HTTPException, Request, Response, status
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis token bucket algorithm.

    Limits requests per user/IP to prevent abuse and ensure fair usage.
    """

    def __init__(
        self,
        app,
        redis_url: str,
        default_limit: int = 60,
        default_window: int = 60,
    ):
        """
        Initialize rate limiter.

        Args:
            app: FastAPI application
            redis_url: Redis connection URL
            default_limit: Default requests per window (60 req/min)
            default_window: Time window in seconds (60s = 1 minute)
        """
        super().__init__(app)
        self.redis_url = redis_url
        self.default_limit = default_limit
        self.default_window = default_window
        self._redis_client: Optional[redis.Redis] = None

    async def get_redis_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._redis_client is None:
            self._redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self._redis_client

    def get_rate_limit_key(self, identifier: str) -> str:
        """
        Generate Redis key for rate limiting.

        Args:
            identifier: User ID or IP address

        Returns:
            Redis key string
        """
        return f"ratelimit:{identifier}"

    def is_excluded_path(self, path: str) -> bool:
        """
        Check if path should be excluded from rate limiting.

        Args:
            path: Request path

        Returns:
            True if path should be excluded
        """
        # Exclude health checks, metrics, and docs
        excluded_prefixes = [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
        return any(path.startswith(prefix) for prefix in excluded_prefixes)

    async def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        window: int,
    ) -> tuple[bool, dict]:
        """
        Check if request is within rate limit using token bucket algorithm.

        Args:
            identifier: User ID or IP address
            limit: Maximum requests per window
            window: Time window in seconds

        Returns:
            Tuple of (allowed, info_dict)
            - allowed: True if request is allowed
            - info_dict: Rate limit info (limit, remaining, reset_time)
        """
        try:
            redis_client = await self.get_redis_client()
            key = self.get_rate_limit_key(identifier)
            current_time = int(time.time())

            # Use Redis pipeline for atomic operations
            pipe = redis_client.pipeline()

            # Get current count and TTL
            pipe.get(key)
            pipe.ttl(key)

            results = await pipe.execute()
            current_count = int(results[0]) if results[0] else 0
            ttl = results[1] if results[1] and results[1] > 0 else window

            # Calculate reset time
            reset_time = current_time + ttl

            # Check if limit exceeded
            if current_count >= limit:
                return False, {
                    "limit": limit,
                    "remaining": 0,
                    "reset": reset_time,
                    "retry_after": ttl,
                }

            # Increment counter
            pipe = redis_client.pipeline()
            pipe.incr(key)

            # Set expiry only on first request (TTL = -2 means key doesn't exist)
            if results[1] == -2:
                pipe.expire(key, window)

            await pipe.execute()

            remaining = max(0, limit - current_count - 1)

            return True, {
                "limit": limit,
                "remaining": remaining,
                "reset": reset_time,
            }

        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # On Redis error, allow the request (fail open)
            return True, {
                "limit": limit,
                "remaining": limit,
                "reset": int(time.time()) + window,
            }

    def get_identifier(self, request: Request) -> str:
        """
        Get unique identifier for rate limiting.

        Prefers user_id from JWT, falls back to IP address.

        Args:
            request: FastAPI request

        Returns:
            Identifier string (user_id or IP)
        """
        # Try to get user ID from request state (set by auth middleware)
        user = getattr(request.state, "user", None)
        if user and hasattr(user, "id"):
            return f"user:{user.id}"

        # Fallback to IP address
        # Check X-Forwarded-For header for real IP (behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take first IP from comma-separated list
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip:{client_ip}"

    def get_rate_limit_for_path(self, path: str, method: str) -> tuple[int, int]:
        """
        Get rate limit configuration for specific path.

        Different endpoints can have different limits.

        Args:
            path: Request path
            method: HTTP method

        Returns:
            Tuple of (limit, window)
        """
        # Stricter limits for expensive operations
        if "/api/v1/executions" in path and method == "POST":
            # Agent execution: 10 requests per minute
            return 10, 60

        if "/api/v1/analytics" in path:
            # Analytics: 30 requests per minute
            return 30, 60

        if "/api/v1/auth" in path:
            # Authentication: 5 requests per minute (prevent brute force)
            return 5, 60

        # Default for all other endpoints
        return self.default_limit, self.default_window

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint

        Returns:
            Response with rate limit headers

        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        # Skip rate limiting for excluded paths
        if self.is_excluded_path(request.url.path):
            return await call_next(request)

        # Get identifier and rate limit config
        identifier = self.get_identifier(request)
        limit, window = self.get_rate_limit_for_path(
            request.url.path,
            request.method
        )

        # Check rate limit
        allowed, info = await self.check_rate_limit(identifier, limit, window)

        # Add rate limit headers to response
        if not allowed:
            # Rate limit exceeded - return 429
            logger.warning(
                f"Rate limit exceeded for {identifier} "
                f"on {request.method} {request.url.path}"
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded. Try again in {info['retry_after']} seconds.",
                    "limit": info["limit"],
                    "retry_after": info["retry_after"],
                    "reset": info["reset"],
                },
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(info["reset"]),
                    "Retry-After": str(info["retry_after"]),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to successful response
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])

        return response
