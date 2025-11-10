"""
Health check endpoints for monitoring and load balancers.

This module provides:
- Basic health check (liveness)
- Readiness check (ready to serve traffic)
- Deep health check (all dependencies)
"""

import asyncio
import os
import shutil
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, status
from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import engine

router = APIRouter(prefix="/health", tags=["Health"])


# ============================================================================
# Basic Health Check (Liveness)
# ============================================================================


@router.get("")
async def health_check() -> dict[str, Any]:
    """
    Basic health check endpoint for monitoring and load balancers.

    This is a simple check that the service is alive and responding.
    Use this for Kubernetes liveness probes.

    Returns:
        Health status and basic information
    """
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "service": settings.PROJECT_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================================
# Readiness Check
# ============================================================================


@router.get("/readiness")
async def readiness_check() -> dict[str, Any]:
    """
    Readiness check endpoint.

    Checks if the service is ready to serve traffic.
    This includes basic dependency checks.
    Use this for Kubernetes readiness probes.

    Returns:
        Readiness status

    Raises:
        HTTPException: If service is not ready
    """
    checks = {
        "database": False,
        "redis": False,
    }
    errors = []

    # Check database connection
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        logger.error(f"Database readiness check failed: {e}")
        errors.append(f"Database: {str(e)}")

    # Check Redis connection (if configured)
    try:
        # Import redis here to avoid circular imports
        import redis.asyncio as redis

        redis_client = redis.from_url(str(settings.REDIS_URL))
        await redis_client.ping()
        await redis_client.close()
        checks["redis"] = True
    except Exception as e:
        logger.error(f"Redis readiness check failed: {e}")
        errors.append(f"Redis: {str(e)}")

    # Determine overall readiness
    is_ready = all(checks.values())

    if not is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "checks": checks,
                "errors": errors,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    return {
        "status": "ready",
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================================
# Liveness Check
# ============================================================================


@router.get("/liveness")
async def liveness_check() -> dict[str, str]:
    """
    Liveness check endpoint.

    Simple check that the service is alive.
    Use this for basic monitoring.

    Returns:
        Liveness status
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================================
# Deep Health Check
# ============================================================================


@router.get("/deep")
async def deep_health_check() -> dict[str, Any]:
    """
    Comprehensive health check for all dependencies.

    Checks:
    - Database connectivity and query execution
    - Redis connectivity and operations
    - Disk space availability
    - Memory usage
    - External API reachability (Anthropic, OpenAI)

    This endpoint may be slow (5-10 seconds) as it thoroughly tests all systems.
    Do NOT use this for load balancer health checks.

    Returns:
        Detailed health status of all components

    Raises:
        HTTPException: If any critical component is unhealthy
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {},
    }

    all_healthy = True

    # ========================================================================
    # Database Health Check
    # ========================================================================
    try:
        db_start = asyncio.get_event_loop().time()

        async with engine.connect() as conn:
            # Test connection
            await conn.execute(text("SELECT 1"))

            # Test query execution
            result = await conn.execute(
                text("SELECT COUNT(*) FROM information_schema.tables")
            )
            table_count = result.scalar()

        db_duration = asyncio.get_event_loop().time() - db_start

        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time_ms": round(db_duration * 1000, 2),
            "table_count": table_count,
        }
    except Exception as e:
        logger.error(f"Database deep health check failed: {e}")
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        all_healthy = False

    # ========================================================================
    # Redis Health Check
    # ========================================================================
    try:
        import redis.asyncio as redis

        redis_start = asyncio.get_event_loop().time()

        redis_client = redis.from_url(str(settings.REDIS_URL))

        # Test ping
        await redis_client.ping()

        # Test set/get
        test_key = "health_check_test"
        await redis_client.set(test_key, "test_value", ex=10)
        value = await redis_client.get(test_key)
        await redis_client.delete(test_key)

        # Get info
        info = await redis_client.info()
        await redis_client.close()

        redis_duration = asyncio.get_event_loop().time() - redis_start

        health_status["checks"]["redis"] = {
            "status": "healthy",
            "response_time_ms": round(redis_duration * 1000, 2),
            "memory_used_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
            "connected_clients": info.get("connected_clients", 0),
        }
    except Exception as e:
        logger.error(f"Redis deep health check failed: {e}")
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        all_healthy = False

    # ========================================================================
    # Disk Space Check
    # ========================================================================
    try:
        disk_usage = shutil.disk_usage("/")
        free_percent = (disk_usage.free / disk_usage.total) * 100

        disk_status = "healthy"
        if free_percent < 5:
            disk_status = "critical"
            all_healthy = False
        elif free_percent < 10:
            disk_status = "warning"

        health_status["checks"]["disk"] = {
            "status": disk_status,
            "total_gb": round(disk_usage.total / 1024 / 1024 / 1024, 2),
            "used_gb": round(disk_usage.used / 1024 / 1024 / 1024, 2),
            "free_gb": round(disk_usage.free / 1024 / 1024 / 1024, 2),
            "free_percent": round(free_percent, 2),
        }
    except Exception as e:
        logger.error(f"Disk space check failed: {e}")
        health_status["checks"]["disk"] = {
            "status": "unknown",
            "error": str(e),
        }

    # ========================================================================
    # Memory Check
    # ========================================================================
    try:
        import psutil

        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        memory_status = "healthy"
        if memory_percent > 95:
            memory_status = "critical"
            all_healthy = False
        elif memory_percent > 90:
            memory_status = "warning"

        health_status["checks"]["memory"] = {
            "status": memory_status,
            "total_gb": round(memory.total / 1024 / 1024 / 1024, 2),
            "available_gb": round(memory.available / 1024 / 1024 / 1024, 2),
            "used_percent": memory_percent,
        }
    except ImportError:
        health_status["checks"]["memory"] = {
            "status": "unknown",
            "message": "psutil not installed",
        }
    except Exception as e:
        logger.error(f"Memory check failed: {e}")
        health_status["checks"]["memory"] = {
            "status": "unknown",
            "error": str(e),
        }

    # ========================================================================
    # External API Checks (Anthropic, OpenAI)
    # ========================================================================
    # Only check if API keys are configured
    if settings.ANTHROPIC_API_KEY:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.anthropic.com",
                    timeout=5.0,
                    headers={"x-api-key": settings.ANTHROPIC_API_KEY},
                )
                health_status["checks"]["anthropic_api"] = {
                    "status": "reachable",
                    "status_code": response.status_code,
                }
        except Exception as e:
            logger.warning(f"Anthropic API check failed: {e}")
            health_status["checks"]["anthropic_api"] = {
                "status": "unreachable",
                "error": str(e),
            }

    if settings.OPENAI_API_KEY:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    timeout=5.0,
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                )
                health_status["checks"]["openai_api"] = {
                    "status": "reachable",
                    "status_code": response.status_code,
                }
        except Exception as e:
            logger.warning(f"OpenAI API check failed: {e}")
            health_status["checks"]["openai_api"] = {
                "status": "unreachable",
                "error": str(e),
            }

    # ========================================================================
    # Overall Status
    # ========================================================================
    if not all_healthy:
        health_status["status"] = "degraded"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status,
        )

    return health_status
