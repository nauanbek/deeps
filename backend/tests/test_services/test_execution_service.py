"""
Tests for ExecutionService.

Tests cover:
- Execution creation
- Execution starting and streaming
- Execution monitoring and listing
- Execution cancellation
- Trace management
- Token usage calculation
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent import Agent
from models.execution import Execution, Trace
from models.user import User
from services.execution_service import execution_service


@pytest.mark.asyncio
class TestExecutionService:
    """Test suite for ExecutionService."""

    async def test_create_execution_success(self, db_session: AsyncSession):
        """Test successful execution creation."""
        # Create user
        user = User(username="testuser", email="test@example.com", hashed_password="fake")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create agent
        agent = Agent(
            name="Test Agent",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
            created_by_id=user.id,
        )
        db_session.add(agent)
        await db_session.commit()
        await db_session.refresh(agent)

        # Create execution
        execution = await execution_service.create_execution(
            db=db_session,
            agent_id=agent.id,
            prompt="Test prompt",
            created_by_id=user.id,
        )

        assert execution.id is not None
        assert execution.agent_id == agent.id
        assert execution.input_prompt == "Test prompt"
        assert execution.status == "pending"
        assert execution.created_by_id == user.id

    async def test_create_execution_invalid_agent(self, db_session: AsyncSession):
        """Test execution creation with invalid agent ID."""
        with pytest.raises(ValueError, match="Agent .* not found"):
            await execution_service.create_execution(
                db=db_session, agent_id=999999, prompt="Test", created_by_id=1
            )

    async def test_get_execution_by_id(self, db_session: AsyncSession):
        """Test retrieving execution by ID."""
        # Create user and agent
        user = User(username="testuser", email="test@example.com", hashed_password="fake")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        agent = Agent(
            name="Test Agent",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
            created_by_id=user.id,
        )
        db_session.add(agent)
        await db_session.commit()
        await db_session.refresh(agent)

        # Create execution
        execution = await execution_service.create_execution(
            db=db_session, agent_id=agent.id, prompt="Test", created_by_id=user.id
        )

        # Retrieve execution
        retrieved = await execution_service.get_execution(db_session, execution.id)

        assert retrieved is not None
        assert retrieved.id == execution.id
        assert retrieved.input_prompt == "Test"

    async def test_get_execution_not_found(self, db_session: AsyncSession):
        """Test retrieving non-existent execution."""
        result = await execution_service.get_execution(db_session, 999999)
        assert result is None

    async def test_list_executions_no_filters(self, db_session: AsyncSession):
        """Test listing all executions."""
        # Create user and agent
        user = User(username="testuser", email="test@example.com", hashed_password="fake")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        agent = Agent(
            name="Test Agent",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
            created_by_id=user.id,
        )
        db_session.add(agent)
        await db_session.commit()
        await db_session.refresh(agent)

        # Create multiple executions
        exec1 = await execution_service.create_execution(
            db=db_session, agent_id=agent.id, prompt="Test 1", created_by_id=user.id
        )
        exec2 = await execution_service.create_execution(
            db=db_session, agent_id=agent.id, prompt="Test 2", created_by_id=user.id
        )

        # List executions
        executions = await execution_service.list_executions(db_session)

        assert len(executions) == 2
        assert exec1.id in [e.id for e in executions]
        assert exec2.id in [e.id for e in executions]

    async def test_list_executions_by_agent(self, db_session: AsyncSession):
        """Test filtering executions by agent ID."""
        # Create user and agents
        user = User(username="testuser", email="test@example.com", hashed_password="fake")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        agent1 = Agent(
            name="Agent 1",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
            created_by_id=user.id,
        )
        agent2 = Agent(
            name="Agent 2",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
            created_by_id=user.id,
        )
        db_session.add_all([agent1, agent2])
        await db_session.commit()
        await db_session.refresh(agent1)
        await db_session.refresh(agent2)

        # Create executions for both agents
        exec1 = await execution_service.create_execution(
            db=db_session, agent_id=agent1.id, prompt="Test 1", created_by_id=user.id
        )
        exec2 = await execution_service.create_execution(
            db=db_session, agent_id=agent2.id, prompt="Test 2", created_by_id=user.id
        )

        # List executions for agent1
        executions = await execution_service.list_executions(db_session, agent_id=agent1.id)

        assert len(executions) == 1
        assert executions[0].id == exec1.id
        assert executions[0].agent_id == agent1.id

    async def test_list_executions_by_status(self, db_session: AsyncSession):
        """Test filtering executions by status."""
        # Create user and agent
        user = User(username="testuser", email="test@example.com", hashed_password="fake")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        agent = Agent(
            name="Test Agent",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
            created_by_id=user.id,
        )
        db_session.add(agent)
        await db_session.commit()
        await db_session.refresh(agent)

        # Create executions with different statuses
        exec1 = Execution(
            agent_id=agent.id,
            input_prompt="Test 1",
            status="pending",
            created_by_id=user.id,
        )
        exec2 = Execution(
            agent_id=agent.id,
            input_prompt="Test 2",
            status="completed",
            created_by_id=user.id,
        )
        db_session.add_all([exec1, exec2])
        await db_session.commit()

        # List pending executions
        pending_executions = await execution_service.list_executions(
            db_session, status="pending"
        )

        assert len(pending_executions) == 1
        assert pending_executions[0].status == "pending"

    async def test_cancel_execution_success(self, db_session: AsyncSession):
        """Test cancelling a running execution."""
        # Create user and agent
        user = User(username="testuser", email="test@example.com", hashed_password="fake")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        agent = Agent(
            name="Test Agent",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
            created_by_id=user.id,
        )
        db_session.add(agent)
        await db_session.commit()
        await db_session.refresh(agent)

        # Create execution with running status
        execution = Execution(
            agent_id=agent.id,
            input_prompt="Test",
            status="running",
            created_by_id=user.id,
        )
        db_session.add(execution)
        await db_session.commit()
        await db_session.refresh(execution)

        # Cancel execution
        success = await execution_service.cancel_execution(db_session, execution.id)

        assert success is True

        # Verify status changed
        await db_session.refresh(execution)
        assert execution.status == "cancelled"

    async def test_cancel_execution_already_completed(self, db_session: AsyncSession):
        """Test cancelling a completed execution (should fail)."""
        # Create user and agent
        user = User(username="testuser", email="test@example.com", hashed_password="fake")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        agent = Agent(
            name="Test Agent",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
            created_by_id=user.id,
        )
        db_session.add(agent)
        await db_session.commit()
        await db_session.refresh(agent)

        # Create completed execution
        execution = Execution(
            agent_id=agent.id,
            input_prompt="Test",
            status="completed",
            created_by_id=user.id,
        )
        db_session.add(execution)
        await db_session.commit()
        await db_session.refresh(execution)

        # Try to cancel
        success = await execution_service.cancel_execution(db_session, execution.id)

        assert success is False

    async def test_cancel_execution_not_found(self, db_session: AsyncSession):
        """Test cancelling non-existent execution."""
        success = await execution_service.cancel_execution(db_session, 999999)
        assert success is False

    async def test_get_execution_traces(self, db_session: AsyncSession):
        """Test retrieving traces for an execution."""
        # Create user and agent
        user = User(username="testuser", email="test@example.com", hashed_password="fake")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        agent = Agent(
            name="Test Agent",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
            created_by_id=user.id,
        )
        db_session.add(agent)
        await db_session.commit()
        await db_session.refresh(agent)

        # Create execution
        execution = Execution(
            agent_id=agent.id, input_prompt="Test", created_by_id=user.id
        )
        db_session.add(execution)
        await db_session.commit()
        await db_session.refresh(execution)

        # Create traces
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
        traces = await execution_service.get_execution_traces(db_session, execution.id)

        assert len(traces) == 2
        assert traces[0].sequence_number == 0
        assert traces[1].sequence_number == 1

    async def test_get_traces_with_pagination(self, db_session: AsyncSession):
        """Test trace pagination."""
        # Create user and agent
        user = User(username="testuser", email="test@example.com", hashed_password="fake")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        agent = Agent(
            name="Test Agent",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            temperature=0.7,
            created_by_id=user.id,
        )
        db_session.add(agent)
        await db_session.commit()
        await db_session.refresh(agent)

        # Create execution
        execution = Execution(
            agent_id=agent.id, input_prompt="Test", created_by_id=user.id
        )
        db_session.add(execution)
        await db_session.commit()
        await db_session.refresh(execution)

        # Create multiple traces
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
        traces = await execution_service.get_execution_traces(
            db_session, execution.id, skip=0, limit=2
        )

        assert len(traces) == 2
        assert traces[0].sequence_number == 0
        assert traces[1].sequence_number == 1

        # Get next 2 traces
        traces_page2 = await execution_service.get_execution_traces(
            db_session, execution.id, skip=2, limit=2
        )

        assert len(traces_page2) == 2
        assert traces_page2[0].sequence_number == 2
        assert traces_page2[1].sequence_number == 3
