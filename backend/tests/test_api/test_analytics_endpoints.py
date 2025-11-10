"""Tests for analytics API endpoints."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent import Agent
from models.execution import Execution


class TestTimeSeriesEndpoint:
    """Tests for time-series analytics endpoint."""

    @pytest.mark.asyncio
    async def test_get_execution_time_series_endpoint(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test GET /api/v1/analytics/executions/time-series endpoint."""
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)

        # Create executions
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
                agent_id=test_agent.id,
                input_prompt="test2",
                status="failed",
                started_at=yesterday,
                total_tokens=500,
                estimated_cost=Decimal("0.025"),
                created_by_id=test_user_id
            ),
        ]
        db_session.add_all(executions)
        await db_session.commit()

        # Make request
        response = client.get(
            "/api/v1/analytics/executions/time-series",
            params={
                "start_date": (now - timedelta(days=2)).isoformat(),
                "end_date": (now + timedelta(hours=1)).isoformat(),
                "interval": "day"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) >= 1

    @pytest.mark.asyncio
    async def test_get_execution_time_series_endpoint_with_agent_filter(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test time-series endpoint with agent filter."""
        now = datetime.utcnow()

        # Create execution
        execution = Execution(
            agent_id=test_agent.id,
            input_prompt="test",
            status="completed",
            started_at=now,
            total_tokens=1000,
            estimated_cost=Decimal("0.05"),
            created_by_id=test_user_id
        )
        db_session.add(execution)
        await db_session.commit()

        # Make request with agent filter
        response = client.get(
            "/api/v1/analytics/executions/time-series",
            params={
                "start_date": (now - timedelta(hours=1)).isoformat(),
                "end_date": (now + timedelta(hours=1)).isoformat(),
                "interval": "hour",
                "agent_id": test_agent.id
            }
        )

        assert response.status_code == 200


class TestAgentUsageEndpoint:
    """Tests for agent usage rankings endpoint."""

    @pytest.mark.asyncio
    async def test_get_agent_usage_endpoint(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test GET /api/v1/analytics/agents/usage endpoint."""
        now = datetime.utcnow()

        # Create executions
        executions = [
            Execution(
                agent_id=test_agent.id,
                input_prompt=f"test{i}",
                status="completed",
                started_at=now,
                completed_at=now + timedelta(seconds=10),
                total_tokens=1000,
                estimated_cost=Decimal("0.05"),
                created_by_id=test_user_id
            )
            for i in range(3)
        ]
        db_session.add_all(executions)
        await db_session.commit()

        # Make request
        response = client.get(
            "/api/v1/analytics/agents/usage",
            params={
                "start_date": (now - timedelta(hours=1)).isoformat(),
                "end_date": (now + timedelta(hours=1)).isoformat(),
                "limit": 10
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "rankings" in data
        assert len(data["rankings"]) == 1
        assert data["rankings"][0]["agent_id"] == test_agent.id
        assert data["rankings"][0]["execution_count"] == 3

    @pytest.mark.asyncio
    async def test_get_agent_usage_endpoint_empty(self, client: TestClient):
        """Test agent usage endpoint with no data."""
        now = datetime.utcnow()

        response = client.get(
            "/api/v1/analytics/agents/usage",
            params={
                "start_date": (now - timedelta(days=7)).isoformat(),
                "end_date": now.isoformat()
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rankings"] == []


class TestTokenUsageBreakdownEndpoint:
    """Tests for token usage breakdown endpoint."""

    @pytest.mark.asyncio
    async def test_get_token_usage_breakdown_endpoint(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test GET /api/v1/analytics/token-usage/breakdown endpoint."""
        now = datetime.utcnow()

        # Create executions
        executions = [
            Execution(
                agent_id=test_agent.id,
                input_prompt="test",
                status="completed",
                started_at=now,
                total_tokens=1500,
                prompt_tokens=900,
                completion_tokens=600,
                estimated_cost=Decimal("0.075"),
                created_by_id=test_user_id
            ),
        ]
        db_session.add_all(executions)
        await db_session.commit()

        # Make request
        response = client.get(
            "/api/v1/analytics/token-usage/breakdown",
            params={
                "start_date": (now - timedelta(hours=1)).isoformat(),
                "end_date": (now + timedelta(hours=1)).isoformat(),
                "group_by": "agent"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_tokens" in data
        assert "total_cost" in data
        assert "breakdown" in data
        assert data["total_tokens"] == 1500

    @pytest.mark.asyncio
    async def test_get_token_usage_breakdown_endpoint_by_model(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test token breakdown grouped by model."""
        now = datetime.utcnow()

        # Create execution
        execution = Execution(
            agent_id=test_agent.id,
            input_prompt="test",
            status="completed",
            started_at=now,
            total_tokens=1000,
            estimated_cost=Decimal("0.05"),
            created_by_id=test_user_id
        )
        db_session.add(execution)
        await db_session.commit()

        # Make request
        response = client.get(
            "/api/v1/analytics/token-usage/breakdown",
            params={
                "start_date": (now - timedelta(hours=1)).isoformat(),
                "end_date": (now + timedelta(hours=1)).isoformat(),
                "group_by": "model"
            }
        )

        assert response.status_code == 200


class TestErrorAnalysisEndpoint:
    """Tests for error analysis endpoint."""

    @pytest.mark.asyncio
    async def test_get_error_analysis_endpoint(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test GET /api/v1/analytics/error-analysis endpoint."""
        now = datetime.utcnow()

        # Create failed executions
        executions = [
            Execution(
                agent_id=test_agent.id,
                input_prompt=f"test{i}",
                status="failed",
                started_at=now,
                error_message="Rate limit exceeded",
                created_by_id=test_user_id
            )
            for i in range(3)
        ]
        db_session.add_all(executions)
        await db_session.commit()

        # Make request
        response = client.get(
            "/api/v1/analytics/error-analysis",
            params={
                "start_date": (now - timedelta(hours=1)).isoformat(),
                "end_date": (now + timedelta(hours=1)).isoformat(),
                "limit": 10
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "errors" in data
        assert len(data["errors"]) >= 1
        assert data["errors"][0]["count"] == 3

    @pytest.mark.asyncio
    async def test_get_error_analysis_endpoint_empty(self, client: TestClient):
        """Test error analysis endpoint with no errors."""
        now = datetime.utcnow()

        response = client.get(
            "/api/v1/analytics/error-analysis",
            params={
                "start_date": (now - timedelta(days=7)).isoformat(),
                "end_date": now.isoformat()
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["errors"] == []


class TestAgentPerformanceEndpoint:
    """Tests for agent performance metrics endpoint."""

    @pytest.mark.asyncio
    async def test_get_agent_performance_endpoint(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test GET /api/v1/analytics/performance/agents/{agent_id} endpoint."""
        now = datetime.utcnow()

        # Create executions
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
                agent_id=test_agent.id,
                input_prompt="test2",
                status="failed",
                started_at=now,
                error_message="Test error",
                created_by_id=test_user_id
            ),
        ]
        db_session.add_all(executions)
        await db_session.commit()

        # Make request
        response = client.get(
            f"/api/v1/analytics/performance/agents/{test_agent.id}",
            params={
                "start_date": (now - timedelta(hours=1)).isoformat(),
                "end_date": (now + timedelta(hours=1)).isoformat()
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == test_agent.id
        assert "metrics" in data
        assert data["metrics"]["total_executions"] == 2
        assert "recent_failures" in data

    @pytest.mark.asyncio
    async def test_get_agent_performance_endpoint_nonexistent(
        self,
        client: TestClient
    ):
        """Test performance endpoint for nonexistent agent."""
        now = datetime.utcnow()

        response = client.get(
            "/api/v1/analytics/performance/agents/99999",
            params={
                "start_date": (now - timedelta(days=7)).isoformat(),
                "end_date": now.isoformat()
            }
        )

        # Should return 404 for nonexistent agent
        assert response.status_code == 404


class TestSystemPerformanceEndpoint:
    """Tests for system performance metrics endpoint."""

    @pytest.mark.asyncio
    async def test_get_system_performance_endpoint(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test GET /api/v1/analytics/performance/system endpoint."""
        now = datetime.utcnow()

        # Create execution
        execution = Execution(
            agent_id=test_agent.id,
            input_prompt="test",
            status="completed",
            started_at=now,
            created_by_id=test_user_id
        )
        db_session.add(execution)
        await db_session.commit()

        # Make request
        response = client.get("/api/v1/analytics/performance/system")

        assert response.status_code == 200
        data = response.json()
        assert "total_agents" in data
        assert "total_executions" in data
        assert "uptime_seconds" in data

    @pytest.mark.asyncio
    async def test_get_system_performance_endpoint_empty(self, client: TestClient):
        """Test system performance endpoint with no data."""
        response = client.get("/api/v1/analytics/performance/system")

        assert response.status_code == 200
        data = response.json()
        assert data["total_agents"] == 0
        assert data["total_executions"] == 0


class TestCostRecommendationsEndpoint:
    """Tests for cost recommendations endpoint."""

    @pytest.mark.asyncio
    async def test_get_cost_recommendations_endpoint(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test GET /api/v1/analytics/cost/recommendations endpoint."""
        now = datetime.utcnow()

        # Create execution
        execution = Execution(
            agent_id=test_agent.id,
            input_prompt="test",
            status="completed",
            started_at=now,
            total_tokens=1000,
            estimated_cost=Decimal("0.05"),
            created_by_id=test_user_id
        )
        db_session.add(execution)
        await db_session.commit()

        # Make request
        response = client.get(
            "/api/v1/analytics/cost/recommendations",
            params={
                "start_date": (now - timedelta(days=30)).isoformat(),
                "end_date": now.isoformat()
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_cost" in data
        assert "potential_savings" in data
        assert "recommendations" in data

    @pytest.mark.asyncio
    async def test_get_cost_recommendations_endpoint_empty(self, client: TestClient):
        """Test cost recommendations endpoint with no data."""
        now = datetime.utcnow()

        response = client.get(
            "/api/v1/analytics/cost/recommendations",
            params={
                "start_date": (now - timedelta(days=30)).isoformat(),
                "end_date": now.isoformat()
            }
        )

        assert response.status_code == 200


class TestCostProjectionsEndpoint:
    """Tests for cost projections endpoint."""

    @pytest.mark.asyncio
    async def test_get_cost_projections_endpoint(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test GET /api/v1/analytics/cost/projections endpoint."""
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
                    estimated_cost=Decimal("1.00"),
                    created_by_id=test_user_id
                )
            )
        db_session.add_all(executions)
        await db_session.commit()

        # Make request
        response = client.get(
            "/api/v1/analytics/cost/projections",
            params={"projection_days": 30}
        )

        assert response.status_code == 200
        data = response.json()
        assert "current_daily_cost" in data
        assert "projected_monthly_cost" in data
        assert "trend" in data
        assert "breakdown_by_agent" in data

    @pytest.mark.asyncio
    async def test_get_cost_projections_endpoint_empty(self, client: TestClient):
        """Test cost projections endpoint with no data."""
        response = client.get("/api/v1/analytics/cost/projections")

        assert response.status_code == 200
        data = response.json()
        assert data["current_daily_cost"] == 0.0
        assert data["projected_monthly_cost"] == 0.0
