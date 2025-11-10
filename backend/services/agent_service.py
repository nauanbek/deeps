"""
Agent Service Layer for business logic.

Handles all agent-related business operations including:
- Agent CRUD operations
- Validation of agent data
- Agent-tool associations
- Soft/hard delete operations
"""

from typing import Any, Optional

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.agent import Agent, AgentTool
from models.tool import Tool
from schemas.agent import AgentCreate, AgentUpdate


# ============================================================================
# Custom Exceptions
# ============================================================================


class AgentServiceError(Exception):
    """Base exception for agent service errors."""

    pass


class AgentNotFoundError(AgentServiceError):
    """Raised when an agent is not found."""

    def __init__(self, agent_id: int):
        self.agent_id = agent_id
        super().__init__(f"Agent with id {agent_id} not found")


class AgentValidationError(AgentServiceError):
    """Raised when agent validation fails."""

    pass


class ToolNotFoundError(AgentServiceError):
    """Raised when a tool is not found."""

    def __init__(self, tool_id: int):
        self.tool_id = tool_id
        super().__init__(f"Tool with id {tool_id} not found")


# ============================================================================
# Agent Service
# ============================================================================


class AgentService:
    """
    Service layer for agent management business logic.

    Provides methods for:
    - Creating agents with validation
    - Retrieving agents by ID or listing with filters
    - Updating agent configurations
    - Soft/hard deleting agents
    - Managing agent-tool associations
    """

    async def create_agent(
        self,
        db: AsyncSession,
        agent_data: AgentCreate,
        created_by_id: int,
    ) -> Agent:
        """
        Create a new agent configuration.

        Args:
            db: Database session
            agent_data: Agent creation data
            created_by_id: ID of user creating the agent

        Returns:
            Created agent instance

        Raises:
            AgentValidationError: If validation fails
        """
        # Validate agent data
        await self._validate_agent_data(db, agent_data, created_by_id)

        # Create agent instance
        agent = Agent(
            name=agent_data.name,
            description=agent_data.description,
            model_provider=agent_data.model_provider,
            model_name=agent_data.model_name,
            temperature=agent_data.temperature,
            max_tokens=agent_data.max_tokens,
            system_prompt=agent_data.system_prompt,
            planning_enabled=agent_data.planning_enabled,
            filesystem_enabled=agent_data.filesystem_enabled,
            additional_config=agent_data.additional_config,
            created_by_id=created_by_id,
            is_active=True,
        )

        db.add(agent)

        try:
            await db.commit()
            await db.refresh(agent)
        except IntegrityError as e:
            await db.rollback()
            raise AgentValidationError(f"Database integrity error: {str(e)}")

        return agent

    async def get_agent(
        self,
        db: AsyncSession,
        agent_id: int,
        include_inactive: bool = False,
    ) -> Optional[Agent]:
        """
        Get agent by ID.

        Args:
            db: Database session
            agent_id: Agent ID
            include_inactive: Whether to include inactive agents

        Returns:
            Agent instance or None if not found
        """
        stmt = select(Agent).where(Agent.id == agent_id)

        if not include_inactive:
            stmt = stmt.where(Agent.is_active == True)

        # Eager load relationships for better performance
        stmt = stmt.options(
            selectinload(Agent.agent_tools).selectinload(AgentTool.tool),
            selectinload(Agent.subagents),
        )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_agents(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        created_by_id: Optional[int] = None,
    ) -> list[Agent]:
        """
        List agents with pagination and filters.

        Args:
            db: Database session
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            is_active: Filter by active status (None = active only by default)
            created_by_id: Filter by creator user ID

        Returns:
            List of agent instances
        """
        stmt = select(Agent)

        # Apply filters
        if is_active is None:
            # Default: only active agents
            stmt = stmt.where(Agent.is_active == True)
        else:
            stmt = stmt.where(Agent.is_active == is_active)

        if created_by_id is not None:
            stmt = stmt.where(Agent.created_by_id == created_by_id)

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)

        # Order by created_at descending (newest first)
        stmt = stmt.order_by(Agent.created_at.desc())

        # Eager load relationships
        stmt = stmt.options(
            selectinload(Agent.agent_tools).selectinload(AgentTool.tool),
            selectinload(Agent.subagents),
        )

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def update_agent(
        self,
        db: AsyncSession,
        agent_id: int,
        agent_update: AgentUpdate,
    ) -> Agent:
        """
        Update agent configuration.

        Args:
            db: Database session
            agent_id: Agent ID to update
            agent_update: Update data (only provided fields are updated)

        Returns:
            Updated agent instance

        Raises:
            AgentNotFoundError: If agent not found
            AgentValidationError: If validation fails
        """
        # Get existing agent
        agent = await self.get_agent(db, agent_id, include_inactive=True)
        if not agent:
            raise AgentNotFoundError(agent_id)

        # Validate update data
        await self._validate_agent_update(db, agent_update, agent)

        # Update only provided fields
        update_data = agent_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(agent, field, value)

        try:
            await db.commit()
            await db.refresh(agent)
        except IntegrityError as e:
            await db.rollback()
            raise AgentValidationError(f"Database integrity error: {str(e)}")

        return agent

    async def delete_agent(
        self,
        db: AsyncSession,
        agent_id: int,
        hard_delete: bool = False,
    ) -> bool:
        """
        Delete agent (soft delete by default).

        Args:
            db: Database session
            agent_id: Agent ID to delete
            hard_delete: If True, permanently delete. If False, set is_active=False

        Returns:
            True if successful

        Raises:
            AgentNotFoundError: If agent not found
        """
        # Get agent
        agent = await self.get_agent(db, agent_id, include_inactive=True)
        if not agent:
            raise AgentNotFoundError(agent_id)

        if hard_delete:
            # Permanently delete
            await db.delete(agent)
        else:
            # Soft delete
            agent.is_active = False

        await db.commit()
        return True

    async def add_tools_to_agent(
        self,
        db: AsyncSession,
        agent_id: int,
        tool_ids: list[int],
        configurations: Optional[dict[int, dict[str, Any]]] = None,
    ) -> Agent:
        """
        Associate tools with an agent.

        Args:
            db: Database session
            agent_id: Agent ID
            tool_ids: List of tool IDs to add
            configurations: Optional dict mapping tool_id to configuration override

        Returns:
            Updated agent instance

        Raises:
            AgentNotFoundError: If agent not found
            ToolNotFoundError: If any tool not found
        """
        # Verify agent exists
        agent = await self.get_agent(db, agent_id, include_inactive=True)
        if not agent:
            raise AgentNotFoundError(agent_id)

        # Verify all tools exist
        stmt = select(Tool).where(Tool.id.in_(tool_ids), Tool.is_active == True)
        result = await db.execute(stmt)
        tools = result.scalars().all()

        if len(tools) != len(tool_ids):
            found_ids = {t.id for t in tools}
            missing_ids = set(tool_ids) - found_ids
            raise ToolNotFoundError(list(missing_ids)[0])

        # Add tools to agent
        for tool_id in tool_ids:
            # Check if association already exists
            stmt = select(AgentTool).where(
                and_(
                    AgentTool.agent_id == agent_id,
                    AgentTool.tool_id == tool_id,
                )
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                config_override = {}
                if configurations and tool_id in configurations:
                    config_override = configurations[tool_id]

                agent_tool = AgentTool(
                    agent_id=agent_id,
                    tool_id=tool_id,
                    configuration_override=config_override,
                )
                db.add(agent_tool)

        await db.commit()
        await db.refresh(agent)
        return agent

    async def remove_tools_from_agent(
        self,
        db: AsyncSession,
        agent_id: int,
        tool_ids: list[int],
    ) -> Agent:
        """
        Remove tool associations from an agent.

        Args:
            db: Database session
            agent_id: Agent ID
            tool_ids: List of tool IDs to remove

        Returns:
            Updated agent instance

        Raises:
            AgentNotFoundError: If agent not found
        """
        # Verify agent exists
        agent = await self.get_agent(db, agent_id, include_inactive=True)
        if not agent:
            raise AgentNotFoundError(agent_id)

        # Remove tool associations
        stmt = select(AgentTool).where(
            and_(
                AgentTool.agent_id == agent_id,
                AgentTool.tool_id.in_(tool_ids),
            )
        )
        result = await db.execute(stmt)
        agent_tools = result.scalars().all()

        for agent_tool in agent_tools:
            await db.delete(agent_tool)

        await db.commit()
        await db.refresh(agent)
        return agent

    async def update_tool_configuration(
        self,
        db: AsyncSession,
        agent_id: int,
        tool_id: int,
        configuration: dict[str, Any],
    ) -> Agent:
        """
        Update tool configuration for an agent.

        Args:
            db: Database session
            agent_id: Agent ID
            tool_id: Tool ID
            configuration: New configuration override

        Returns:
            Updated agent instance

        Raises:
            AgentNotFoundError: If agent not found
            ToolNotFoundError: If tool association not found
        """
        # Verify agent exists
        agent = await self.get_agent(db, agent_id, include_inactive=True)
        if not agent:
            raise AgentNotFoundError(agent_id)

        # Get agent-tool association
        stmt = select(AgentTool).where(
            and_(
                AgentTool.agent_id == agent_id,
                AgentTool.tool_id == tool_id,
            )
        )
        result = await db.execute(stmt)
        agent_tool = result.scalar_one_or_none()

        if not agent_tool:
            raise ToolNotFoundError(tool_id)

        # Update configuration
        agent_tool.configuration_override = configuration

        await db.commit()
        await db.refresh(agent)
        return agent

    # ========================================================================
    # Private Validation Methods
    # ========================================================================

    async def _validate_agent_data(
        self,
        db: AsyncSession,
        agent_data: AgentCreate,
        created_by_id: int,
        exclude_agent_id: Optional[int] = None,
    ) -> None:
        """
        Validate agent creation data.

        Args:
            db: Database session
            agent_data: Agent data to validate
            created_by_id: ID of user creating the agent
            exclude_agent_id: Agent ID to exclude from name uniqueness check

        Raises:
            AgentValidationError: If validation fails
        """
        # Validate temperature range
        if agent_data.temperature < 0.0 or agent_data.temperature > 2.0:
            raise AgentValidationError(
                f"Temperature must be between 0.0 and 2.0, got {agent_data.temperature}"
            )

        # Validate max_tokens
        if agent_data.max_tokens is not None and agent_data.max_tokens <= 0:
            raise AgentValidationError(
                f"max_tokens must be positive, got {agent_data.max_tokens}"
            )

        # Check name uniqueness per user
        stmt = select(Agent).where(
            and_(
                Agent.name == agent_data.name,
                Agent.created_by_id == created_by_id,
                Agent.is_active == True,
            )
        )

        if exclude_agent_id is not None:
            stmt = stmt.where(Agent.id != exclude_agent_id)

        result = await db.execute(stmt)
        existing_agent = result.scalar_one_or_none()

        if existing_agent:
            raise AgentValidationError(
                f"Agent with name '{agent_data.name}' already exists for this user"
            )

    async def _validate_agent_update(
        self,
        db: AsyncSession,
        agent_update: AgentUpdate,
        existing_agent: Agent,
    ) -> None:
        """
        Validate agent update data.

        Args:
            db: Database session
            agent_update: Update data
            existing_agent: Existing agent being updated

        Raises:
            AgentValidationError: If validation fails
        """
        # Validate temperature if provided
        if agent_update.temperature is not None:
            if agent_update.temperature < 0.0 or agent_update.temperature > 2.0:
                raise AgentValidationError(
                    f"Temperature must be between 0.0 and 2.0, got {agent_update.temperature}"
                )

        # Validate max_tokens if provided
        if agent_update.max_tokens is not None and agent_update.max_tokens <= 0:
            raise AgentValidationError(
                f"max_tokens must be positive, got {agent_update.max_tokens}"
            )

        # Check name uniqueness if name is being updated
        if agent_update.name is not None and agent_update.name != existing_agent.name:
            stmt = select(Agent).where(
                and_(
                    Agent.name == agent_update.name,
                    Agent.created_by_id == existing_agent.created_by_id,
                    Agent.is_active == True,
                    Agent.id != existing_agent.id,
                )
            )
            result = await db.execute(stmt)
            duplicate = result.scalar_one_or_none()

            if duplicate:
                raise AgentValidationError(
                    f"Agent with name '{agent_update.name}' already exists for this user"
                )


# ============================================================================
# Singleton Instance
# ============================================================================

# Create singleton instance for dependency injection
agent_service = AgentService()
