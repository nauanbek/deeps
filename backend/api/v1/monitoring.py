"""API endpoints for monitoring and analytics."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from core.database import get_db
from core.dependencies import get_current_active_user
from models.user import User
from services.monitoring_service import monitoring_service
from schemas.monitoring import (
    DashboardOverview,
    AgentHealth,
    ExecutionStats,
    TokenUsageSummary
)
from schemas.execution import ExecutionResponse


router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/dashboard", response_model=DashboardOverview)
async def get_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get dashboard overview metrics.

    Returns high-level metrics including:
    - Total agents
    - Total executions
    - Executions in last 24 hours
    - Overall success rate
    - Total tokens used
    - Estimated total cost

    **Example Response:**
    ```json
    {
        "total_agents": 5,
        "total_executions": 150,
        "executions_today": 12,
        "success_rate": 95.5,
        "total_tokens_used": 125000,
        "estimated_total_cost": 6.25
    }
    ```
    """
    data = await monitoring_service.get_dashboard_overview(db)
    return data


@router.get("/agents/health", response_model=List[AgentHealth])
async def get_agent_health(
    agent_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get agent health metrics.

    Args:
        agent_id: Optional agent ID to filter by specific agent

    Returns health metrics for each agent including:
    - Total executions
    - Success/error counts
    - Success rate
    - Average execution time
    - Last execution timestamp

    **Example Response:**
    ```json
    [
        {
            "agent_id": 1,
            "agent_name": "Customer Support Agent",
            "total_executions": 45,
            "success_count": 43,
            "error_count": 2,
            "success_rate": 95.6,
            "avg_execution_time": 2.5,
            "last_execution_at": "2025-01-08T10:30:00"
        }
    ]
    ```
    """
    health_data = await monitoring_service.get_agent_health(db, agent_id)
    return health_data


@router.get("/executions/stats", response_model=ExecutionStats)
async def get_execution_stats(
    days: int = Query(7, ge=1, le=365, description="Number of days to include in stats"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get execution statistics for the last N days.

    Args:
        days: Number of days to include (1-365, default: 7)

    Returns execution counts grouped by status.

    **Example Response:**
    ```json
    {
        "by_status": {
            "pending": 2,
            "running": 1,
            "completed": 120,
            "failed": 5,
            "cancelled": 0
        },
        "period_days": 7
    }
    ```
    """
    stats = await monitoring_service.get_execution_stats(db, days)
    return stats


@router.get("/usage/tokens", response_model=TokenUsageSummary)
async def get_token_usage(
    days: int = Query(30, ge=1, le=365, description="Number of days to include in summary"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get token usage summary for the last N days.

    Args:
        days: Number of days to include (1-365, default: 30)

    Returns token usage metrics including costs.

    **Example Response:**
    ```json
    {
        "total_tokens": 125000,
        "prompt_tokens": 75000,
        "completion_tokens": 50000,
        "estimated_cost": 6.25,
        "period_days": 30
    }
    ```
    """
    usage = await monitoring_service.get_token_usage_summary(db, days)
    return usage


@router.get("/executions/recent", response_model=List[ExecutionResponse])
async def get_recent_executions(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of executions to return"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get most recent executions.

    Args:
        limit: Maximum number of executions to return (1-100, default: 10)

    Returns list of recent executions ordered by creation time (newest first).

    **Example Response:**
    ```json
    [
        {
            "id": 150,
            "agent_id": 1,
            "status": "completed",
            "input_data": {"message": "Hello"},
            "output_data": {"response": "Hi there!"},
            "started_at": "2025-01-08T10:30:00",
            "completed_at": "2025-01-08T10:30:05",
            "created_at": "2025-01-08T10:30:00"
        }
    ]
    ```
    """
    executions = await monitoring_service.get_recent_executions(db, limit)
    return executions


@router.get("/executions/errors", response_model=List[ExecutionResponse])
async def get_recent_errors(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of errors to return"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get most recent failed executions.

    Args:
        limit: Maximum number of errors to return (1-100, default: 10)

    Returns list of recent failed executions ordered by creation time (newest first).

    **Example Response:**
    ```json
    [
        {
            "id": 145,
            "agent_id": 1,
            "status": "failed",
            "input_data": {"message": "Test"},
            "error_message": "API rate limit exceeded",
            "started_at": "2025-01-08T09:15:00",
            "completed_at": "2025-01-08T09:15:02",
            "created_at": "2025-01-08T09:15:00"
        }
    ]
    ```
    """
    errors = await monitoring_service.get_recent_errors(db, limit)
    return errors
