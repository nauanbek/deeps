"""Service layer for advanced analytics and monitoring."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, case, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent import Agent
from models.execution import Execution


class AnalyticsService:
    """Service for managing advanced analytics operations."""

    async def get_execution_time_series(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        interval: str,
        agent_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate time-series data for execution metrics.

        Uses database-level aggregations to avoid loading 100k+ records into memory.

        Args:
            db: Database session
            start_date: Start of date range
            end_date: End of date range
            interval: Time bucket interval ('hour', 'day', 'week', 'month')
            agent_id: Optional agent ID filter

        Returns:
            List of time-series data points with execution metrics
        """
        # Map interval to PostgreSQL date_trunc precision
        trunc_precision = {
            "hour": "hour",
            "day": "day",
            "week": "week",
            "month": "month",
        }.get(interval, "day")

        # Build aggregated query (fixes memory issue - aggregates at DB level)
        # Returns ~100 rows instead of 100,000+ execution objects
        query = (
            select(
                func.date_trunc(trunc_precision, Execution.started_at).label('bucket'),
                func.count().label('total'),
                func.sum(
                    case((Execution.status == "completed", 1), else_=0)
                ).label('successful'),
                func.sum(
                    case((Execution.status == "failed", 1), else_=0)
                ).label('failed'),
                func.sum(
                    case((Execution.status == "cancelled", 1), else_=0)
                ).label('cancelled'),
                func.avg(
                    case(
                        (
                            and_(
                                Execution.status == "completed",
                                Execution.completed_at.isnot(None),
                                Execution.started_at.isnot(None)
                            ),
                            func.extract('epoch', Execution.completed_at - Execution.started_at)
                        ),
                        else_=None
                    )
                ).label('avg_duration'),
                func.sum(Execution.total_tokens).label('total_tokens'),
                func.sum(Execution.estimated_cost).label('estimated_cost'),
            )
            .where(
                and_(
                    Execution.started_at >= start_date,
                    Execution.started_at <= end_date,
                    Execution.started_at.isnot(None),
                )
            )
            .group_by('bucket')
            .order_by('bucket')
        )

        if agent_id:
            query = query.where(Execution.agent_id == agent_id)

        result = await db.execute(query)
        rows = result.all()

        # Build time-series data from aggregated results
        time_series_data = []
        for row in rows:
            time_series_data.append({
                "timestamp": row.bucket,
                "total_executions": row.total or 0,
                "successful": row.successful or 0,
                "failed": row.failed or 0,
                "cancelled": row.cancelled or 0,
                "avg_duration_seconds": float(row.avg_duration or 0.0),
                "total_tokens": row.total_tokens or 0,
                "estimated_cost": float(row.estimated_cost or Decimal("0.0")),
            })

        return time_series_data

    def _get_time_bucket(self, dt: datetime, interval: str) -> datetime:
        """
        Get the time bucket for a given datetime and interval.

        Args:
            dt: Datetime to bucket
            interval: Bucket interval ('hour', 'day', 'week', 'month')

        Returns:
            Bucket start datetime
        """
        if interval == "hour":
            return dt.replace(minute=0, second=0, microsecond=0)
        elif interval == "day":
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)
        elif interval == "week":
            # Start of week (Monday)
            days_since_monday = dt.weekday()
            week_start = dt - timedelta(days=days_since_monday)
            return week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        elif interval == "month":
            return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            return dt

    async def get_agent_usage_rankings(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get top agents by usage.

        Args:
            db: Database session
            start_date: Start of date range
            end_date: End of date range
            limit: Maximum number of agents to return

        Returns:
            List of agent usage rankings
        """
        # Get all executions in date range
        query = (
            select(Execution)
            .where(
                and_(
                    Execution.started_at >= start_date,
                    Execution.started_at <= end_date,
                    Execution.started_at.isnot(None),
                )
            )
        )
        result = await db.execute(query)
        executions = result.scalars().all()

        if not executions:
            return []

        # Group by agent
        agent_data: Dict[int, List[Execution]] = {}
        for execution in executions:
            if execution.agent_id not in agent_data:
                agent_data[execution.agent_id] = []
            agent_data[execution.agent_id].append(execution)

        # Pre-fetch all agents in a single query (fixes N+1 query issue)
        agent_ids = list(agent_data.keys())
        agents_query = select(Agent).where(Agent.id.in_(agent_ids))
        agents_result = await db.execute(agents_query)
        agents = agents_result.scalars().all()

        # Create agent lookup dictionary
        agents_by_id = {agent.id: agent for agent in agents}

        # Build rankings
        rankings = []
        for agent_id, agent_executions in agent_data.items():
            # Get agent details from pre-fetched dictionary
            agent = agents_by_id.get(agent_id)

            if not agent:
                continue

            # Calculate metrics
            total = len(agent_executions)
            successful = sum(1 for e in agent_executions if e.status == "completed")
            success_rate = successful / total if total > 0 else 0.0

            # Calculate average duration
            durations = [
                (e.completed_at - e.started_at).total_seconds()
                for e in agent_executions
                if e.status == "completed"
                and e.completed_at
                and e.started_at
            ]
            avg_duration = sum(durations) / len(durations) if durations else 0.0

            # Sum tokens and costs
            total_tokens = sum(e.total_tokens or 0 for e in agent_executions)
            total_cost = sum(
                float(e.estimated_cost or Decimal("0.0"))
                for e in agent_executions
            )

            rankings.append({
                "agent_id": agent.id,
                "agent_name": agent.name,
                "execution_count": total,
                "success_rate": success_rate,
                "total_tokens": total_tokens,
                "estimated_cost": total_cost,
                "avg_duration_seconds": avg_duration,
            })

        # Sort by execution count (descending) and limit
        rankings.sort(key=lambda x: x["execution_count"], reverse=True)
        return rankings[:limit]

    async def get_token_usage_breakdown(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        group_by: str,
    ) -> Dict[str, Any]:
        """
        Break down token usage by dimension.

        Args:
            db: Database session
            start_date: Start of date range
            end_date: End of date range
            group_by: Grouping dimension ('agent', 'model', 'day')

        Returns:
            Token usage breakdown with totals and breakdowns
        """
        # Get all executions in date range
        query = (
            select(Execution)
            .where(
                and_(
                    Execution.started_at >= start_date,
                    Execution.started_at <= end_date,
                    Execution.started_at.isnot(None),
                )
            )
        )
        result = await db.execute(query)
        executions = result.scalars().all()

        if not executions:
            return {
                "total_tokens": 0,
                "total_cost": 0.0,
                "breakdown": [],
            }

        # Pre-fetch agents if grouping by agent or model (fixes N+1 query issue)
        agents_by_id: Dict[int, Agent] = {}
        if group_by in ("agent", "model"):
            unique_agent_ids = list(set(e.agent_id for e in executions))
            agents_query = select(Agent).where(Agent.id.in_(unique_agent_ids))
            agents_result = await db.execute(agents_query)
            agents = agents_result.scalars().all()
            agents_by_id = {agent.id: agent for agent in agents}

        # Group executions
        groups: Dict[str, List[Execution]] = {}
        for execution in executions:
            if group_by == "agent":
                # Get agent name from pre-fetched dictionary
                agent = agents_by_id.get(execution.agent_id)
                group_key = agent.name if agent else f"Agent {execution.agent_id}"
            elif group_by == "model":
                # Get model name from pre-fetched dictionary
                agent = agents_by_id.get(execution.agent_id)
                group_key = agent.model_name if agent else "Unknown"
            elif group_by == "day":
                # Group by day
                group_key = execution.started_at.strftime("%Y-%m-%d")
            else:
                group_key = "Unknown"

            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(execution)

        # Build breakdown
        breakdown = []
        total_tokens = 0
        total_cost = 0.0

        for group_key, group_executions in groups.items():
            prompt_tokens = sum(e.prompt_tokens or 0 for e in group_executions)
            completion_tokens = sum(e.completion_tokens or 0 for e in group_executions)
            group_total_tokens = sum(e.total_tokens or 0 for e in group_executions)
            group_cost = sum(
                float(e.estimated_cost or Decimal("0.0"))
                for e in group_executions
            )

            breakdown.append({
                "group_key": group_key,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": group_total_tokens,
                "estimated_cost": group_cost,
            })

            total_tokens += group_total_tokens
            total_cost += group_cost

        # Sort by total tokens (descending)
        breakdown.sort(key=lambda x: x["total_tokens"], reverse=True)

        return {
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "breakdown": breakdown,
        }

    async def get_error_analysis(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Analyze common error patterns.

        Args:
            db: Database session
            start_date: Start of date range
            end_date: End of date range
            limit: Maximum number of error patterns to return

        Returns:
            List of error patterns with counts and affected agents
        """
        # Get failed executions in date range
        query = (
            select(Execution)
            .where(
                and_(
                    Execution.status == "failed",
                    Execution.started_at >= start_date,
                    Execution.started_at <= end_date,
                    Execution.error_message.isnot(None),
                )
            )
        )
        result = await db.execute(query)
        failed_executions = result.scalars().all()

        if not failed_executions:
            return []

        # Group by error pattern (using error message as pattern)
        error_patterns: Dict[str, Dict[str, Any]] = {}
        for execution in failed_executions:
            error_msg = execution.error_message or "Unknown error"

            if error_msg not in error_patterns:
                error_patterns[error_msg] = {
                    "error_pattern": error_msg,
                    "count": 0,
                    "affected_agents": set(),
                    "first_seen": execution.started_at,
                    "last_seen": execution.started_at,
                }

            pattern_data = error_patterns[error_msg]
            pattern_data["count"] += 1
            pattern_data["affected_agents"].add(execution.agent_id)

            # Update timestamps
            if execution.started_at < pattern_data["first_seen"]:
                pattern_data["first_seen"] = execution.started_at
            if execution.started_at > pattern_data["last_seen"]:
                pattern_data["last_seen"] = execution.started_at

        # Convert to list and format
        error_list = []
        for pattern_data in error_patterns.values():
            error_list.append({
                "error_pattern": pattern_data["error_pattern"],
                "count": pattern_data["count"],
                "affected_agents": list(pattern_data["affected_agents"]),
                "first_seen": pattern_data["first_seen"],
                "last_seen": pattern_data["last_seen"],
            })

        # Sort by count (descending) and limit
        error_list.sort(key=lambda x: x["count"], reverse=True)
        return error_list[:limit]

    async def get_agent_performance_metrics(
        self,
        db: AsyncSession,
        agent_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed performance metrics for a specific agent.

        Args:
            db: Database session
            agent_id: Agent ID
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Agent performance metrics or None if agent doesn't exist
        """
        # Get agent
        agent_query = select(Agent).where(Agent.id == agent_id)
        agent_result = await db.execute(agent_query)
        agent = agent_result.scalar_one_or_none()

        if not agent:
            return None

        # Get executions for this agent
        query = (
            select(Execution)
            .where(
                and_(
                    Execution.agent_id == agent_id,
                    Execution.started_at >= start_date,
                    Execution.started_at <= end_date,
                    Execution.started_at.isnot(None),
                )
            )
        )
        result = await db.execute(query)
        executions = result.scalars().all()

        if not executions:
            return {
                "agent_id": agent.id,
                "agent_name": agent.name,
                "metrics": {
                    "total_executions": 0,
                    "success_rate": 0.0,
                    "avg_duration_seconds": 0.0,
                    "min_duration_seconds": 0.0,
                    "max_duration_seconds": 0.0,
                    "p50_duration_seconds": 0.0,
                    "p95_duration_seconds": 0.0,
                    "p99_duration_seconds": 0.0,
                    "avg_tokens_per_execution": 0.0,
                    "total_cost": 0.0,
                    "uptime_percentage": 0.0,
                },
                "recent_failures": [],
            }

        # Calculate metrics
        total = len(executions)
        successful = sum(1 for e in executions if e.status == "completed")
        failed = sum(1 for e in executions if e.status == "failed")
        success_rate = successful / total if total > 0 else 0.0

        # Calculate duration statistics (only for completed executions)
        durations = [
            (e.completed_at - e.started_at).total_seconds()
            for e in executions
            if e.status == "completed"
            and e.completed_at
            and e.started_at
        ]

        if durations:
            durations_sorted = sorted(durations)
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            p50_duration = self._calculate_percentile(durations_sorted, 50)
            p95_duration = self._calculate_percentile(durations_sorted, 95)
            p99_duration = self._calculate_percentile(durations_sorted, 99)
        else:
            avg_duration = min_duration = max_duration = 0.0
            p50_duration = p95_duration = p99_duration = 0.0

        # Calculate token statistics
        completed_executions = [e for e in executions if e.status == "completed"]
        if completed_executions:
            total_tokens_sum = sum(e.total_tokens or 0 for e in completed_executions)
            avg_tokens = total_tokens_sum / len(completed_executions)
        else:
            avg_tokens = 0.0

        # Calculate total cost
        total_cost = sum(
            float(e.estimated_cost or Decimal("0.0"))
            for e in executions
        )

        # Calculate uptime (percentage of successful executions)
        uptime_percentage = success_rate * 100

        # Get recent failures
        recent_failures = []
        failed_executions = [e for e in executions if e.status == "failed"]
        failed_executions.sort(key=lambda e: e.started_at, reverse=True)

        for execution in failed_executions[:5]:  # Last 5 failures
            recent_failures.append({
                "execution_id": execution.id,
                "error_message": execution.error_message or "Unknown error",
                "timestamp": execution.started_at,
            })

        return {
            "agent_id": agent.id,
            "agent_name": agent.name,
            "metrics": {
                "total_executions": total,
                "success_rate": success_rate,
                "avg_duration_seconds": avg_duration,
                "min_duration_seconds": min_duration,
                "max_duration_seconds": max_duration,
                "p50_duration_seconds": p50_duration,
                "p95_duration_seconds": p95_duration,
                "p99_duration_seconds": p99_duration,
                "avg_tokens_per_execution": avg_tokens,
                "total_cost": total_cost,
                "uptime_percentage": uptime_percentage,
            },
            "recent_failures": recent_failures,
        }

    def _calculate_percentile(self, sorted_values: List[float], percentile: float) -> float:
        """
        Calculate percentile from sorted values.

        Args:
            sorted_values: List of sorted values
            percentile: Percentile to calculate (0-100)

        Returns:
            Percentile value
        """
        if not sorted_values:
            return 0.0

        index = (percentile / 100.0) * (len(sorted_values) - 1)
        lower = int(index)
        upper = min(lower + 1, len(sorted_values) - 1)
        weight = index - lower

        return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight

    async def get_system_performance_metrics(
        self,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Get overall system performance metrics.

        Args:
            db: Database session

        Returns:
            System-wide performance metrics
        """
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)

        # Count total agents
        total_agents_query = select(func.count(Agent.id))
        total_agents = await db.scalar(total_agents_query) or 0

        # Count active agents
        active_agents_query = select(func.count(Agent.id)).where(
            Agent.is_active == True
        )
        active_agents = await db.scalar(active_agents_query) or 0

        # Count total executions
        total_executions_query = select(func.count(Execution.id))
        total_executions = await db.scalar(total_executions_query) or 0

        # Count executions in last 24h
        executions_24h_query = select(func.count(Execution.id)).where(
            Execution.started_at >= yesterday
        )
        executions_24h = await db.scalar(executions_24h_query) or 0

        # Calculate success rate for last 24h
        if executions_24h > 0:
            successful_24h_query = select(func.count(Execution.id)).where(
                and_(
                    Execution.started_at >= yesterday,
                    Execution.status == "completed"
                )
            )
            successful_24h = await db.scalar(successful_24h_query) or 0
            success_rate_24h = successful_24h / executions_24h
        else:
            success_rate_24h = 0.0

        # Calculate average response time for last 24h
        executions_24h_query = (
            select(Execution.started_at, Execution.completed_at)
            .where(
                and_(
                    Execution.started_at >= yesterday,
                    Execution.status == "completed",
                    Execution.completed_at.isnot(None)
                )
            )
        )
        result = await db.execute(executions_24h_query)
        executions_24h_data = result.all()

        if executions_24h_data:
            durations = [
                (completed - started).total_seconds() * 1000  # Convert to ms
                for started, completed in executions_24h_data
            ]
            avg_response_time_ms = sum(durations) / len(durations)
        else:
            avg_response_time_ms = 0.0

        # Calculate uptime (time since first execution)
        first_execution_query = (
            select(Execution.created_at)
            .order_by(Execution.created_at)
            .limit(1)
        )
        first_execution_time = await db.scalar(first_execution_query)
        if first_execution_time:
            uptime_seconds = int((now - first_execution_time).total_seconds())
        else:
            uptime_seconds = 0

        # Placeholder values for database size and cache hit rate
        # These would typically come from database/cache monitoring
        database_size_mb = 0.0
        cache_hit_rate = 0.0

        return {
            "uptime_seconds": uptime_seconds,
            "total_agents": total_agents,
            "active_agents": active_agents,
            "total_executions": total_executions,
            "executions_last_24h": executions_24h,
            "success_rate_last_24h": success_rate_24h,
            "avg_response_time_ms": avg_response_time_ms,
            "database_size_mb": database_size_mb,
            "cache_hit_rate": cache_hit_rate,
        }

    async def get_cost_recommendations(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """
        Generate cost optimization recommendations.

        Args:
            db: Database session
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Cost recommendations with potential savings
        """
        # Get all executions in date range
        query = (
            select(Execution)
            .where(
                and_(
                    Execution.started_at >= start_date,
                    Execution.started_at <= end_date,
                    Execution.started_at.isnot(None),
                )
            )
        )
        result = await db.execute(query)
        executions = result.scalars().all()

        if not executions:
            return {
                "total_cost": 0.0,
                "potential_savings": 0.0,
                "recommendations": [],
            }

        # Calculate total cost
        total_cost = sum(
            float(e.estimated_cost or Decimal("0.0"))
            for e in executions
        )

        # Analyze for optimization opportunities
        recommendations = []
        potential_savings = 0.0

        # Future Enhancement: ML-based cost optimization recommendations
        # Potential features:
        # 1. Detect agents using expensive models (e.g., GPT-4) for simple tasks
        # 2. Identify agents with low max_tokens utilization (oversized configs)
        # 3. Flag high error rates indicating inefficient prompts
        # 4. Find redundant agent configurations that could be merged
        # 5. Suggest model downgrade opportunities based on task complexity
        #
        # This would require historical execution data analysis and
        # machine learning models to detect patterns and recommend optimizations.

        return {
            "total_cost": total_cost,
            "potential_savings": potential_savings,
            "recommendations": recommendations,
        }

    async def get_cost_projections(
        self,
        db: AsyncSession,
        projection_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Project future costs based on historical data.

        Args:
            db: Database session
            projection_days: Number of days to project

        Returns:
            Cost projections with trends
        """
        now = datetime.utcnow()
        lookback_days = min(projection_days, 30)  # Use up to 30 days of history
        lookback_date = now - timedelta(days=lookback_days)

        # Get recent executions
        query = (
            select(Execution)
            .where(
                and_(
                    Execution.started_at >= lookback_date,
                    Execution.started_at <= now,
                    Execution.started_at.isnot(None),
                )
            )
        )
        result = await db.execute(query)
        executions = result.scalars().all()

        if not executions:
            return {
                "current_daily_cost": 0.0,
                "projected_monthly_cost": 0.0,
                "trend": "stable",
                "trend_percentage": 0.0,
                "breakdown_by_agent": [],
            }

        # Calculate daily average cost
        total_cost = sum(
            float(e.estimated_cost or Decimal("0.0"))
            for e in executions
        )
        daily_cost = total_cost / lookback_days if lookback_days > 0 else 0.0

        # Project monthly cost
        projected_monthly_cost = daily_cost * 30

        # Determine trend (simplified - compare first half vs second half)
        midpoint = lookback_date + timedelta(days=lookback_days / 2)
        first_half = [e for e in executions if e.started_at < midpoint]
        second_half = [e for e in executions if e.started_at >= midpoint]

        first_half_cost = sum(
            float(e.estimated_cost or Decimal("0.0"))
            for e in first_half
        )
        second_half_cost = sum(
            float(e.estimated_cost or Decimal("0.0"))
            for e in second_half
        )

        if first_half_cost > 0:
            trend_percentage = ((second_half_cost - first_half_cost) / first_half_cost) * 100
            if trend_percentage > 10:
                trend = "increasing"
            elif trend_percentage < -10:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"
            trend_percentage = 0.0

        # Breakdown by agent
        agent_costs: Dict[int, Dict[str, Any]] = {}
        for execution in executions:
            if execution.agent_id not in agent_costs:
                agent_costs[execution.agent_id] = {
                    "cost": 0.0,
                    "agent_id": execution.agent_id,
                }
            agent_costs[execution.agent_id]["cost"] += float(
                execution.estimated_cost or Decimal("0.0")
            )

        # Get agent names and calculate projections
        breakdown_by_agent = []
        for agent_id, data in agent_costs.items():
            agent_query = select(Agent.name).where(Agent.id == agent_id)
            agent_result = await db.execute(agent_query)
            agent_name = agent_result.scalar_one_or_none() or f"Agent {agent_id}"

            agent_daily_cost = data["cost"] / lookback_days if lookback_days > 0 else 0.0
            agent_projected_cost = agent_daily_cost * 30

            breakdown_by_agent.append({
                "agent_id": agent_id,
                "agent_name": agent_name,
                "projected_cost": agent_projected_cost,
                "percentage_of_total": (
                    (agent_projected_cost / projected_monthly_cost * 100)
                    if projected_monthly_cost > 0
                    else 0.0
                ),
            })

        # Sort by projected cost (descending)
        breakdown_by_agent.sort(key=lambda x: x["projected_cost"], reverse=True)

        return {
            "current_daily_cost": daily_cost,
            "projected_monthly_cost": projected_monthly_cost,
            "trend": trend,
            "trend_percentage": trend_percentage,
            "breakdown_by_agent": breakdown_by_agent,
        }


# Singleton instance
analytics_service = AnalyticsService()
