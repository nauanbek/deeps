"""
Pydantic schemas for monitoring and analytics.

This module defines schemas for real-time monitoring and dashboard metrics:
- Dashboard overview (total agents, executions, success rate, costs)
- Agent health metrics (execution counts, success rates, avg times)
- Execution statistics (status breakdown by period)
- Token usage summaries (prompt/completion tokens, cost estimates)

These schemas power the main dashboard and monitoring endpoints,
providing quick insights into system health and agent performance.
"""

from pydantic import BaseModel, Field
from typing import Dict, Optional


class DashboardOverview(BaseModel):
    """Dashboard overview metrics."""

    total_agents: int = Field(..., description="Total number of agents")
    total_executions: int = Field(..., description="Total execution count")
    executions_today: int = Field(..., description="Executions in last 24 hours")
    success_rate: float = Field(..., description="Overall success rate percentage")
    total_tokens_used: int = Field(..., description="Sum of all tokens used")
    estimated_total_cost: float = Field(..., description="Sum of all costs")


class AgentHealth(BaseModel):
    """Agent health metrics."""

    agent_id: int = Field(..., description="Agent ID")
    agent_name: str = Field(..., description="Agent name")
    total_executions: int = Field(..., description="Total execution count")
    success_count: int = Field(..., description="Successful execution count")
    error_count: int = Field(..., description="Failed execution count")
    success_rate: float = Field(..., description="Success rate percentage")
    avg_execution_time: float = Field(..., description="Average execution time in seconds")
    last_execution_at: Optional[str] = Field(None, description="Last execution timestamp")


class ExecutionStats(BaseModel):
    """Execution statistics."""

    by_status: Dict[str, int] = Field(..., description="Counts by execution status")
    period_days: int = Field(..., description="Number of days included in stats")


class TokenUsageSummary(BaseModel):
    """Token usage summary."""

    total_tokens: int = Field(..., description="Total tokens used")
    prompt_tokens: int = Field(..., description="Prompt tokens used")
    completion_tokens: int = Field(..., description="Completion tokens used")
    estimated_cost: float = Field(..., description="Estimated total cost")
    period_days: int = Field(..., description="Number of days included in summary")
