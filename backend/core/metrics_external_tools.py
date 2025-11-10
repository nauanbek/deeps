"""
Prometheus Metrics for External Tools Integration.

Tracks tool usage, performance, and errors for monitoring and analytics.
"""

from prometheus_client import Counter, Gauge, Histogram

# ============================================================================
# Tool Execution Metrics
# ============================================================================

# Tool execution counter
tool_executions_total = Counter(
    "tool_executions_total",
    "Total number of external tool executions",
    labelnames=["tool_type", "tool_name", "success", "user_id"],
)

# Tool execution duration histogram
tool_execution_duration_seconds = Histogram(
    "tool_execution_duration_seconds",
    "External tool execution duration in seconds",
    labelnames=["tool_type", "tool_name"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],  # Custom buckets for tool execution
)

# Tool connection errors counter
tool_connection_errors_total = Counter(
    "tool_connection_errors_total",
    "Total number of tool connection errors",
    labelnames=["tool_type", "error_type"],
)

# Tool configuration tests counter
tool_connection_tests_total = Counter(
    "tool_connection_tests_total",
    "Total number of tool connection tests",
    labelnames=["tool_type", "success"],
)

# ============================================================================
# Tool Configuration Metrics
# ============================================================================

# Active tool configurations gauge
tool_configs_active = Gauge(
    "tool_configs_active",
    "Number of active external tool configurations",
    labelnames=["tool_type", "user_id"],
)

# Total tool configurations gauge
tool_configs_total = Gauge(
    "tool_configs_total",
    "Total number of external tool configurations",
    labelnames=["tool_type"],
)

# Tool configurations by provider
tool_configs_by_provider = Gauge(
    "tool_configs_by_provider",
    "Number of tool configurations by provider",
    labelnames=["provider"],
)

# ============================================================================
# Rate Limiting Metrics
# ============================================================================

# Rate limit hits counter
rate_limit_hits_total = Counter(
    "rate_limit_hits_total",
    "Total number of rate limit hits",
    labelnames=["limit_type", "user_id"],
)

# Rate limit remaining gauge
rate_limit_remaining = Gauge(
    "rate_limit_remaining",
    "Current rate limit remaining for user",
    labelnames=["limit_type", "user_id"],
)

# ============================================================================
# API Request Metrics
# ============================================================================

# External tools API requests counter
external_tools_api_requests_total = Counter(
    "external_tools_api_requests_total",
    "Total number of external tools API requests",
    labelnames=["endpoint", "method", "status_code"],
)

# External tools API request duration
external_tools_api_duration_seconds = Histogram(
    "external_tools_api_duration_seconds",
    "External tools API request duration in seconds",
    labelnames=["endpoint", "method"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

# ============================================================================
# Tool Usage Analytics Metrics
# ============================================================================

# Tool usage by category
tool_usage_by_category = Counter(
    "tool_usage_by_category",
    "Tool usage count by category",
    labelnames=["category"],  # database, git, logs, monitoring, http
)

# Tool catalog views
tool_catalog_views_total = Counter(
    "tool_catalog_views_total",
    "Total number of tool catalog views",
    labelnames=["user_id"],
)

# Tool marketplace actions
tool_marketplace_actions_total = Counter(
    "tool_marketplace_actions_total",
    "Total number of tool marketplace actions",
    labelnames=["action", "tool_type"],  # action: view, configure, test, connect
)

# ============================================================================
# Helper Functions
# ============================================================================


def record_tool_execution(
    tool_type: str,
    tool_name: str,
    duration_seconds: float,
    success: bool,
    user_id: int,
):
    """
    Record a tool execution in metrics.

    Args:
        tool_type: Type of tool (postgresql, elasticsearch, http, gitlab)
        tool_name: Name of tool configuration
        duration_seconds: Execution duration in seconds
        success: Whether execution succeeded
        user_id: User ID
    """
    # Increment execution counter
    tool_executions_total.labels(
        tool_type=tool_type,
        tool_name=tool_name,
        success=str(success).lower(),
        user_id=str(user_id),
    ).inc()

    # Record execution duration
    tool_execution_duration_seconds.labels(
        tool_type=tool_type,
        tool_name=tool_name,
    ).observe(duration_seconds)

    # Increment category usage
    category = get_tool_category(tool_type)
    tool_usage_by_category.labels(category=category).inc()


def record_connection_error(tool_type: str, error_type: str):
    """
    Record a tool connection error.

    Args:
        tool_type: Type of tool
        error_type: Type of error (timeout, auth_failed, network_error, etc.)
    """
    tool_connection_errors_total.labels(
        tool_type=tool_type,
        error_type=error_type,
    ).inc()


def record_connection_test(tool_type: str, success: bool):
    """
    Record a tool connection test.

    Args:
        tool_type: Type of tool
        success: Whether test succeeded
    """
    tool_connection_tests_total.labels(
        tool_type=tool_type,
        success=str(success).lower(),
    ).inc()


def update_tool_config_gauges(
    tool_type: str,
    active_count: int,
    total_count: int,
    user_id: int,
):
    """
    Update tool configuration gauges.

    Args:
        tool_type: Type of tool
        active_count: Number of active configurations
        total_count: Total number of configurations
        user_id: User ID
    """
    tool_configs_active.labels(
        tool_type=tool_type,
        user_id=str(user_id),
    ).set(active_count)

    tool_configs_total.labels(
        tool_type=tool_type,
    ).set(total_count)


def record_rate_limit_hit(limit_type: str, user_id: int):
    """
    Record a rate limit hit.

    Args:
        limit_type: Type of limit (tool_exec, oauth, api)
        user_id: User ID
    """
    rate_limit_hits_total.labels(
        limit_type=limit_type,
        user_id=str(user_id),
    ).inc()


def update_rate_limit_remaining(limit_type: str, user_id: int, remaining: int):
    """
    Update rate limit remaining gauge.

    Args:
        limit_type: Type of limit
        user_id: User ID
        remaining: Remaining requests
    """
    rate_limit_remaining.labels(
        limit_type=limit_type,
        user_id=str(user_id),
    ).set(remaining)


def record_api_request(
    endpoint: str,
    method: str,
    status_code: int,
    duration_seconds: float,
):
    """
    Record an external tools API request.

    Args:
        endpoint: API endpoint (e.g., /external-tools, /external-tools/{id})
        method: HTTP method (GET, POST, PUT, DELETE)
        status_code: HTTP status code
        duration_seconds: Request duration in seconds
    """
    external_tools_api_requests_total.labels(
        endpoint=endpoint,
        method=method,
        status_code=str(status_code),
    ).inc()

    external_tools_api_duration_seconds.labels(
        endpoint=endpoint,
        method=method,
    ).observe(duration_seconds)


def record_marketplace_action(action: str, tool_type: str):
    """
    Record a tool marketplace action.

    Args:
        action: Action type (view, configure, test, connect)
        tool_type: Tool type
    """
    tool_marketplace_actions_total.labels(
        action=action,
        tool_type=tool_type,
    ).inc()


def get_tool_category(tool_type: str) -> str:
    """
    Get tool category from tool type.

    Args:
        tool_type: Tool type

    Returns:
        Category string
    """
    category_map = {
        "postgresql": "database",
        "mysql": "database",
        "mongodb": "database",
        "gitlab": "git",
        "github": "git",
        "elasticsearch": "logs",
        "splunk": "logs",
        "sentry": "monitoring",
        "datadog": "monitoring",
        "http": "http",
    }
    return category_map.get(tool_type, "other")
