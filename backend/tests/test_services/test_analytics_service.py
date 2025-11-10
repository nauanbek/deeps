"""Tests for analytics service."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent import Agent
from models.execution import Execution
from services.analytics_service import analytics_service


class TestExecutionTimeSeries:
    """Tests for execution time-series analytics."""

    @pytest.mark.asyncio
    async def test_get_execution_time_series_daily(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test time-series data with daily interval."""
        # Create executions across multiple days
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        two_days_ago = now - timedelta(days=2)

        executions = [
            # Two days ago: 1 successful, 1 failed
            Execution(
                agent_id=test_agent.id,
                input_prompt="test1",
                status="completed",
                started_at=two_days_ago,
                completed_at=two_days_ago + timedelta(seconds=10),
                total_tokens=1000,
                prompt_tokens=600,
                completion_tokens=400,
                estimated_cost=Decimal("0.05"),
                created_by_id=test_user_id
            ),
            Execution(
                agent_id=test_agent.id,
                input_prompt="test2",
                status="failed",
                started_at=two_days_ago,
                completed_at=two_days_ago + timedelta(seconds=5),
                total_tokens=500,
                prompt_tokens=300,
                completion_tokens=200,
                estimated_cost=Decimal("0.025"),
                created_by_id=test_user_id
            ),
            # Yesterday: 2 successful
            Execution(
                agent_id=test_agent.id,
                input_prompt="test3",
                status="completed",
                started_at=yesterday,
                completed_at=yesterday + timedelta(seconds=15),
                total_tokens=2000,
                prompt_tokens=1200,
                completion_tokens=800,
                estimated_cost=Decimal("0.10"),
                created_by_id=test_user_id
            ),
            Execution(
                agent_id=test_agent.id,
                input_prompt="test4",
                status="completed",
                started_at=yesterday,
                completed_at=yesterday + timedelta(seconds=20),
                total_tokens=1500,
                prompt_tokens=900,
                completion_tokens=600,
                estimated_cost=Decimal("0.075"),
                created_by_id=test_user_id
            ),
            # Today: 1 successful, 1 cancelled
            Execution(
                agent_id=test_agent.id,
                input_prompt="test5",
                status="completed",
                started_at=now,
                completed_at=now + timedelta(seconds=12),
                total_tokens=1200,
                prompt_tokens=700,
                completion_tokens=500,
                estimated_cost=Decimal("0.06"),
                created_by_id=test_user_id
            ),
            Execution(
                agent_id=test_agent.id,
                input_prompt="test6",
                status="cancelled",
                started_at=now,
                completed_at=now + timedelta(seconds=2),
                total_tokens=100,
                prompt_tokens=100,
                completion_tokens=0,
                estimated_cost=Decimal("0.005"),
                created_by_id=test_user_id
            ),
        ]

        db_session.add_all(executions)
        await db_session.commit()

        # Get time-series data
        start_date = two_days_ago - timedelta(hours=1)
        end_date = now + timedelta(hours=1)

        result = await analytics_service.get_execution_time_series(
            db_session,
            start_date=start_date,
            end_date=end_date,
            interval="day"
        )

        # Should have 3 days of data
        assert len(result) == 3

        # Check two days ago
        day_2 = result[0]
        assert day_2["total_executions"] == 2
        assert day_2["successful"] == 1
        assert day_2["failed"] == 1
        assert day_2["cancelled"] == 0
        assert day_2["total_tokens"] == 1500
        # Only successful executions are included in avg duration (only 1 completed with 10s)
        assert abs(day_2["avg_duration_seconds"] - 10.0) < 0.1

        # Check yesterday
        day_1 = result[1]
        assert day_1["total_executions"] == 2
        assert day_1["successful"] == 2
        assert day_1["failed"] == 0
        assert day_1["cancelled"] == 0
        assert day_1["total_tokens"] == 3500
        assert abs(day_1["avg_duration_seconds"] - 17.5) < 0.1  # (15 + 20) / 2

        # Check today
        day_0 = result[2]
        assert day_0["total_executions"] == 2
        assert day_0["successful"] == 1
        assert day_0["failed"] == 0
        assert day_0["cancelled"] == 1
        assert day_0["total_tokens"] == 1300

    @pytest.mark.asyncio
    async def test_get_execution_time_series_filtered_by_agent(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test time-series filtered by specific agent."""
        # Create another agent
        agent2 = Agent(
            name="Agent 2",
            description="Second agent",
            model_provider="openai",
            model_name="gpt-4",
            created_by_id=test_user_id,
            is_active=True
        )
        db_session.add(agent2)
        await db_session.commit()
        await db_session.refresh(agent2)

        now = datetime.utcnow()

        # Create executions for both agents
        executions = [
            Execution(
                agent_id=test_agent.id,
                input_prompt="test1",
                status="completed",
                started_at=now,
                completed_at=now + timedelta(seconds=10),
                total_tokens=1000,
                estimated_cost=Decimal("0.05"),
                created_by_id=test_user_id
            ),
            Execution(
                agent_id=agent2.id,
                input_prompt="test2",
                status="completed",
                started_at=now,
                completed_at=now + timedelta(seconds=10),
                total_tokens=2000,
                estimated_cost=Decimal("0.10"),
                created_by_id=test_user_id
            ),
        ]
        db_session.add_all(executions)
        await db_session.commit()

        # Get time-series filtered by test_agent
        result = await analytics_service.get_execution_time_series(
            db_session,
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(hours=1),
            interval="day",
            agent_id=test_agent.id
        )

        assert len(result) == 1
        assert result[0]["total_executions"] == 1
        assert result[0]["total_tokens"] == 1000

    @pytest.mark.asyncio
    async def test_get_execution_time_series_empty(self, db_session: AsyncSession):
        """Test time-series with no data."""
        now = datetime.utcnow()

        result = await analytics_service.get_execution_time_series(
            db_session,
            start_date=now - timedelta(days=7),
            end_date=now,
            interval="day"
        )

        assert result == []


class TestAgentUsageRankings:
    """Tests for agent usage rankings."""

    @pytest.mark.asyncio
    async def test_get_agent_usage_rankings(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test agent usage rankings."""
        # Create multiple agents
        agent2 = Agent(
            name="Agent 2",
            model_provider="openai",
            model_name="gpt-4",
            created_by_id=test_user_id,
            is_active=True
        )
        agent3 = Agent(
            name="Agent 3",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            created_by_id=test_user_id,
            is_active=True
        )
        db_session.add_all([agent2, agent3])
        await db_session.commit()
        await db_session.refresh(agent2)
        await db_session.refresh(agent3)

        now = datetime.utcnow()

        # Create executions with different usage patterns
        executions = [
            # Agent 1: 3 executions, 2 successful (66.7% success)
            Execution(
                agent_id=test_agent.id,
                input_prompt="test1",
                status="completed",
                started_at=now,
                completed_at=now + timedelta(seconds=10),
                total_tokens=1000,
                estimated_cost=Decimal("0.05"),
                created_by_id=test_user_id
            ),
            Execution(
                agent_id=test_agent.id,
                input_prompt="test2",
                status="completed",
                started_at=now,
                completed_at=now + timedelta(seconds=15),
                total_tokens=1500,
                estimated_cost=Decimal("0.075"),
                created_by_id=test_user_id
            ),
            Execution(
                agent_id=test_agent.id,
                input_prompt="test3",
                status="failed",
                started_at=now,
                completed_at=now + timedelta(seconds=5),
                total_tokens=500,
                estimated_cost=Decimal("0.025"),
                created_by_id=test_user_id
            ),
            # Agent 2: 5 executions, 5 successful (100% success)
            *[
                Execution(
                    agent_id=agent2.id,
                    input_prompt=f"test{i}",
                    status="completed",
                    started_at=now,
                    completed_at=now + timedelta(seconds=20),
                    total_tokens=2000,
                    estimated_cost=Decimal("0.10"),
                    created_by_id=test_user_id
                )
                for i in range(5)
            ],
            # Agent 3: 1 execution, 1 successful (100% success)
            Execution(
                agent_id=agent3.id,
                input_prompt="test",
                status="completed",
                started_at=now,
                completed_at=now + timedelta(seconds=8),
                total_tokens=800,
                estimated_cost=Decimal("0.04"),
                created_by_id=test_user_id
            ),
        ]
        db_session.add_all(executions)
        await db_session.commit()

        # Get rankings
        result = await analytics_service.get_agent_usage_rankings(
            db_session,
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(hours=1),
            limit=10
        )

        assert len(result) == 3

        # Agent 2 should be first (most executions)
        assert result[0]["agent_id"] == agent2.id
        assert result[0]["agent_name"] == "Agent 2"
        assert result[0]["execution_count"] == 5
        assert result[0]["success_rate"] == 1.0
        assert result[0]["total_tokens"] == 10000
        assert abs(result[0]["avg_duration_seconds"] - 20.0) < 0.1

        # Agent 1 should be second
        assert result[1]["agent_id"] == test_agent.id
        assert result[1]["execution_count"] == 3
        assert abs(result[1]["success_rate"] - 0.666) < 0.01

        # Agent 3 should be last
        assert result[2]["agent_id"] == agent3.id
        assert result[2]["execution_count"] == 1

    @pytest.mark.asyncio
    async def test_get_agent_usage_rankings_with_limit(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test agent rankings with limit."""
        # Create another agent
        agent2 = Agent(
            name="Agent 2",
            model_provider="openai",
            model_name="gpt-4",
            created_by_id=test_user_id,
            is_active=True
        )
        db_session.add(agent2)
        await db_session.commit()
        await db_session.refresh(agent2)

        now = datetime.utcnow()

        # Create executions
        executions = [
            Execution(
                agent_id=test_agent.id,
                input_prompt="test",
                status="completed",
                started_at=now,
                completed_at=now + timedelta(seconds=10),
                total_tokens=1000,
                estimated_cost=Decimal("0.05"),
                created_by_id=test_user_id
            ),
            Execution(
                agent_id=agent2.id,
                input_prompt="test",
                status="completed",
                started_at=now,
                completed_at=now + timedelta(seconds=10),
                total_tokens=1000,
                estimated_cost=Decimal("0.05"),
                created_by_id=test_user_id
            ),
        ]
        db_session.add_all(executions)
        await db_session.commit()

        # Get rankings with limit=1
        result = await analytics_service.get_agent_usage_rankings(
            db_session,
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(hours=1),
            limit=1
        )

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_agent_usage_rankings_empty(self, db_session: AsyncSession):
        """Test rankings with no executions."""
        now = datetime.utcnow()

        result = await analytics_service.get_agent_usage_rankings(
            db_session,
            start_date=now - timedelta(days=7),
            end_date=now,
            limit=10
        )

        assert result == []


class TestTokenUsageBreakdown:
    """Tests for token usage breakdown."""

    @pytest.mark.asyncio
    async def test_get_token_usage_breakdown_by_agent(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test token breakdown grouped by agent."""
        # Create another agent
        agent2 = Agent(
            name="Agent 2",
            model_provider="openai",
            model_name="gpt-4",
            created_by_id=test_user_id,
            is_active=True
        )
        db_session.add(agent2)
        await db_session.commit()
        await db_session.refresh(agent2)

        now = datetime.utcnow()

        # Create executions
        executions = [
            Execution(
                agent_id=test_agent.id,
                input_prompt="test1",
                status="completed",
                started_at=now,
                total_tokens=1500,
                prompt_tokens=900,
                completion_tokens=600,
                estimated_cost=Decimal("0.075"),
                created_by_id=test_user_id
            ),
            Execution(
                agent_id=test_agent.id,
                input_prompt="test2",
                status="completed",
                started_at=now,
                total_tokens=1000,
                prompt_tokens=600,
                completion_tokens=400,
                estimated_cost=Decimal("0.05"),
                created_by_id=test_user_id
            ),
            Execution(
                agent_id=agent2.id,
                input_prompt="test3",
                status="completed",
                started_at=now,
                total_tokens=2000,
                prompt_tokens=1200,
                completion_tokens=800,
                estimated_cost=Decimal("0.10"),
                created_by_id=test_user_id
            ),
        ]
        db_session.add_all(executions)
        await db_session.commit()

        # Get breakdown by agent
        result = await analytics_service.get_token_usage_breakdown(
            db_session,
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(hours=1),
            group_by="agent"
        )

        assert result["total_tokens"] == 4500
        assert abs(result["total_cost"] - 0.225) < 0.001

        assert len(result["breakdown"]) == 2

        # Find test_agent in breakdown
        agent1_data = next(
            (b for b in result["breakdown"] if b["group_key"] == test_agent.name),
            None
        )
        assert agent1_data is not None
        assert agent1_data["total_tokens"] == 2500
        assert agent1_data["prompt_tokens"] == 1500
        assert agent1_data["completion_tokens"] == 1000

        # Find agent2 in breakdown
        agent2_data = next(
            (b for b in result["breakdown"] if b["group_key"] == agent2.name),
            None
        )
        assert agent2_data is not None
        assert agent2_data["total_tokens"] == 2000

    @pytest.mark.asyncio
    async def test_get_token_usage_breakdown_by_model(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test token breakdown grouped by model."""
        # Create agent with different model
        agent2 = Agent(
            name="Agent 2",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            created_by_id=test_user_id,
            is_active=True
        )
        db_session.add(agent2)
        await db_session.commit()
        await db_session.refresh(agent2)

        now = datetime.utcnow()

        # Create executions
        executions = [
            Execution(
                agent_id=test_agent.id,  # gpt-4
                input_prompt="test1",
                status="completed",
                started_at=now,
                total_tokens=1000,
                prompt_tokens=600,
                completion_tokens=400,
                estimated_cost=Decimal("0.05"),
                created_by_id=test_user_id
            ),
            Execution(
                agent_id=agent2.id,  # claude
                input_prompt="test2",
                status="completed",
                started_at=now,
                total_tokens=2000,
                prompt_tokens=1200,
                completion_tokens=800,
                estimated_cost=Decimal("0.10"),
                created_by_id=test_user_id
            ),
        ]
        db_session.add_all(executions)
        await db_session.commit()

        # Get breakdown by model
        result = await analytics_service.get_token_usage_breakdown(
            db_session,
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(hours=1),
            group_by="model"
        )

        assert result["total_tokens"] == 3000
        assert len(result["breakdown"]) == 2

    @pytest.mark.asyncio
    async def test_get_token_usage_breakdown_empty(self, db_session: AsyncSession):
        """Test token breakdown with no data."""
        now = datetime.utcnow()

        result = await analytics_service.get_token_usage_breakdown(
            db_session,
            start_date=now - timedelta(days=7),
            end_date=now,
            group_by="agent"
        )

        assert result["total_tokens"] == 0
        assert result["total_cost"] == 0.0
        assert result["breakdown"] == []


class TestErrorAnalysis:
    """Tests for error analysis."""

    @pytest.mark.asyncio
    async def test_get_error_analysis(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test error pattern analysis."""
        now = datetime.utcnow()

        # Create executions with different errors
        executions = [
            # Rate limit errors
            Execution(
                agent_id=test_agent.id,
                input_prompt="test1",
                status="failed",
                started_at=now - timedelta(hours=2),
                error_message="Rate limit exceeded",
                created_by_id=test_user_id
            ),
            Execution(
                agent_id=test_agent.id,
                input_prompt="test2",
                status="failed",
                started_at=now - timedelta(hours=1),
                error_message="Rate limit exceeded",
                created_by_id=test_user_id
            ),
            Execution(
                agent_id=test_agent.id,
                input_prompt="test3",
                status="failed",
                started_at=now,
                error_message="Rate limit exceeded",
                created_by_id=test_user_id
            ),
            # Timeout errors
            Execution(
                agent_id=test_agent.id,
                input_prompt="test4",
                status="failed",
                started_at=now - timedelta(hours=1),
                error_message="Request timeout",
                created_by_id=test_user_id
            ),
            Execution(
                agent_id=test_agent.id,
                input_prompt="test5",
                status="failed",
                started_at=now,
                error_message="Request timeout",
                created_by_id=test_user_id
            ),
        ]
        db_session.add_all(executions)
        await db_session.commit()

        # Get error analysis
        result = await analytics_service.get_error_analysis(
            db_session,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(hours=1),
            limit=10
        )

        assert len(result) == 2

        # Rate limit should be first (most common)
        rate_limit_error = result[0]
        assert "Rate limit" in rate_limit_error["error_pattern"]
        assert rate_limit_error["count"] == 3
        assert test_agent.id in rate_limit_error["affected_agents"]

        # Timeout should be second
        timeout_error = result[1]
        assert "timeout" in timeout_error["error_pattern"]
        assert timeout_error["count"] == 2

    @pytest.mark.asyncio
    async def test_get_error_analysis_with_limit(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test error analysis with limit."""
        now = datetime.utcnow()

        # Create multiple error types
        executions = [
            Execution(
                agent_id=test_agent.id,
                input_prompt=f"test{i}",
                status="failed",
                started_at=now,
                error_message=f"Error type {i}",
                created_by_id=test_user_id
            )
            for i in range(5)
        ]
        db_session.add_all(executions)
        await db_session.commit()

        # Get analysis with limit=2
        result = await analytics_service.get_error_analysis(
            db_session,
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(hours=1),
            limit=2
        )

        assert len(result) <= 2

    @pytest.mark.asyncio
    async def test_get_error_analysis_empty(self, db_session: AsyncSession):
        """Test error analysis with no errors."""
        now = datetime.utcnow()

        result = await analytics_service.get_error_analysis(
            db_session,
            start_date=now - timedelta(days=7),
            end_date=now,
            limit=10
        )

        assert result == []


class TestAgentPerformanceMetrics:
    """Tests for agent performance metrics."""

    @pytest.mark.asyncio
    async def test_get_agent_performance_metrics(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test detailed agent performance metrics."""
        now = datetime.utcnow()

        # Create executions with varying durations
        executions = [
            Execution(
                agent_id=test_agent.id,
                input_prompt="test1",
                status="completed",
                started_at=now,
                completed_at=now + timedelta(seconds=10),  # 10s
                total_tokens=1000,
                estimated_cost=Decimal("0.05"),
                created_by_id=test_user_id
            ),
            Execution(
                agent_id=test_agent.id,
                input_prompt="test2",
                status="completed",
                started_at=now,
                completed_at=now + timedelta(seconds=20),  # 20s
                total_tokens=2000,
                estimated_cost=Decimal("0.10"),
                created_by_id=test_user_id
            ),
            Execution(
                agent_id=test_agent.id,
                input_prompt="test3",
                status="completed",
                started_at=now,
                completed_at=now + timedelta(seconds=30),  # 30s
                total_tokens=3000,
                estimated_cost=Decimal("0.15"),
                created_by_id=test_user_id
            ),
            Execution(
                agent_id=test_agent.id,
                input_prompt="test4",
                status="failed",
                started_at=now,
                error_message="Test error",
                created_by_id=test_user_id
            ),
        ]
        db_session.add_all(executions)
        await db_session.commit()

        # Get performance metrics
        result = await analytics_service.get_agent_performance_metrics(
            db_session,
            agent_id=test_agent.id,
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(hours=1)
        )

        assert result["agent_id"] == test_agent.id
        assert result["agent_name"] == test_agent.name

        metrics = result["metrics"]
        assert metrics["total_executions"] == 4
        assert metrics["success_rate"] == 0.75  # 3 out of 4
        assert abs(metrics["avg_duration_seconds"] - 20.0) < 0.1  # (10+20+30)/3
        assert metrics["min_duration_seconds"] == 10.0
        assert metrics["max_duration_seconds"] == 30.0
        assert metrics["p50_duration_seconds"] == 20.0  # median
        assert abs(metrics["avg_tokens_per_execution"] - 2000.0) < 0.1  # 6000/3
        assert abs(metrics["total_cost"] - 0.30) < 0.01

        # Check recent failures
        assert len(result["recent_failures"]) == 1
        assert result["recent_failures"][0]["error_message"] == "Test error"

    @pytest.mark.asyncio
    async def test_get_agent_performance_metrics_nonexistent_agent(
        self,
        db_session: AsyncSession
    ):
        """Test performance metrics for nonexistent agent."""
        now = datetime.utcnow()

        result = await analytics_service.get_agent_performance_metrics(
            db_session,
            agent_id=99999,
            start_date=now - timedelta(days=7),
            end_date=now
        )

        # Should return None or empty metrics
        assert result is None or result["metrics"]["total_executions"] == 0


class TestSystemPerformanceMetrics:
    """Tests for system-wide performance metrics."""

    @pytest.mark.asyncio
    async def test_get_system_performance_metrics(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test system performance metrics."""
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)

        # Create executions
        executions = [
            # Today
            Execution(
                agent_id=test_agent.id,
                input_prompt="test1",
                status="completed",
                started_at=now,
                completed_at=now + timedelta(seconds=10),
                created_by_id=test_user_id
            ),
            Execution(
                agent_id=test_agent.id,
                input_prompt="test2",
                status="completed",
                started_at=now,
                completed_at=now + timedelta(seconds=20),
                created_by_id=test_user_id
            ),
            # Yesterday
            Execution(
                agent_id=test_agent.id,
                input_prompt="test3",
                status="failed",
                started_at=yesterday,
                created_by_id=test_user_id
            ),
        ]
        db_session.add_all(executions)
        await db_session.commit()

        # Get system metrics
        result = await analytics_service.get_system_performance_metrics(db_session)

        assert result["total_agents"] == 1
        assert result["active_agents"] == 1
        assert result["total_executions"] == 3
        assert result["executions_last_24h"] == 2
        assert result["success_rate_last_24h"] == 1.0  # 2 out of 2 today
        assert result["uptime_seconds"] >= 0

    @pytest.mark.asyncio
    async def test_get_system_performance_metrics_empty(
        self,
        db_session: AsyncSession
    ):
        """Test system metrics with no data."""
        result = await analytics_service.get_system_performance_metrics(db_session)

        assert result["total_agents"] == 0
        assert result["active_agents"] == 0
        assert result["total_executions"] == 0


class TestCostRecommendations:
    """Tests for cost optimization recommendations."""

    @pytest.mark.asyncio
    async def test_get_cost_recommendations(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test cost optimization recommendations."""
        now = datetime.utcnow()

        # Create executions with high costs
        executions = [
            Execution(
                agent_id=test_agent.id,
                input_prompt="test" * 100,
                status="completed",
                started_at=now,
                total_tokens=4000,  # High token usage
                execution_params={"max_tokens": 8000},  # Using only 50% of max_tokens
                estimated_cost=Decimal("0.20"),
                created_by_id=test_user_id
            ),
        ]
        db_session.add_all(executions)
        await db_session.commit()

        # Get recommendations
        result = await analytics_service.get_cost_recommendations(
            db_session,
            start_date=now - timedelta(days=30),
            end_date=now + timedelta(hours=1)
        )

        assert "total_cost" in result
        assert "potential_savings" in result
        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)

    @pytest.mark.asyncio
    async def test_get_cost_recommendations_empty(self, db_session: AsyncSession):
        """Test cost recommendations with no data."""
        now = datetime.utcnow()

        result = await analytics_service.get_cost_recommendations(
            db_session,
            start_date=now - timedelta(days=30),
            end_date=now
        )

        assert result["total_cost"] == 0.0
        assert result["potential_savings"] == 0.0
        assert result["recommendations"] == []


class TestCostProjections:
    """Tests for cost projections."""

    @pytest.mark.asyncio
    async def test_get_cost_projections(
        self,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test cost projections based on historical data."""
        now = datetime.utcnow()

        # Create executions over past days
        executions = []
        for i in range(7):
            day = now - timedelta(days=i)
            executions.append(
                Execution(
                    agent_id=test_agent.id,
                    input_prompt=f"test{i}",
                    status="completed",
                    started_at=day,
                    estimated_cost=Decimal("1.00"),  # $1 per day
                    created_by_id=test_user_id
                )
            )
        db_session.add_all(executions)
        await db_session.commit()

        # Get projections
        result = await analytics_service.get_cost_projections(
            db_session,
            projection_days=30
        )

        assert result["current_daily_cost"] >= 0
        assert result["projected_monthly_cost"] >= 0
        assert result["trend"] in ["increasing", "decreasing", "stable"]
        assert "breakdown_by_agent" in result

    @pytest.mark.asyncio
    async def test_get_cost_projections_empty(self, db_session: AsyncSession):
        """Test cost projections with no historical data."""
        result = await analytics_service.get_cost_projections(
            db_session,
            projection_days=30
        )

        assert result["current_daily_cost"] == 0.0
        assert result["projected_monthly_cost"] == 0.0
        assert result["breakdown_by_agent"] == []
