"""
Tests for Execution API endpoints.

Tests cover:
- POST /api/v1/executions (create execution)
- POST /api/v1/executions/{id}/start (start execution)
- GET /api/v1/executions/{id} (get execution)
- GET /api/v1/executions (list executions)
- POST /api/v1/executions/{id}/cancel (cancel execution)
- GET /api/v1/executions/{id}/traces (get traces)
- WebSocket /api/v1/executions/{id}/stream (stream execution)
"""

import asyncio
import json

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent import Agent
from models.execution import Execution, Trace
from models.user import User


@pytest.mark.asyncio
class TestExecutionAPIEndpoints:
    """Test suite for Execution API endpoints."""

    async def test_create_execution_endpoint(
        self, client: TestClient, db_session: AsyncSession, test_user: User
    ):
        """Test POST /api/v1/executions."""
        # Create agent
        agent = Agent(
            name="Test Agent",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
            created_by_id=test_user.id,
        )
        db_session.add(agent)
        await db_session.commit()
        await db_session.refresh(agent)

        # Create execution via API
        response = client.post(
            "/api/v1/executions/",
            json={"agent_id": agent.id, "prompt": "Test prompt"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["agent_id"] == agent.id
        assert data["input_prompt"] == "Test prompt"
        assert data["status"] == "pending"
        assert "id" in data

    async def test_create_execution_invalid_agent(
        self, client: TestClient, db_session: AsyncSession
    ):
        """Test creating execution with invalid agent ID."""
        response = client.post(
            "/api/v1/executions/",
            json={"agent_id": 999999, "prompt": "Test"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    async def test_get_execution_endpoint(
        self, client: TestClient, db_session: AsyncSession, test_user: User
    ):
        """Test GET /api/v1/executions/{id}."""
        # Create agent
        agent = Agent(
            name="Test Agent",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
            created_by_id=test_user.id,
        )
        db_session.add(agent)
        await db_session.commit()
        await db_session.refresh(agent)

        # Create execution
        execution = Execution(
            agent_id=agent.id,
            input_prompt="Test prompt",
            status="pending",
            created_by_id=test_user.id,
        )
        db_session.add(execution)
        await db_session.commit()
        await db_session.refresh(execution)

        # Get execution via API
        response = client.get(f"/api/v1/executions/{execution.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == execution.id
        assert data["agent_id"] == agent.id
        assert data["input_prompt"] == "Test prompt"

    async def test_get_execution_not_found(
        self, client: TestClient, db_session: AsyncSession
    ):
        """Test getting non-existent execution."""
        response = client.get("/api/v1/executions/999999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_list_executions_endpoint(
        self, client: TestClient, db_session: AsyncSession, test_user: User
    ):
        """Test GET /api/v1/executions."""
        # Create agent
        agent = Agent(
            name="Test Agent",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
            created_by_id=test_user.id,
        )
        db_session.add(agent)
        await db_session.commit()
        await db_session.refresh(agent)

        # Create executions
        exec1 = Execution(
            agent_id=agent.id, input_prompt="Test 1", created_by_id=test_user.id
        )
        exec2 = Execution(
            agent_id=agent.id, input_prompt="Test 2", created_by_id=test_user.id
        )
        db_session.add_all([exec1, exec2])
        await db_session.commit()

        # List executions
        response = client.get("/api/v1/executions/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

    async def test_list_executions_with_filters(
        self, client: TestClient, db_session: AsyncSession, test_user: User
    ):
        """Test listing executions with filters."""
        # Create agents
        agent1 = Agent(
            name="Agent 1",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
            created_by_id=test_user.id,
        )
        agent2 = Agent(
            name="Agent 2",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
            created_by_id=test_user.id,
        )
        db_session.add_all([agent1, agent2])
        await db_session.commit()
        await db_session.refresh(agent1)
        await db_session.refresh(agent2)

        # Create executions
        exec1 = Execution(
            agent_id=agent1.id,
            input_prompt="Test 1",
            status="pending",
            created_by_id=test_user.id,
        )
        exec2 = Execution(
            agent_id=agent2.id,
            input_prompt="Test 2",
            status="completed",
            created_by_id=test_user.id,
        )
        db_session.add_all([exec1, exec2])
        await db_session.commit()

        # Filter by agent_id
        response = client.get(f"/api/v1/executions/?agent_id={agent1.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["agent_id"] == agent1.id

        # Filter by status
        response = client.get("/api/v1/executions/?status=completed")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "completed"

    async def test_cancel_execution_endpoint(
        self, client: TestClient, db_session: AsyncSession, test_user: User
    ):
        """Test POST /api/v1/executions/{id}/cancel."""
        # Create agent
        agent = Agent(
            name="Test Agent",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
            created_by_id=test_user.id,
        )
        db_session.add(agent)
        await db_session.commit()
        await db_session.refresh(agent)

        # Create running execution
        execution = Execution(
            agent_id=agent.id,
            input_prompt="Test",
            status="running",
            created_by_id=test_user.id,
        )
        db_session.add(execution)
        await db_session.commit()
        await db_session.refresh(execution)

        # Cancel execution
        response = client.post(f"/api/v1/executions/{execution.id}/cancel")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "cancelled"

        # Verify in database
        await db_session.refresh(execution)
        assert execution.status == "cancelled"

    async def test_cancel_execution_not_running(
        self, client: TestClient, db_session: AsyncSession, test_user: User
    ):
        """Test cancelling non-running execution."""
        # Create agent
        agent = Agent(
            name="Test Agent",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
            created_by_id=test_user.id,
        )
        db_session.add(agent)
        await db_session.commit()
        await db_session.refresh(agent)

        # Create completed execution
        execution = Execution(
            agent_id=agent.id,
            input_prompt="Test",
            status="completed",
            created_by_id=test_user.id,
        )
        db_session.add(execution)
        await db_session.commit()
        await db_session.refresh(execution)

        # Try to cancel
        response = client.post(f"/api/v1/executions/{execution.id}/cancel")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_get_traces_endpoint(
        self, client: TestClient, db_session: AsyncSession, test_user: User
    ):
        """Test GET /api/v1/executions/{id}/traces."""
        # Create agent
        agent = Agent(
            name="Test Agent",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
            created_by_id=test_user.id,
        )
        db_session.add(agent)
        await db_session.commit()
        await db_session.refresh(agent)

        # Create execution
        execution = Execution(
            agent_id=agent.id, input_prompt="Test", created_by_id=test_user.id
        )
        db_session.add(execution)
        await db_session.commit()
        await db_session.refresh(execution)

        # Create traces
        from datetime import datetime

        trace1 = Trace(
            execution_id=execution.id,
            sequence_number=0,
            timestamp=datetime.utcnow(),
            event_type="llm_call",
            content={"prompt": "test"},
        )
        trace2 = Trace(
            execution_id=execution.id,
            sequence_number=1,
            timestamp=datetime.utcnow(),
            event_type="llm_response",
            content={"response": "test"},
        )
        db_session.add_all([trace1, trace2])
        await db_session.commit()

        # Get traces
        response = client.get(f"/api/v1/executions/{execution.id}/traces")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["sequence_number"] == 0
        assert data[1]["sequence_number"] == 1

    async def test_get_traces_with_pagination(
        self, client: TestClient, db_session: AsyncSession, test_user: User
    ):
        """Test trace pagination."""
        # Create agent
        agent = Agent(
            name="Test Agent",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
            created_by_id=test_user.id,
        )
        db_session.add(agent)
        await db_session.commit()
        await db_session.refresh(agent)

        # Create execution
        execution = Execution(
            agent_id=agent.id, input_prompt="Test", created_by_id=test_user.id
        )
        db_session.add(execution)
        await db_session.commit()
        await db_session.refresh(execution)

        # Create multiple traces
        from datetime import datetime

        for i in range(5):
            trace = Trace(
                execution_id=execution.id,
                sequence_number=i,
                timestamp=datetime.utcnow(),
                event_type="log",
                content={"message": f"Log {i}"},
            )
            db_session.add(trace)
        await db_session.commit()

        # Get first 2 traces
        response = client.get(
            f"/api/v1/executions/{execution.id}/traces?skip=0&limit=2"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["sequence_number"] == 0
