"""
Custom middleware for the DeepAgents Control Platform.

This module provides:
- HTTP request metrics collection
- Request timing
- Error tracking
"""

import time
from typing import Callable

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from api.v1.metrics import record_error, record_http_request


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect HTTP request metrics for Prometheus.

    Records:
    - Request count by method, endpoint, and status
    - Request duration by method and endpoint
    - Errors by type
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and collect metrics.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            Response from the route handler
        """
        # Record start time
        start_time = time.time()

        # Extract request information
        method = request.method
        path = request.url.path

        # Normalize endpoint path (remove IDs for better grouping)
        endpoint = self._normalize_path(path)

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Record metrics
            record_http_request(
                method=method,
                endpoint=endpoint,
                status=response.status_code,
                duration=duration,
            )

            # Log slow requests
            if duration > 2.0:
                logger.warning(
                    f"Slow request: {method} {path} took {duration:.2f}s "
                    f"(status: {response.status_code})"
                )

            return response

        except Exception as e:
            # Calculate duration even for errors
            duration = time.time() - start_time

            # Record error metrics
            error_type = type(e).__name__
            record_error(error_type=error_type, component="http")

            # Record as 500 error
            record_http_request(
                method=method,
                endpoint=endpoint,
                status=500,
                duration=duration,
            )

            # Log error
            logger.error(
                f"Request error: {method} {path} failed after {duration:.2f}s: {e}"
            )

            # Re-raise the exception to be handled by FastAPI
            raise

    @staticmethod
    def _normalize_path(path: str) -> str:
        """
        Normalize URL path for better metric grouping.

        Replaces UUIDs and numeric IDs with placeholders to prevent
        high cardinality in metrics.

        Args:
            path: Original URL path

        Returns:
            Normalized path with ID placeholders

        Examples:
            /api/v1/agents/123 -> /api/v1/agents/{id}
            /api/v1/executions/abc-def -> /api/v1/executions/{id}
        """
        import re

        # Replace UUIDs with {id}
        path = re.sub(
            r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "/{id}",
            path,
            flags=re.IGNORECASE,
        )

        # Replace numeric IDs with {id}
        path = re.sub(r"/\d+", "/{id}", path)

        return path


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses.

    Useful for debugging and audit trails.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request and response information.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            Response from the route handler
        """
        # Log request
        logger.debug(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        # Process request
        response = await call_next(request)

        # Log response
        logger.debug(
            f"Response: {request.method} {request.url.path} "
            f"-> {response.status_code}"
        )

        return response
