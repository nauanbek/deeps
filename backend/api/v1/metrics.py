"""
Prometheus metrics endpoint for monitoring.

This module provides:
- HTTP request metrics (duration, count, status)
- Database connection metrics
- Agent execution metrics
- System metrics
"""

from typing import Any

from fastapi import APIRouter, Response
from loguru import logger
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

router = APIRouter(prefix="/metrics", tags=["Metrics"])

# ============================================================================
# Metric Definitions
# ============================================================================

# HTTP Request Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
)

# Agent Execution Metrics
agent_executions_total = Counter(
    "agent_executions_total",
    "Total agent executions",
    ["agent_id", "status"],
)

agent_execution_duration_seconds = Histogram(
    "agent_execution_duration_seconds",
    "Agent execution duration in seconds",
    ["agent_id"],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600),
)

agent_execution_errors_total = Counter(
    "agent_execution_errors_total",
    "Total agent execution errors",
    ["agent_id", "error_type"],
)

# Tool Execution Metrics
agent_tool_executions_total = Counter(
    "agent_tool_executions_total",
    "Total tool executions by agents",
    ["tool_name", "agent_id"],
)

# Database Metrics
db_connections_active = Gauge(
    "db_connections_active",
    "Number of active database connections",
)

db_connections_idle = Gauge(
    "db_connections_idle",
    "Number of idle database connections",
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0),
)

# Redis Metrics
redis_commands_total = Counter(
    "redis_commands_total",
    "Total Redis commands executed",
    ["command"],
)

redis_cache_hits_total = Counter(
    "redis_cache_hits_total",
    "Total cache hits",
)

redis_cache_misses_total = Counter(
    "redis_cache_misses_total",
    "Total cache misses",
)

# User Metrics
active_users_total = Gauge(
    "active_users_total",
    "Number of active users",
)

total_users = Gauge(
    "total_users",
    "Total number of registered users",
)

# Agent Metrics
total_agents = Gauge(
    "total_agents",
    "Total number of agents",
)

active_agents = Gauge(
    "active_agents",
    "Number of active agents",
)

# Template Metrics
total_templates = Gauge(
    "total_templates",
    "Total number of agent templates",
)

template_usage_total = Counter(
    "template_usage_total",
    "Template usage count",
    ["template_id"],
)

# API Token Metrics
api_tokens_total = Counter(
    "api_tokens_total",
    "Total API tokens created",
)

api_token_usage_total = Counter(
    "api_token_usage_total",
    "API token usage count",
    ["token_id"],
)

# Error Metrics
errors_total = Counter(
    "errors_total",
    "Total errors",
    ["error_type", "component"],
)


# ============================================================================
# Metrics Endpoint
# ============================================================================


@router.get("", include_in_schema=False)
async def metrics() -> Response:
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus text format for scraping.
    This endpoint should be called by Prometheus at regular intervals.

    Returns:
        Response with Prometheus metrics in text format
    """
    try:
        # Generate metrics in Prometheus format
        metrics_data = generate_latest(REGISTRY)

        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST,
        )
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return Response(
            content=b"",
            media_type=CONTENT_TYPE_LATEST,
            status_code=500,
        )


# ============================================================================
# Metrics Collection Helpers
# ============================================================================


def record_http_request(
    method: str,
    endpoint: str,
    status: int,
    duration: float,
) -> None:
    """
    Record HTTP request metrics.

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        status: HTTP status code
        duration: Request duration in seconds
    """
    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(
        duration
    )


def record_agent_execution(
    agent_id: str,
    status: str,
    duration: float,
    error_type: str | None = None,
) -> None:
    """
    Record agent execution metrics.

    Args:
        agent_id: Agent identifier
        status: Execution status (success, failed, etc.)
        duration: Execution duration in seconds
        error_type: Type of error if failed (optional)
    """
    agent_executions_total.labels(agent_id=agent_id, status=status).inc()
    agent_execution_duration_seconds.labels(agent_id=agent_id).observe(duration)

    if error_type:
        agent_execution_errors_total.labels(
            agent_id=agent_id, error_type=error_type
        ).inc()


def record_tool_execution(tool_name: str, agent_id: str) -> None:
    """
    Record tool execution metrics.

    Args:
        tool_name: Name of the tool executed
        agent_id: Agent that executed the tool
    """
    agent_tool_executions_total.labels(tool_name=tool_name, agent_id=agent_id).inc()


def record_db_query(operation: str, duration: float) -> None:
    """
    Record database query metrics.

    Args:
        operation: Database operation type (select, insert, update, delete)
        duration: Query duration in seconds
    """
    db_query_duration_seconds.labels(operation=operation).observe(duration)


def update_db_connections(active: int, idle: int) -> None:
    """
    Update database connection metrics.

    Args:
        active: Number of active connections
        idle: Number of idle connections
    """
    db_connections_active.set(active)
    db_connections_idle.set(idle)


def record_redis_command(command: str) -> None:
    """
    Record Redis command execution.

    Args:
        command: Redis command name
    """
    redis_commands_total.labels(command=command).inc()


def record_cache_access(hit: bool) -> None:
    """
    Record cache access (hit or miss).

    Args:
        hit: True if cache hit, False if cache miss
    """
    if hit:
        redis_cache_hits_total.inc()
    else:
        redis_cache_misses_total.inc()


def update_user_metrics(active: int, total: int) -> None:
    """
    Update user count metrics.

    Args:
        active: Number of active users
        total: Total number of users
    """
    active_users_total.set(active)
    total_users.set(total)


def update_agent_metrics(active: int, total: int) -> None:
    """
    Update agent count metrics.

    Args:
        active: Number of active agents
        total: Total number of agents
    """
    active_agents.set(active)
    total_agents.set(total)


def update_template_metrics(total: int) -> None:
    """
    Update template count metrics.

    Args:
        total: Total number of templates
    """
    total_templates.set(total)


def record_template_usage(template_id: str) -> None:
    """
    Record template usage.

    Args:
        template_id: Template identifier
    """
    template_usage_total.labels(template_id=template_id).inc()


def record_error(error_type: str, component: str) -> None:
    """
    Record error occurrence.

    Args:
        error_type: Type/category of error
        component: Component where error occurred
    """
    errors_total.labels(error_type=error_type, component=component).inc()
