"""API endpoints for advanced analytics and monitoring."""

from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_active_user
from models.user import User
from schemas.analytics import (
    AgentPerformanceResponse,
    AgentUsageResponse,
    CostProjectionsResponse,
    CostRecommendationsResponse,
    ErrorAnalysisResponse,
    SystemPerformanceResponse,
    TimeSeriesResponse,
    TokenUsageBreakdownResponse,
)
from services.analytics_service import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/executions/time-series", response_model=TimeSeriesResponse)
async def get_execution_time_series(
    start_date: datetime = Query(..., description="Start of date range"),
    end_date: datetime = Query(..., description="End of date range"),
    interval: Literal["hour", "day", "week", "month"] = Query(
        "day", description="Time bucket interval"
    ),
    agent_id: Optional[int] = Query(None, description="Optional agent ID filter"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get execution time-series analytics.

    Returns time-bucketed execution metrics including counts by status,
    average duration, token usage, and cost estimates over time.

    Args:
        start_date: Start of date range (ISO 8601 format)
        end_date: End of date range (ISO 8601 format)
        interval: Time bucket interval (hour, day, week, month)
        agent_id: Optional filter by specific agent ID

    **Example Response:**
    ```json
    {
        "data": [
            {
                "timestamp": "2025-11-08T00:00:00Z",
                "total_executions": 45,
                "successful": 42,
                "failed": 2,
                "cancelled": 1,
                "avg_duration_seconds": 12.5,
                "total_tokens": 15000,
                "estimated_cost": 0.45
            }
        ]
    }
    ```
    """
    data = await analytics_service.get_execution_time_series(
        db, start_date=start_date, end_date=end_date, interval=interval, agent_id=agent_id
    )
    return {"data": data}


@router.get("/agents/usage", response_model=AgentUsageResponse)
async def get_agent_usage_rankings(
    start_date: datetime = Query(..., description="Start of date range"),
    end_date: datetime = Query(..., description="End of date range"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of agents to return"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get agent usage rankings.

    Returns top agents ranked by execution count with detailed usage metrics
    including success rates, token consumption, costs, and performance.

    Args:
        start_date: Start of date range (ISO 8601 format)
        end_date: End of date range (ISO 8601 format)
        limit: Maximum number of agents (1-100, default: 10)

    **Example Response:**
    ```json
    {
        "rankings": [
            {
                "agent_id": 1,
                "agent_name": "Research Agent",
                "execution_count": 150,
                "success_rate": 0.96,
                "total_tokens": 250000,
                "estimated_cost": 7.50,
                "avg_duration_seconds": 15.2
            }
        ]
    }
    ```
    """
    rankings = await analytics_service.get_agent_usage_rankings(
        db, start_date=start_date, end_date=end_date, limit=limit
    )
    return {"rankings": rankings}


@router.get("/token-usage/breakdown", response_model=TokenUsageBreakdownResponse)
async def get_token_usage_breakdown(
    start_date: datetime = Query(..., description="Start of date range"),
    end_date: datetime = Query(..., description="End of date range"),
    group_by: Literal["agent", "model", "day"] = Query(
        "agent", description="Dimension to group by"
    ),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get token usage breakdown by dimension.

    Break down token usage and costs by agent, model, or day to identify
    consumption patterns and cost drivers.

    Args:
        start_date: Start of date range (ISO 8601 format)
        end_date: End of date range (ISO 8601 format)
        group_by: Grouping dimension (agent, model, day)

    **Example Response:**
    ```json
    {
        "total_tokens": 500000,
        "total_cost": 15.00,
        "breakdown": [
            {
                "group_key": "claude-3-5-sonnet-20241022",
                "prompt_tokens": 200000,
                "completion_tokens": 100000,
                "total_tokens": 300000,
                "estimated_cost": 9.00
            }
        ]
    }
    ```
    """
    breakdown = await analytics_service.get_token_usage_breakdown(
        db, start_date=start_date, end_date=end_date, group_by=group_by
    )
    return breakdown


@router.get("/error-analysis", response_model=ErrorAnalysisResponse)
async def get_error_analysis(
    start_date: datetime = Query(..., description="Start of date range"),
    end_date: datetime = Query(..., description="End of date range"),
    limit: int = Query(10, ge=1, le=100, description="Maximum error patterns to return"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get error pattern analysis.

    Analyzes failed executions to identify common error patterns, affected agents,
    and error frequency over time.

    Args:
        start_date: Start of date range (ISO 8601 format)
        end_date: End of date range (ISO 8601 format)
        limit: Maximum error patterns (1-100, default: 10)

    **Example Response:**
    ```json
    {
        "errors": [
            {
                "error_pattern": "Rate limit exceeded",
                "count": 15,
                "affected_agents": [1, 3, 5],
                "first_seen": "2025-11-01T10:00:00Z",
                "last_seen": "2025-11-08T14:30:00Z"
            }
        ]
    }
    ```
    """
    errors = await analytics_service.get_error_analysis(
        db, start_date=start_date, end_date=end_date, limit=limit
    )
    return {"errors": errors}


@router.get("/performance/agents/{agent_id}", response_model=AgentPerformanceResponse)
async def get_agent_performance_metrics(
    agent_id: int,
    start_date: datetime = Query(..., description="Start of date range"),
    end_date: datetime = Query(..., description="End of date range"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed performance metrics for a specific agent.

    Returns comprehensive performance statistics including duration percentiles,
    success rates, token usage, costs, and recent failures.

    Args:
        agent_id: Agent ID
        start_date: Start of date range (ISO 8601 format)
        end_date: End of date range (ISO 8601 format)

    **Example Response:**
    ```json
    {
        "agent_id": 1,
        "agent_name": "Research Agent",
        "metrics": {
            "total_executions": 150,
            "success_rate": 0.96,
            "avg_duration_seconds": 15.2,
            "min_duration_seconds": 2.1,
            "max_duration_seconds": 45.3,
            "p50_duration_seconds": 12.5,
            "p95_duration_seconds": 28.7,
            "p99_duration_seconds": 40.1,
            "avg_tokens_per_execution": 1667,
            "total_cost": 7.50,
            "uptime_percentage": 98.5
        },
        "recent_failures": [
            {
                "execution_id": 123,
                "error_message": "Rate limit exceeded",
                "timestamp": "2025-11-08T10:30:00Z"
            }
        ]
    }
    ```
    """
    metrics = await analytics_service.get_agent_performance_metrics(
        db, agent_id=agent_id, start_date=start_date, end_date=end_date
    )

    if metrics is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    return metrics


@router.get("/performance/system", response_model=SystemPerformanceResponse)
async def get_system_performance_metrics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get overall system performance metrics.

    Returns system-wide performance statistics including uptime, agent counts,
    execution volumes, success rates, and response times.

    **Example Response:**
    ```json
    {
        "uptime_seconds": 864000,
        "total_agents": 12,
        "active_agents": 10,
        "total_executions": 5000,
        "executions_last_24h": 250,
        "success_rate_last_24h": 0.94,
        "avg_response_time_ms": 1250,
        "database_size_mb": 512,
        "cache_hit_rate": 0.85
    }
    ```
    """
    metrics = await analytics_service.get_system_performance_metrics(db)
    return metrics


@router.get("/cost/recommendations", response_model=CostRecommendationsResponse)
async def get_cost_recommendations(
    start_date: datetime = Query(..., description="Start of date range"),
    end_date: datetime = Query(..., description="End of date range"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get cost optimization recommendations.

    Analyzes usage patterns to identify cost optimization opportunities such as
    model downgrades, token limit adjustments, and inefficient configurations.

    Args:
        start_date: Start of date range (ISO 8601 format)
        end_date: End of date range (ISO 8601 format)

    **Example Response:**
    ```json
    {
        "total_cost": 150.00,
        "potential_savings": 25.00,
        "recommendations": [
            {
                "type": "model_downgrade",
                "description": "Agent 'Simple QA' uses Claude Opus but has simple tasks.",
                "agent_id": 5,
                "estimated_savings": 15.00,
                "impact": "low"
            }
        ]
    }
    ```
    """
    recommendations = await analytics_service.get_cost_recommendations(
        db, start_date=start_date, end_date=end_date
    )
    return recommendations


@router.get("/cost/projections", response_model=CostProjectionsResponse)
async def get_cost_projections(
    projection_days: int = Query(
        30, ge=1, le=365, description="Number of days to project"
    ),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get cost projections based on historical usage.

    Projects future costs by analyzing historical usage patterns and trends,
    with breakdown by agent.

    Args:
        projection_days: Days to project (1-365, default: 30)

    **Example Response:**
    ```json
    {
        "current_daily_cost": 5.00,
        "projected_monthly_cost": 150.00,
        "trend": "increasing",
        "trend_percentage": 12.5,
        "breakdown_by_agent": [
            {
                "agent_id": 1,
                "agent_name": "Research Agent",
                "projected_cost": 45.00,
                "percentage_of_total": 30.0
            }
        ]
    }
    ```
    """
    projections = await analytics_service.get_cost_projections(
        db, projection_days=projection_days
    )
    return projections
