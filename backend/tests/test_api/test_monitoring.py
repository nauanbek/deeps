"""Tests for monitoring API endpoints."""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent import Agent
from models.execution import Execution


class TestDashboardEndpoint:
    """Tests for dashboard endpoint."""

    @pytest.mark.asyncio
    async def test_get_dashboard_endpoint(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test GET /api/v1/monitoring/dashboard endpoint."""
        # Create test data
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

        # Make request
        response = client.get("/api/v1/monitoring/dashboard")

        assert response.status_code == 200
        data = response.json()

        assert data["total_agents"] == 1
        assert data["total_executions"] == 2
        assert data["executions_today"] == 2
        assert data["success_rate"] == 50.0
        assert data["total_tokens_used"] == 1500
        assert data["estimated_total_cost"] == 0.075

    @pytest.mark.asyncio
    async def test_get_dashboard_endpoint_empty(self, client: TestClient):
        """Test dashboard endpoint with no data."""
        response = client.get("/api/v1/monitoring/dashboard")

        assert response.status_code == 200
        data = response.json()

        assert data["total_agents"] == 0
        assert data["total_executions"] == 0
        assert data["executions_today"] == 0
        assert data["success_rate"] == 0.0
        assert data["total_tokens_used"] == 0
        assert data["estimated_total_cost"] == 0.0


class TestAgentHealthEndpoint:
    """Tests for agent health endpoint."""

    @pytest.mark.asyncio
    async def test_get_agent_health_endpoint(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test GET /api/v1/monitoring/agents/health endpoint."""
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

        # Make request
        response = client.get("/api/v1/monitoring/agents/health")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        agent_health = data[0]

        assert agent_health["agent_id"] == test_agent.id
        assert agent_health["agent_name"] == test_agent.name
        assert agent_health["total_executions"] == 2
        assert agent_health["success_count"] == 1
        assert agent_health["error_count"] == 1
        assert agent_health["success_rate"] == 50.0
        assert agent_health["avg_execution_time"] > 0
        assert agent_health["last_execution_at"] is not None

    @pytest.mark.asyncio
    async def test_get_agent_health_endpoint_with_agent_id(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test agent health endpoint with specific agent_id filter."""
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

        # Make request with agent_id filter
        response = client.get(
            f"/api/v1/monitoring/agents/health?agent_id={test_agent.id}"
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert data[0]["agent_id"] == test_agent.id

    @pytest.mark.asyncio
    async def test_get_agent_health_endpoint_empty(self, client: TestClient):
        """Test agent health endpoint with no agents."""
        response = client.get("/api/v1/monitoring/agents/health")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 0


class TestExecutionStatsEndpoint:
    """Tests for execution stats endpoint."""

    @pytest.mark.asyncio
    async def test_get_execution_stats_endpoint(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test GET /api/v1/monitoring/executions/stats endpoint."""
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

        # Make request
        response = client.get("/api/v1/monitoring/executions/stats")

        assert response.status_code == 200
        data = response.json()

        assert data["by_status"]["completed"] == 2
        assert data["by_status"]["failed"] == 1
        assert data["by_status"]["running"] == 1
        assert data["by_status"]["pending"] == 1
        assert data["by_status"]["cancelled"] == 0
        assert data["period_days"] == 7

    @pytest.mark.asyncio
    async def test_get_execution_stats_endpoint_with_custom_days(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test execution stats endpoint with custom days parameter."""
        now = datetime.utcnow()

        # Create recent execution (within 3 days)
        recent_execution = Execution(
            agent_id=test_agent.id,
            input_prompt="recent",
            status="completed",
            started_at=now - timedelta(days=2),
            created_at=now - timedelta(days=2),
            created_by_id=test_user_id
        )

        # Create old execution (outside 3 days)
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

        # Make request with days=3
        response = client.get("/api/v1/monitoring/executions/stats?days=3")

        assert response.status_code == 200
        data = response.json()

        # Should only count the recent execution
        assert data["by_status"]["completed"] == 1
        assert data["period_days"] == 3

    @pytest.mark.asyncio
    async def test_get_execution_stats_endpoint_validation(self, client: TestClient):
        """Test execution stats endpoint parameter validation."""
        # Test with invalid days (too large)
        response = client.get("/api/v1/monitoring/executions/stats?days=500")
        assert response.status_code == 422

        # Test with invalid days (too small)
        response = client.get("/api/v1/monitoring/executions/stats?days=0")
        assert response.status_code == 422


class TestTokenUsageEndpoint:
    """Tests for token usage endpoint."""

    @pytest.mark.asyncio
    async def test_get_token_usage_endpoint(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test GET /api/v1/monitoring/usage/tokens endpoint."""
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

        # Make request
        response = client.get("/api/v1/monitoring/usage/tokens")

        assert response.status_code == 200
        data = response.json()

        assert data["total_tokens"] == 3000
        assert data["prompt_tokens"] == 1800
        assert data["completion_tokens"] == 1200
        assert data["estimated_cost"] == 0.15
        assert data["period_days"] == 30

    @pytest.mark.asyncio
    async def test_get_token_usage_endpoint_with_custom_days(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test token usage endpoint with custom days parameter."""
        now = datetime.utcnow()

        # Create recent execution (within 7 days)
        recent_execution = Execution(
            agent_id=test_agent.id,
            input_prompt="recent",
            status="completed",
            started_at=now - timedelta(days=3),
            total_tokens=1000,
            estimated_cost=0.05,
            created_by_id=test_user_id
        )

        # Create old execution (outside 7 days)
        old_execution = Execution(
            agent_id=test_agent.id,
            input_prompt="old",
            status="completed",
            started_at=now - timedelta(days=10),
            total_tokens=2000,
            estimated_cost=0.10,
            created_by_id=test_user_id
        )

        db_session.add_all([recent_execution, old_execution])
        await db_session.commit()

        # Make request with days=7
        response = client.get("/api/v1/monitoring/usage/tokens?days=7")

        assert response.status_code == 200
        data = response.json()

        # Should only include recent execution
        assert data["total_tokens"] == 1000
        assert data["estimated_cost"] == 0.05
        assert data["period_days"] == 7

    @pytest.mark.asyncio
    async def test_get_token_usage_endpoint_validation(self, client: TestClient):
        """Test token usage endpoint parameter validation."""
        # Test with invalid days (too large)
        response = client.get("/api/v1/monitoring/usage/tokens?days=500")
        assert response.status_code == 422

        # Test with invalid days (too small)
        response = client.get("/api/v1/monitoring/usage/tokens?days=0")
        assert response.status_code == 422


class TestRecentExecutionsEndpoint:
    """Tests for recent executions endpoint."""

    @pytest.mark.asyncio
    async def test_get_recent_executions_endpoint(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test GET /api/v1/monitoring/executions/recent endpoint."""
        now = datetime.utcnow()

        # Create executions at different times
        for i in range(5):
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

        # Make request
        response = client.get("/api/v1/monitoring/executions/recent")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 5
        # Should be ordered by most recent first
        assert data[0]["input_prompt"] == "data0"
        assert data[4]["input_prompt"] == "data4"

    @pytest.mark.asyncio
    async def test_get_recent_executions_endpoint_with_limit(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test recent executions endpoint with custom limit."""
        now = datetime.utcnow()

        # Create 15 executions
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

        # Make request with limit=5
        response = client.get("/api/v1/monitoring/executions/recent?limit=5")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 5

    @pytest.mark.asyncio
    async def test_get_recent_executions_endpoint_validation(self, client: TestClient):
        """Test recent executions endpoint parameter validation."""
        # Test with invalid limit (too large)
        response = client.get("/api/v1/monitoring/executions/recent?limit=200")
        assert response.status_code == 422

        # Test with invalid limit (too small)
        response = client.get("/api/v1/monitoring/executions/recent?limit=0")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_recent_executions_endpoint_empty(self, client: TestClient):
        """Test recent executions endpoint with no data."""
        response = client.get("/api/v1/monitoring/executions/recent")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 0


class TestRecentErrorsEndpoint:
    """Tests for recent errors endpoint."""

    @pytest.mark.asyncio
    async def test_get_recent_errors_endpoint(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test GET /api/v1/monitoring/executions/errors endpoint."""
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

        # Make request
        response = client.get("/api/v1/monitoring/executions/errors")

        assert response.status_code == 200
        data = response.json()

        # Should only include failed executions
        assert len(data) == 5
        assert all(e["status"] == "failed" for e in data)
        # Should be ordered by most recent first
        assert data[0]["input_prompt"] == "data0"

    @pytest.mark.asyncio
    async def test_get_recent_errors_endpoint_with_limit(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_agent: Agent,
        test_user_id: int
    ):
        """Test recent errors endpoint with custom limit."""
        now = datetime.utcnow()

        # Create 10 failed executions
        for i in range(10):
            execution = Execution(
                agent_id=test_agent.id,
                input_prompt=f"data{i}",
                status="failed",
                started_at=now - timedelta(minutes=i),
                created_at=now - timedelta(minutes=i),
                created_by_id=test_user_id
            )
            db_session.add(execution)

        await db_session.commit()

        # Make request with limit=3
        response = client.get("/api/v1/monitoring/executions/errors?limit=3")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 3

    @pytest.mark.asyncio
    async def test_get_recent_errors_endpoint_validation(self, client: TestClient):
        """Test recent errors endpoint parameter validation."""
        # Test with invalid limit (too large)
        response = client.get("/api/v1/monitoring/executions/errors?limit=200")
        assert response.status_code == 422

        # Test with invalid limit (too small)
        response = client.get("/api/v1/monitoring/executions/errors?limit=0")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_recent_errors_endpoint_empty(self, client: TestClient):
        """Test recent errors endpoint with no errors."""
        response = client.get("/api/v1/monitoring/executions/errors")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 0
