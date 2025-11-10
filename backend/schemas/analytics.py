"""
Pydantic schemas for analytics and advanced monitoring.

This module defines all schemas related to analytics and monitoring:
- Time-series analytics (execution trends over time)
- Agent usage rankings and performance metrics
- Token usage breakdown and cost analysis
- Error pattern analysis and failure tracking
- System-wide performance metrics
- Cost optimization recommendations and projections

These schemas support the Analytics and Monitoring API endpoints,
enabling comprehensive observability of agent executions, resource usage,
and cost management.
"""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class TimeSeriesParams(BaseModel):
    """Query parameters for time-series analytics."""

    start_date: datetime = Field(..., description="Start of date range")
    end_date: datetime = Field(..., description="End of date range")
    interval: Literal["hour", "day", "week", "month"] = Field(
        default="day", description="Time bucket interval"
    )
    agent_id: Optional[int] = Field(None, description="Optional agent ID filter")


class TimeSeriesDataPoint(BaseModel):
    """Single data point in time-series analysis."""

    timestamp: datetime = Field(..., description="Time bucket timestamp")
    total_executions: int = Field(..., description="Total executions in period")
    successful: int = Field(..., description="Successful executions")
    failed: int = Field(..., description="Failed executions")
    cancelled: int = Field(..., description="Cancelled executions")
    avg_duration_seconds: float = Field(
        ..., description="Average execution duration in seconds"
    )
    total_tokens: int = Field(..., description="Total tokens used in period")
    estimated_cost: float = Field(..., description="Estimated cost for period")


class TimeSeriesResponse(BaseModel):
    """Response containing time-series data points."""

    data: List[TimeSeriesDataPoint] = Field(..., description="Time-series data points")


class AgentUsageRanking(BaseModel):
    """Agent usage ranking data."""

    agent_id: int = Field(..., description="Agent ID")
    agent_name: str = Field(..., description="Agent name")
    execution_count: int = Field(..., description="Total executions")
    success_rate: float = Field(..., description="Success rate (0-1)")
    total_tokens: int = Field(..., description="Total tokens consumed")
    estimated_cost: float = Field(..., description="Estimated total cost")
    avg_duration_seconds: float = Field(..., description="Average execution duration")


class AgentUsageResponse(BaseModel):
    """Response containing agent usage rankings."""

    rankings: List[AgentUsageRanking] = Field(..., description="Agent usage rankings")


class TokenBreakdownItem(BaseModel):
    """Single item in token usage breakdown."""

    group_key: str = Field(..., description="Group identifier (agent name, model, date)")
    prompt_tokens: int = Field(..., description="Prompt tokens used")
    completion_tokens: int = Field(..., description="Completion tokens used")
    total_tokens: int = Field(..., description="Total tokens used")
    estimated_cost: float = Field(..., description="Estimated cost")


class TokenUsageBreakdownResponse(BaseModel):
    """Response containing token usage breakdown."""

    total_tokens: int = Field(..., description="Total tokens across all groups")
    total_cost: float = Field(..., description="Total cost across all groups")
    breakdown: List[TokenBreakdownItem] = Field(..., description="Breakdown by group")


class ErrorAnalysisItem(BaseModel):
    """Single error pattern analysis."""

    error_pattern: str = Field(..., description="Error pattern or message")
    count: int = Field(..., description="Number of occurrences")
    affected_agents: List[int] = Field(..., description="List of affected agent IDs")
    first_seen: datetime = Field(..., description="First occurrence timestamp")
    last_seen: datetime = Field(..., description="Last occurrence timestamp")


class ErrorAnalysisResponse(BaseModel):
    """Response containing error analysis."""

    errors: List[ErrorAnalysisItem] = Field(..., description="Error patterns")


class RecentFailure(BaseModel):
    """Recent execution failure."""

    execution_id: int = Field(..., description="Execution ID")
    error_message: str = Field(..., description="Error message")
    timestamp: datetime = Field(..., description="Failure timestamp")


class PerformanceMetrics(BaseModel):
    """Detailed performance metrics."""

    total_executions: int = Field(..., description="Total execution count")
    success_rate: float = Field(..., description="Success rate (0-1)")
    avg_duration_seconds: float = Field(..., description="Average duration")
    min_duration_seconds: float = Field(..., description="Minimum duration")
    max_duration_seconds: float = Field(..., description="Maximum duration")
    p50_duration_seconds: float = Field(..., description="50th percentile duration")
    p95_duration_seconds: float = Field(..., description="95th percentile duration")
    p99_duration_seconds: float = Field(..., description="99th percentile duration")
    avg_tokens_per_execution: float = Field(..., description="Average tokens per run")
    total_cost: float = Field(..., description="Total cost")
    uptime_percentage: float = Field(..., description="Uptime percentage")


class AgentPerformanceResponse(BaseModel):
    """Response containing agent performance metrics."""

    agent_id: int = Field(..., description="Agent ID")
    agent_name: str = Field(..., description="Agent name")
    metrics: PerformanceMetrics = Field(..., description="Performance metrics")
    recent_failures: List[RecentFailure] = Field(
        ..., description="Recent execution failures"
    )


class SystemPerformanceResponse(BaseModel):
    """Response containing system-wide performance metrics."""

    uptime_seconds: int = Field(..., description="System uptime in seconds")
    total_agents: int = Field(..., description="Total number of agents")
    active_agents: int = Field(..., description="Number of active agents")
    total_executions: int = Field(..., description="Total executions all-time")
    executions_last_24h: int = Field(..., description="Executions in last 24 hours")
    success_rate_last_24h: float = Field(..., description="Success rate last 24h (0-1)")
    avg_response_time_ms: float = Field(..., description="Average response time in ms")
    database_size_mb: float = Field(..., description="Database size in megabytes")
    cache_hit_rate: float = Field(..., description="Cache hit rate (0-1)")


class CostRecommendation(BaseModel):
    """Single cost optimization recommendation."""

    type: str = Field(..., description="Recommendation type")
    description: str = Field(..., description="Recommendation description")
    agent_id: Optional[int] = Field(None, description="Affected agent ID")
    estimated_savings: float = Field(..., description="Estimated cost savings")
    impact: Literal["low", "medium", "high"] = Field(..., description="Impact level")


class CostRecommendationsResponse(BaseModel):
    """Response containing cost optimization recommendations."""

    total_cost: float = Field(..., description="Total cost in period")
    potential_savings: float = Field(..., description="Total potential savings")
    recommendations: List[CostRecommendation] = Field(
        ..., description="List of recommendations"
    )


class AgentCostBreakdown(BaseModel):
    """Cost breakdown for single agent."""

    agent_id: int = Field(..., description="Agent ID")
    agent_name: str = Field(..., description="Agent name")
    projected_cost: float = Field(..., description="Projected monthly cost")
    percentage_of_total: float = Field(..., description="Percentage of total cost")


class CostProjectionsResponse(BaseModel):
    """Response containing cost projections."""

    current_daily_cost: float = Field(..., description="Current daily average cost")
    projected_monthly_cost: float = Field(..., description="Projected monthly cost")
    trend: Literal["increasing", "decreasing", "stable"] = Field(
        ..., description="Cost trend"
    )
    trend_percentage: float = Field(
        ..., description="Trend change percentage (positive or negative)"
    )
    breakdown_by_agent: List[AgentCostBreakdown] = Field(
        ..., description="Cost breakdown by agent"
    )
