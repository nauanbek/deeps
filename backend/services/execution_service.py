"""
Execution Service for orchestrating agent runs.

This service handles:
- Creating execution records
- Starting and streaming agent executions
- Monitoring execution status
- Cancelling running executions
- Managing execution traces
"""

from typing import Any, AsyncIterator, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from deepagents_integration.executor import agent_executor
from deepagents_integration.factory import agent_factory
from loguru import logger
from models.agent import Agent
from models.execution import Execution, Trace
from services.tool_factory import tool_factory


class ExecutionService:
    """
    Service layer for execution orchestration.

    Responsibilities:
    - Create execution records in database
    - Orchestrate agent execution with deepagents
    - Stream trace events in real-time
    - Track execution status and errors
    - Provide execution querying and filtering
    - Handle execution cancellation
    """

    async def create_execution(
        self, db: AsyncSession, agent_id: int, prompt: str, created_by_id: int
    ) -> Execution:
        """
        Create a new execution record.

        Args:
            db: Database session
            agent_id: ID of agent to execute
            prompt: User input prompt
            created_by_id: User creating the execution

        Returns:
            Created execution record

        Raises:
            ValueError: If agent not found
        """
        # Validate agent exists
        agent = await db.get(Agent, agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        # Create execution record
        execution = Execution(
            agent_id=agent_id,
            input_prompt=prompt,
            status="pending",
            created_by_id=created_by_id,
        )
        db.add(execution)
        await db.commit()
        await db.refresh(execution)
        return execution

    async def start_execution(
        self, db: AsyncSession, execution_id: int
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Start execution and stream trace events.

        This method:
        1. Validates execution exists and is in correct state
        2. Creates deepagent instance from configuration
        3. Executes agent with streaming
        4. Yields trace events as they occur

        Args:
            db: Database session
            execution_id: Execution ID to start

        Yields:
            Trace events as dictionaries

        Raises:
            ValueError: If execution not found or already running
        """
        # Get execution and agent
        execution = await db.get(Execution, execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        if execution.status == "running":
            raise ValueError(f"Execution {execution_id} is already running")

        agent_model = await db.get(Agent, execution.agent_id)
        if not agent_model:
            raise ValueError(f"Agent {execution.agent_id} not found")

        # Load external tools if configured
        external_tools = []
        if agent_model.langchain_tool_ids:
            try:
                external_tools = await tool_factory.get_tools_for_agent(
                    agent_id=agent_model.id,
                    user_id=agent_model.created_by_id,
                    db=db,
                    tool_ids=agent_model.langchain_tool_ids,
                    execution_id=execution_id,
                )
                logger.info(
                    f"Loaded {len(external_tools)} external tools for agent {agent_model.id}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to load external tools for agent {agent_model.id}: {e}"
                )
                # Continue without external tools rather than failing the execution
                # This allows the agent to still run with built-in tools

        # Create deepagent instance with external tools
        deep_agent = await agent_factory.create_agent(
            agent_config=agent_model,
            tools=external_tools if external_tools else None,
            db_session=db,
        )

        # Execute with streaming
        async for trace_event in agent_executor.execute_agent(
            agent=deep_agent,
            prompt=execution.input_prompt,
            execution_id=execution_id,
            db=db,
            stream=True,
        ):
            yield trace_event

    async def get_execution(
        self, db: AsyncSession, execution_id: int
    ) -> Optional[Execution]:
        """
        Get execution by ID.

        Args:
            db: Database session
            execution_id: Execution ID

        Returns:
            Execution if found, None otherwise
        """
        return await db.get(Execution, execution_id)

    async def list_executions(
        self,
        db: AsyncSession,
        agent_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Execution]:
        """
        List executions with optional filters.

        Args:
            db: Database session
            agent_id: Filter by agent ID
            status: Filter by status
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            List of executions matching filters
        """
        query = select(Execution)

        conditions = []
        if agent_id:
            conditions.append(Execution.agent_id == agent_id)
        if status:
            conditions.append(Execution.status == status)

        if conditions:
            query = query.where(and_(*conditions))

        query = (
            query.offset(skip).limit(limit).order_by(Execution.created_at.desc())
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    async def cancel_execution(self, db: AsyncSession, execution_id: int) -> bool:
        """
        Cancel a running execution.

        Args:
            db: Database session
            execution_id: Execution ID to cancel

        Returns:
            True if cancelled successfully, False otherwise
        """
        execution = await db.get(Execution, execution_id)
        if not execution:
            return False

        if execution.status != "running":
            return False

        execution.status = "cancelled"
        await db.commit()
        return True

    async def get_execution_traces(
        self, db: AsyncSession, execution_id: int, skip: int = 0, limit: int = 1000
    ) -> List[Trace]:
        """
        Get traces for an execution with pagination.

        Args:
            db: Database session
            execution_id: Execution ID
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            List of traces ordered by sequence number
        """
        query = (
            select(Trace)
            .where(Trace.execution_id == execution_id)
            .order_by(Trace.sequence_number)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())


# Singleton instance for convenience
execution_service = ExecutionService()
