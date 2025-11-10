"""Tests for monitoring service."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent import Agent
from models.execution import Execution
from services.monitoring_service import monitoring_service


class TestDashboardOverview:
    """Tests for dashboard overview metrics."""

    @pytest.mark.asyncio
    async def test_get_dashboard_overview(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test getting dashboard overview with data."""
        # Create test executions
        execution1 = Execution(
            agent_id=test_agent.id,
            input_prompt="data",
            status="completed",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            total_tokens=1000,
            prompt_tokens=600,
            completion_tokens=400,
            estimated_cost=0.05,
            created_by_id=test_user_id
        )
        execution2 = Execution(
            agent_id=test_agent.id,
            input_prompt="data2",
            status="failed",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            total_tokens=500,
            prompt_tokens=300,
            completion_tokens=200,
            estimated_cost=0.025,
            created_by_id=test_user_id
        )

        db_session.add_all([execution1, execution2])
        await db_session.commit()

        # Get dashboard overview
        result = await monitoring_service.get_dashboard_overview(db_session)

        assert result["total_agents"] == 1
        assert result["total_executions"] == 2
        assert result["executions_today"] == 2  # Both created today
        assert result["success_rate"] == 50.0  # 1 out of 2 succeeded
        assert result["total_tokens_used"] == 1500
        assert result["estimated_total_cost"] == 0.075

    @pytest.mark.asyncio
    async def test_get_dashboard_overview_no_data(self, db_session: AsyncSession):
        """Test dashboard overview with no data."""
        result = await monitoring_service.get_dashboard_overview(db_session)

        assert result["total_agents"] == 0
        assert result["total_executions"] == 0
        assert result["executions_today"] == 0
        assert result["success_rate"] == 0.0
        assert result["total_tokens_used"] == 0
        assert result["estimated_total_cost"] == 0.0

    @pytest.mark.asyncio
    async def test_get_dashboard_overview_with_user_filter(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test dashboard overview filtered by user."""
        # Create another agent by a different user
        other_agent = Agent(
            name="Other Agent",
            description="Other user's agent",
            model_provider="openai",
            model_name="gpt-4",
            system_prompt="You are helpful",
            created_by_id=test_user_id + 1,  # Different user
            is_active=True
        )
        db_session.add(other_agent)
        await db_session.commit()
        await db_session.refresh(other_agent)

        # Create executions for both agents
        execution1 = Execution(
            agent_id=test_agent.id,
            input_prompt="data",
            status="completed",
            started_at=datetime.utcnow(),
            created_by_id=test_user_id
        )
        execution2 = Execution(
            agent_id=other_agent.id,
            input_prompt="data2",
            status="completed",
            started_at=datetime.utcnow(),
            created_by_id=test_user_id + 1
        )

        db_session.add_all([execution1, execution2])
        await db_session.commit()

        # Get dashboard for specific user
        result = await monitoring_service.get_dashboard_overview(
            db_session,
            user_id=test_user_id
        )

        # Should only count the first user's data
        assert result["total_agents"] == 1
        assert result["total_executions"] == 1


class TestAgentHealth:
    """Tests for agent health metrics."""

    @pytest.mark.asyncio
    async def test_get_agent_health_all_agents(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test getting health for all agents."""
        # Create test executions
        execution1 = Execution(
            agent_id=test_agent.id,
            input_prompt="data",
            status="completed",
            started_at=datetime.utcnow() - timedelta(seconds=10),
            completed_at=datetime.utcnow(),
            created_by_id=test_user_id
        )
        execution2 = Execution(
            agent_id=test_agent.id,
            input_prompt="data2",
            status="failed",
            started_at=datetime.utcnow() - timedelta(seconds=5),
            completed_at=datetime.utcnow(),
            created_by_id=test_user_id
        )

        db_session.add_all([execution1, execution2])
        await db_session.commit()

        # Get health metrics
        health_data = await monitoring_service.get_agent_health(db_session)

        assert len(health_data) == 1
        agent_health = health_data[0]

        assert agent_health["agent_id"] == test_agent.id
        assert agent_health["agent_name"] == test_agent.name
        assert agent_health["total_executions"] == 2
        assert agent_health["success_count"] == 1
        assert agent_health["error_count"] == 1
        assert agent_health["success_rate"] == 50.0
        assert agent_health["avg_execution_time"] > 0
        assert agent_health["last_execution_at"] is not None

    @pytest.mark.asyncio
    async def test_get_agent_health_single_agent(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test getting health for a specific agent."""
        # Create another agent
        other_agent = Agent(
            name="Other Agent",
            description="Another agent",
            model_provider="openai",
            model_name="gpt-4",
            system_prompt="You are helpful",
            created_by_id=test_user_id,
            is_active=True
        )
        db_session.add(other_agent)
        await db_session.commit()
        await db_session.refresh(other_agent)

        # Create executions for both
        execution1 = Execution(
            agent_id=test_agent.id,
            input_prompt="data",
            status="completed",
            started_at=datetime.utcnow(),
            created_by_id=test_user_id
        )
        execution2 = Execution(
            agent_id=other_agent.id,
            input_prompt="data2",
            status="completed",
            started_at=datetime.utcnow(),
            created_by_id=test_user_id
        )

        db_session.add_all([execution1, execution2])
        await db_session.commit()

        # Get health for specific agent
        health_data = await monitoring_service.get_agent_health(
            db_session,
            agent_id=test_agent.id
        )

        assert len(health_data) == 1
        assert health_data[0]["agent_id"] == test_agent.id

    @pytest.mark.asyncio
    async def test_calculate_success_rate(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test success rate calculation."""
        # Create 3 completed and 1 failed execution
        for i in range(3):
            execution = Execution(
                agent_id=test_agent.id,
                input_prompt=f"data{i}",
                status="completed",
                started_at=datetime.utcnow(),
                created_by_id=test_user_id
            )
            db_session.add(execution)

        failed_execution = Execution(
            agent_id=test_agent.id,
            input_prompt="failed",
            status="failed",
            started_at=datetime.utcnow(),
            created_by_id=test_user_id
        )
        db_session.add(failed_execution)
        await db_session.commit()

        # Calculate success rate
        success_rate = await monitoring_service._calculate_success_rate(db_session)

        # 3 out of 4 = 75%
        assert success_rate == 75.0

    @pytest.mark.asyncio
    async def test_calculate_average_execution_time(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test average execution time calculation."""
        now = datetime.utcnow()

        # Create executions with known durations
        execution1 = Execution(
            agent_id=test_agent.id,
            input_prompt="data1",
            status="completed",
            started_at=now - timedelta(seconds=20),
            completed_at=now - timedelta(seconds=10),  # 10 seconds
            created_by_id=test_user_id
        )
        execution2 = Execution(
            agent_id=test_agent.id,
            input_prompt="data2",
            status="completed",
            started_at=now - timedelta(seconds=30),
            completed_at=now,  # 30 seconds
            created_by_id=test_user_id
        )

        db_session.add_all([execution1, execution2])
        await db_session.commit()

        # Calculate average
        avg_time = await monitoring_service._calculate_avg_execution_time(
            db_session,
            test_agent.id
        )

        # Average of 10 and 30 is 20
        assert avg_time == 20.0

    @pytest.mark.asyncio
    async def test_agent_health_no_executions(
        self,
        db_session: AsyncSession,
        test_agent: Agent
    ):
        """Test agent health when there are no executions."""
        health_data = await monitoring_service.get_agent_health(db_session)

        assert len(health_data) == 1
        agent_health = health_data[0]

        assert agent_health["total_executions"] == 0
        assert agent_health["success_count"] == 0
        assert agent_health["error_count"] == 0
        assert agent_health["success_rate"] == 0.0
        assert agent_health["avg_execution_time"] == 0.0
        assert agent_health["last_execution_at"] is None


class TestExecutionStatistics:
    """Tests for execution statistics."""

    @pytest.mark.asyncio
    async def test_get_execution_stats_by_status(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test execution stats grouped by status."""
        # Create executions with different statuses
        statuses = ["completed", "completed", "failed", "running", "pending"]

        for status in statuses:
            execution = Execution(
                agent_id=test_agent.id,
                input_prompt="data",
                status=status,
                started_at=datetime.utcnow(),
                created_by_id=test_user_id
            )
            db_session.add(execution)

        await db_session.commit()

        # Get stats
        stats = await monitoring_service.get_execution_stats(db_session, days=7)

        assert stats["by_status"]["completed"] == 2
        assert stats["by_status"]["failed"] == 1
        assert stats["by_status"]["running"] == 1
        assert stats["by_status"]["pending"] == 1
        assert stats["by_status"]["cancelled"] == 0
        assert stats["period_days"] == 7

    @pytest.mark.asyncio
    async def test_get_execution_stats_by_date_range(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test execution stats filtered by date range."""
        now = datetime.utcnow()

        # Create execution within range (2 days ago)
        recent_execution = Execution(
            agent_id=test_agent.id,
            input_prompt="recent",
            status="completed",
            started_at=now - timedelta(days=2),
            created_at=now - timedelta(days=2),
            created_by_id=test_user_id
        )

        # Create execution outside range (10 days ago)
        old_execution = Execution(
            agent_id=test_agent.id,
            input_prompt="old",
            status="completed",
            started_at=now - timedelta(days=10),
            created_at=now - timedelta(days=10),
            created_by_id=test_user_id
        )

        db_session.add_all([recent_execution, old_execution])
        await db_session.commit()

        # Get stats for last 7 days
        stats = await monitoring_service.get_execution_stats(db_session, days=7)

        # Should only count the recent execution
        assert stats["by_status"]["completed"] == 1

    @pytest.mark.asyncio
    async def test_get_total_executions(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test getting total execution count."""
        # Create multiple executions
        for i in range(5):
            execution = Execution(
                agent_id=test_agent.id,
                input_prompt=f"data{i}",
                status="completed",
                started_at=datetime.utcnow(),
                created_by_id=test_user_id
            )
            db_session.add(execution)

        await db_session.commit()

        # Get dashboard (which includes total)
        result = await monitoring_service.get_dashboard_overview(db_session)

        assert result["total_executions"] == 5

    @pytest.mark.asyncio
    async def test_get_executions_by_agent(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test getting executions grouped by agent."""
        # Create another agent
        other_agent = Agent(
            name="Other Agent",
            description="Another agent",
            model_provider="openai",
            model_name="gpt-4",
            system_prompt="You are helpful",
            created_by_id=test_user_id,
            is_active=True
        )
        db_session.add(other_agent)
        await db_session.commit()
        await db_session.refresh(other_agent)

        # Create executions for both agents
        for agent in [test_agent, other_agent]:
            for i in range(2):
                execution = Execution(
                    agent_id=agent.id,
                    input_prompt=f"data{i}",
                    status="completed",
                    started_at=datetime.utcnow(),
                    created_by_id=test_user_id
                )
                db_session.add(execution)

        await db_session.commit()

        # Get health for all agents
        health_data = await monitoring_service.get_agent_health(db_session)

        assert len(health_data) == 2
        assert all(h["total_executions"] == 2 for h in health_data)


class TestUsageAnalytics:
    """Tests for token usage and cost analytics."""

    @pytest.mark.asyncio
    async def test_get_token_usage_summary(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test token usage summary."""
        # Create executions with token usage
        execution1 = Execution(
            agent_id=test_agent.id,
            input_prompt="data1",
            status="completed",
            started_at=datetime.utcnow(),
            total_tokens=1000,
            prompt_tokens=600,
            completion_tokens=400,
            estimated_cost=0.05,
            created_by_id=test_user_id
        )
        execution2 = Execution(
            agent_id=test_agent.id,
            input_prompt="data2",
            status="completed",
            started_at=datetime.utcnow(),
            total_tokens=2000,
            prompt_tokens=1200,
            completion_tokens=800,
            estimated_cost=0.10,
            created_by_id=test_user_id
        )

        db_session.add_all([execution1, execution2])
        await db_session.commit()

        # Get usage summary
        usage = await monitoring_service.get_token_usage_summary(db_session, days=30)

        assert usage["total_tokens"] == 3000
        assert usage["prompt_tokens"] == 1800
        assert usage["completion_tokens"] == 1200
        assert usage["estimated_cost"] == 0.15
        assert usage["period_days"] == 30

    @pytest.mark.asyncio
    async def test_get_cost_summary(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test cost summary calculation."""
        # Create executions with costs
        costs = [0.05, 0.10, 0.15, 0.20]

        for cost in costs:
            execution = Execution(
                agent_id=test_agent.id,
                input_prompt="data",
                status="completed",
                started_at=datetime.utcnow(),
                estimated_cost=cost,
                created_by_id=test_user_id
            )
            db_session.add(execution)

        await db_session.commit()

        # Get cost from dashboard
        result = await monitoring_service.get_dashboard_overview(db_session)

        # Sum should be 0.50
        assert result["estimated_total_cost"] == 0.50

    @pytest.mark.asyncio
    async def test_get_usage_by_agent(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test usage metrics by agent via health endpoint."""
        # Create executions with varying token usage
        execution1 = Execution(
            agent_id=test_agent.id,
            input_prompt="data1",
            status="completed",
            started_at=datetime.utcnow(),
            total_tokens=1000,
            created_by_id=test_user_id
        )
        execution2 = Execution(
            agent_id=test_agent.id,
            input_prompt="data2",
            status="completed",
            started_at=datetime.utcnow(),
            total_tokens=2000,
            created_by_id=test_user_id
        )

        db_session.add_all([execution1, execution2])
        await db_session.commit()

        # Get health metrics
        health_data = await monitoring_service.get_agent_health(db_session)

        assert len(health_data) == 1
        assert health_data[0]["total_executions"] == 2

    @pytest.mark.asyncio
    async def test_get_usage_by_time_period(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test usage filtered by time period."""
        now = datetime.utcnow()

        # Create recent execution (within 30 days)
        recent_execution = Execution(
            agent_id=test_agent.id,
            input_prompt="recent",
            status="completed",
            started_at=now - timedelta(days=15),
            total_tokens=1000,
            estimated_cost=0.05,
            created_by_id=test_user_id
        )

        # Create old execution (outside 30 days)
        old_execution = Execution(
            agent_id=test_agent.id,
            input_prompt="old",
            status="completed",
            started_at=now - timedelta(days=45),
            total_tokens=2000,
            estimated_cost=0.10,
            created_by_id=test_user_id
        )

        db_session.add_all([recent_execution, old_execution])
        await db_session.commit()

        # Get usage for last 30 days
        usage = await monitoring_service.get_token_usage_summary(db_session, days=30)

        # Should only include recent execution
        assert usage["total_tokens"] == 1000
        assert usage["estimated_cost"] == 0.05


class TestRecentActivity:
    """Tests for recent activity endpoints."""

    @pytest.mark.asyncio
    async def test_get_recent_executions(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test getting recent executions."""
        now = datetime.utcnow()

        # Create executions at different times
        for i in range(15):
            execution = Execution(
                agent_id=test_agent.id,
                input_prompt=f"data{i}",
                status="completed",
                started_at=now - timedelta(minutes=i),
                created_at=now - timedelta(minutes=i),
                created_by_id=test_user_id
            )
            db_session.add(execution)

        await db_session.commit()

        # Get recent executions (limit 10)
        recent = await monitoring_service.get_recent_executions(db_session, limit=10)

        assert len(recent) == 10
        # Should be ordered by most recent first
        assert recent[0].input_prompt == "data0"
        assert recent[9].input_prompt == "data9"

    @pytest.mark.asyncio
    async def test_get_recent_errors(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test getting recent failed executions."""
        now = datetime.utcnow()

        # Create mix of successful and failed executions
        for i in range(10):
            status = "failed" if i % 2 == 0 else "completed"
            execution = Execution(
                agent_id=test_agent.id,
                input_prompt=f"data{i}",
                status=status,
                started_at=now - timedelta(minutes=i),
                created_at=now - timedelta(minutes=i),
                created_by_id=test_user_id
            )
            db_session.add(execution)

        await db_session.commit()

        # Get recent errors
        errors = await monitoring_service.get_recent_errors(db_session, limit=10)

        # Should only include failed executions
        assert len(errors) == 5
        assert all(e.status == "failed" for e in errors)
        # Should be ordered by most recent first
        assert errors[0].input_prompt == "data0"

    @pytest.mark.asyncio
    async def test_get_recent_executions_empty(self, db_session: AsyncSession):
        """Test getting recent executions when none exist."""
        recent = await monitoring_service.get_recent_executions(db_session, limit=10)

        assert len(recent) == 0

    @pytest.mark.asyncio
    async def test_get_recent_errors_empty(self, db_session: AsyncSession):
        """Test getting recent errors when none exist."""
        errors = await monitoring_service.get_recent_errors(db_session, limit=10)

        assert len(errors) == 0
