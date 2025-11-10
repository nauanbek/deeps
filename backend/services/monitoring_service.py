"""Service layer for monitoring and analytics."""

from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import datetime, timedelta

from models.agent import Agent
from models.execution import Execution


class MonitoringService:
    """Service for managing monitoring and analytics operations."""

    async def get_dashboard_overview(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get high-level dashboard metrics.

        Args:
            db: Database session
            user_id: Optional user ID to filter by

        Returns:
            Dictionary containing:
                - total_agents: Total number of agents
                - total_executions: Total execution count
                - executions_today: Executions in last 24 hours
                - success_rate: Overall success rate percentage
                - total_tokens_used: Sum of all tokens used
                - estimated_total_cost: Sum of all costs
        """
        # Count total agents
        query = select(func.count(Agent.id))
        if user_id:
            query = query.where(Agent.created_by_id == user_id)
        total_agents = await db.scalar(query)

        # Count total executions
        query = select(func.count(Execution.id))
        if user_id:
            query = query.where(Execution.created_by_id == user_id)
        total_executions = await db.scalar(query)

        # Count executions today (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        query = select(func.count(Execution.id)).where(
            Execution.started_at >= yesterday
        )
        if user_id:
            query = query.where(Execution.created_by_id == user_id)
        executions_today = await db.scalar(query)

        # Calculate success rate
        success_rate = await self._calculate_success_rate(db, user_id)

        # Sum token usage
        query = select(func.sum(Execution.total_tokens))
        if user_id:
            query = query.where(Execution.created_by_id == user_id)
        total_tokens = await db.scalar(query) or 0

        # Sum costs
        query = select(func.sum(Execution.estimated_cost))
        if user_id:
            query = query.where(Execution.created_by_id == user_id)
        total_cost = await db.scalar(query) or 0.0

        return {
            "total_agents": total_agents or 0,
            "total_executions": total_executions or 0,
            "executions_today": executions_today or 0,
            "success_rate": success_rate,
            "total_tokens_used": total_tokens,
            "estimated_total_cost": float(total_cost),
        }

    async def _calculate_success_rate(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None
    ) -> float:
        """
        Calculate overall success rate.

        Args:
            db: Database session
            user_id: Optional user ID to filter by

        Returns:
            Success rate as a percentage (0-100)
        """
        # Count completed executions
        query = select(func.count(Execution.id)).where(
            Execution.status == "completed"
        )
        if user_id:
            query = query.where(Execution.created_by_id == user_id)
        completed = await db.scalar(query) or 0

        # Count total executions
        query = select(func.count(Execution.id))
        if user_id:
            query = query.where(Execution.created_by_id == user_id)
        total = await db.scalar(query) or 0

        if total == 0:
            return 0.0

        return (completed / total) * 100

    async def get_agent_health(
        self,
        db: AsyncSession,
        agent_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get health metrics for agents.

        Args:
            db: Database session
            agent_id: Optional agent ID to filter by specific agent

        Returns:
            List of dictionaries containing:
                - agent_id: Agent ID
                - agent_name: Agent name
                - total_executions: Total execution count
                - success_count: Successful execution count
                - error_count: Failed execution count
                - success_rate: Success rate percentage
                - avg_execution_time: Average execution time in seconds
                - last_execution_at: Last execution timestamp (ISO format)
        """
        # Build query to get agents
        if agent_id:
            agents_query = select(Agent).where(Agent.id == agent_id)
        else:
            agents_query = select(Agent).where(Agent.is_active == True)

        result = await db.execute(agents_query)
        agents = result.scalars().all()

        health_data = []
        for agent in agents:
            # Count executions
            total_query = select(func.count(Execution.id)).where(
                Execution.agent_id == agent.id
            )
            total = await db.scalar(total_query) or 0

            # Count successful executions
            success_query = select(func.count(Execution.id)).where(
                and_(
                    Execution.agent_id == agent.id,
                    Execution.status == "completed"
                )
            )
            success = await db.scalar(success_query) or 0

            # Count errors
            error_query = select(func.count(Execution.id)).where(
                and_(
                    Execution.agent_id == agent.id,
                    Execution.status == "failed"
                )
            )
            errors = await db.scalar(error_query) or 0

            # Calculate average execution time
            avg_time = await self._calculate_avg_execution_time(db, agent.id)

            # Get last execution time
            last_exec_query = (
                select(Execution.started_at)
                .where(Execution.agent_id == agent.id)
                .order_by(desc(Execution.started_at))
                .limit(1)
            )
            last_exec = await db.scalar(last_exec_query)

            health_data.append({
                "agent_id": agent.id,
                "agent_name": agent.name,
                "total_executions": total,
                "success_count": success,
                "error_count": errors,
                "success_rate": (success / total * 100) if total > 0 else 0.0,
                "avg_execution_time": avg_time,
                "last_execution_at": last_exec.isoformat() if last_exec else None,
            })

        return health_data

    async def _calculate_avg_execution_time(
        self,
        db: AsyncSession,
        agent_id: int
    ) -> float:
        """
        Calculate average execution time for an agent in seconds.

        Args:
            db: Database session
            agent_id: Agent ID

        Returns:
            Average execution time in seconds
        """
        # Get completed executions with both timestamps
        query = (
            select(Execution.started_at, Execution.completed_at)
            .where(
                and_(
                    Execution.agent_id == agent_id,
                    Execution.status == "completed",
                    Execution.completed_at.isnot(None)
                )
            )
        )
        result = await db.execute(query)
        executions = result.all()

        if not executions:
            return 0.0

        durations = [
            (completed - started).total_seconds()
            for started, completed in executions
        ]

        return sum(durations) / len(durations)

    async def get_execution_stats(
        self,
        db: AsyncSession,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get execution statistics for the last N days.

        Args:
            db: Database session
            days: Number of days to include in statistics

        Returns:
            Dictionary containing:
                - by_status: Dictionary of counts by status
                - period_days: Number of days included
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Count by status
        status_counts = {}
        for status in ["pending", "running", "completed", "failed", "cancelled"]:
            query = select(func.count(Execution.id)).where(
                and_(
                    Execution.status == status,
                    Execution.created_at >= cutoff_date
                )
            )
            count = await db.scalar(query) or 0
            status_counts[status] = count

        return {
            "by_status": status_counts,
            "period_days": days,
        }

    async def get_token_usage_summary(
        self,
        db: AsyncSession,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get token usage summary for the last N days.

        Args:
            db: Database session
            days: Number of days to include in summary

        Returns:
            Dictionary containing:
                - total_tokens: Total tokens used
                - prompt_tokens: Prompt tokens used
                - completion_tokens: Completion tokens used
                - estimated_cost: Estimated total cost
                - period_days: Number of days included
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query = select(
            func.sum(Execution.total_tokens),
            func.sum(Execution.prompt_tokens),
            func.sum(Execution.completion_tokens),
            func.sum(Execution.estimated_cost)
        ).where(Execution.started_at >= cutoff_date)

        result = await db.execute(query)
        row = result.first()

        return {
            "total_tokens": row[0] or 0,
            "prompt_tokens": row[1] or 0,
            "completion_tokens": row[2] or 0,
            "estimated_cost": float(row[3] or 0.0),
            "period_days": days,
        }

    async def get_recent_executions(
        self,
        db: AsyncSession,
        limit: int = 10
    ) -> List[Execution]:
        """
        Get most recent executions.

        Args:
            db: Database session
            limit: Maximum number of executions to return

        Returns:
            List of Execution instances ordered by most recent first
        """
        query = (
            select(Execution)
            .order_by(desc(Execution.created_at))
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_recent_errors(
        self,
        db: AsyncSession,
        limit: int = 10
    ) -> List[Execution]:
        """
        Get most recent failed executions.

        Args:
            db: Database session
            limit: Maximum number of errors to return

        Returns:
            List of failed Execution instances ordered by most recent first
        """
        query = (
            select(Execution)
            .where(Execution.status == "failed")
            .order_by(desc(Execution.created_at))
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())


# Singleton instance
monitoring_service = MonitoringService()
