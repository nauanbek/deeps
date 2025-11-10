"""
Subagent Service Layer for business logic.

Handles all subagent-related business operations including:
- Adding subagents to agents
- Listing agent subagents
- Removing subagents from agents
- Updating subagent configurations
- Circular dependency detection
- Self-reference prevention
"""

from typing import Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.agent import Agent, Subagent
from schemas.subagent import SubagentCreate, SubagentUpdate


# ============================================================================
# Custom Exceptions
# ============================================================================


class SubagentServiceError(Exception):
    """Base exception for subagent service errors."""

    pass


class AgentNotFoundError(SubagentServiceError):
    """Raised when an agent is not found."""

    def __init__(self, agent_id: int):
        self.agent_id = agent_id
        super().__init__(f"Agent with id {agent_id} not found")


class SubagentNotFoundError(SubagentServiceError):
    """Raised when a subagent relationship is not found."""

    def __init__(self, agent_id: int, subagent_id: int):
        self.agent_id = agent_id
        self.subagent_id = subagent_id
        super().__init__(
            f"Subagent relationship not found: agent_id={agent_id}, subagent_id={subagent_id}"
        )


class SelfReferenceError(SubagentServiceError):
    """Raised when trying to make an agent its own subagent."""

    def __init__(self, agent_id: int):
        super().__init__(f"Agent {agent_id} cannot be its own subagent")


class CircularDependencyError(SubagentServiceError):
    """Raised when a circular dependency is detected."""

    def __init__(self, agent_id: int, subagent_id: int):
        super().__init__(
            f"Circular dependency detected: adding subagent {subagent_id} to agent {agent_id} "
            f"would create a cycle"
        )


# ============================================================================
# Subagent Service
# ============================================================================


class SubagentService:
    """
    Service layer for subagent management business logic.

    Provides methods for:
    - Adding subagents to agents with validation
    - Retrieving subagent relationships
    - Updating subagent configurations
    - Removing subagent relationships
    - Preventing circular dependencies and self-references
    """

    async def add_subagent_to_agent(
        self,
        db: AsyncSession,
        agent_id: int,
        subagent_data: SubagentCreate,
    ) -> Subagent:
        """
        Add a subagent to an agent.

        Args:
            db: Database session
            agent_id: ID of the parent agent
            subagent_data: Subagent creation data

        Returns:
            Created Subagent instance

        Raises:
            AgentNotFoundError: If parent or subagent not found
            SelfReferenceError: If agent_id == subagent_id
            CircularDependencyError: If adding would create a cycle
            ValueError: If relationship already exists
        """
        # Verify parent agent exists
        parent_agent = await self._get_agent_by_id(db, agent_id)
        if not parent_agent:
            raise AgentNotFoundError(agent_id)

        # Verify subagent exists
        subagent = await self._get_agent_by_id(db, subagent_data.subagent_id)
        if not subagent:
            raise AgentNotFoundError(subagent_data.subagent_id)

        # Prevent self-reference
        if agent_id == subagent_data.subagent_id:
            raise SelfReferenceError(agent_id)

        # Check for circular dependencies
        if await self._would_create_cycle(db, agent_id, subagent_data.subagent_id):
            raise CircularDependencyError(agent_id, subagent_data.subagent_id)

        # Check if relationship already exists
        existing = await self._get_subagent_relationship(
            db, agent_id, subagent_data.subagent_id
        )
        if existing:
            raise ValueError(
                f"Subagent relationship already exists: agent_id={agent_id}, "
                f"subagent_id={subagent_data.subagent_id}"
            )

        # Create subagent relationship
        subagent_relationship = Subagent(
            agent_id=agent_id,
            subagent_id=subagent_data.subagent_id,
            delegation_prompt=subagent_data.delegation_prompt,
            priority=subagent_data.priority,
        )

        db.add(subagent_relationship)

        try:
            await db.commit()
            await db.refresh(subagent_relationship)
        except IntegrityError as e:
            await db.rollback()
            raise ValueError(f"Database integrity error: {str(e)}")

        return subagent_relationship

    async def list_agent_subagents(
        self,
        db: AsyncSession,
        agent_id: int,
    ) -> list[Subagent]:
        """
        List all subagents for an agent.

        Args:
            db: Database session
            agent_id: ID of the parent agent

        Returns:
            List of Subagent instances ordered by priority (descending)

        Raises:
            AgentNotFoundError: If agent not found
        """
        # Verify agent exists
        agent = await self._get_agent_by_id(db, agent_id)
        if not agent:
            raise AgentNotFoundError(agent_id)

        # Query subagents
        stmt = (
            select(Subagent)
            .where(Subagent.agent_id == agent_id)
            .order_by(Subagent.priority.desc())
            .options(selectinload(Subagent.subagent))
        )

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def remove_subagent_from_agent(
        self,
        db: AsyncSession,
        agent_id: int,
        subagent_id: int,
    ) -> bool:
        """
        Remove a subagent from an agent.

        Args:
            db: Database session
            agent_id: ID of the parent agent
            subagent_id: ID of the subagent to remove

        Returns:
            True if successful

        Raises:
            AgentNotFoundError: If parent agent not found
            SubagentNotFoundError: If relationship not found
        """
        # Verify agent exists
        agent = await self._get_agent_by_id(db, agent_id)
        if not agent:
            raise AgentNotFoundError(agent_id)

        # Get subagent relationship
        subagent_relationship = await self._get_subagent_relationship(
            db, agent_id, subagent_id
        )
        if not subagent_relationship:
            raise SubagentNotFoundError(agent_id, subagent_id)

        # Delete relationship
        await db.delete(subagent_relationship)
        await db.commit()

        return True

    async def update_subagent_config(
        self,
        db: AsyncSession,
        agent_id: int,
        subagent_id: int,
        update_data: SubagentUpdate,
    ) -> Subagent:
        """
        Update subagent configuration.

        Args:
            db: Database session
            agent_id: ID of the parent agent
            subagent_id: ID of the subagent
            update_data: Update data (only provided fields are updated)

        Returns:
            Updated Subagent instance

        Raises:
            AgentNotFoundError: If parent agent not found
            SubagentNotFoundError: If relationship not found
        """
        # Verify agent exists
        agent = await self._get_agent_by_id(db, agent_id)
        if not agent:
            raise AgentNotFoundError(agent_id)

        # Get subagent relationship
        subagent_relationship = await self._get_subagent_relationship(
            db, agent_id, subagent_id
        )
        if not subagent_relationship:
            raise SubagentNotFoundError(agent_id, subagent_id)

        # Update only provided fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(subagent_relationship, field, value)

        try:
            await db.commit()
            await db.refresh(subagent_relationship)
        except IntegrityError as e:
            await db.rollback()
            raise ValueError(f"Database integrity error: {str(e)}")

        return subagent_relationship

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    async def _get_agent_by_id(
        self,
        db: AsyncSession,
        agent_id: int,
    ) -> Optional[Agent]:
        """
        Get agent by ID (only active agents).

        Args:
            db: Database session
            agent_id: Agent ID

        Returns:
            Agent instance or None if not found
        """
        stmt = select(Agent).where(
            Agent.id == agent_id,
            Agent.is_active == True,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_subagent_relationship(
        self,
        db: AsyncSession,
        agent_id: int,
        subagent_id: int,
    ) -> Optional[Subagent]:
        """
        Get subagent relationship by agent_id and subagent_id.

        Args:
            db: Database session
            agent_id: Parent agent ID
            subagent_id: Subagent ID

        Returns:
            Subagent instance or None if not found
        """
        stmt = select(Subagent).where(
            and_(
                Subagent.agent_id == agent_id,
                Subagent.subagent_id == subagent_id,
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def _would_create_cycle(
        self,
        db: AsyncSession,
        agent_id: int,
        subagent_id: int,
    ) -> bool:
        """
        Check if adding a subagent relationship would create a circular dependency.

        Uses depth-first search to detect cycles in the directed graph of agent relationships.

        A cycle exists if:
        - The subagent already has the parent agent as a descendant in its subagent tree

        Args:
            db: Database session
            agent_id: ID of the parent agent
            subagent_id: ID of the subagent to add

        Returns:
            True if adding would create a cycle, False otherwise
        """
        # === CYCLE DETECTION ALGORITHM ===
        # We want to add edge: agent_id → subagent_id
        #
        # A cycle would form if there's already a path: subagent_id → ... → agent_id
        # Because then we'd have: agent_id → subagent_id → ... → agent_id (cycle!)
        #
        # Example of a cycle:
        #   Agent A has subagent B
        #   Agent B has subagent C
        #   If we try to make C a subagent of A's parent (or A itself), we create:
        #   A → B → C → A (cycle detected!)
        #
        # Algorithm:
        #   1. Start from subagent_id
        #   2. Traverse all descendants using DFS
        #   3. If we find agent_id in the descendant tree, adding the edge would create a cycle
        # === END ALGORITHM DESCRIPTION ===

        # If subagent_id already has agent_id as a descendant, adding agent_id → subagent_id
        # would create a cycle
        return await self._has_descendant(db, subagent_id, agent_id)

    async def _has_descendant(
        self,
        db: AsyncSession,
        agent_id: int,
        descendant_id: int,
        visited: Optional[set[int]] = None,
    ) -> bool:
        """
        Check if agent_id has descendant_id in its subagent tree (recursive DFS).

        Args:
            db: Database session
            agent_id: ID of the agent to check
            descendant_id: ID of the potential descendant
            visited: Set of visited agent IDs to prevent infinite loops

        Returns:
            True if descendant_id is in the subagent tree of agent_id
        """
        # === DEPTH-FIRST SEARCH (DFS) FOR DESCENDANT DETECTION ===
        # This is a classic graph traversal algorithm:
        # - Graph: Agents are nodes, subagent relationships are directed edges
        # - Goal: Find if there's a path from agent_id to descendant_id
        # - Method: Recursive DFS with visited set to prevent cycles
        # === END ALGORITHM DESCRIPTION ===

        # Initialize visited set on first call (None → empty set)
        # This tracks which nodes we've already explored to avoid infinite loops
        if visited is None:
            visited = set()

        # BASE CASE: Prevent infinite loops in case of existing cycles
        # If we've already visited this agent during traversal, stop here
        # This is crucial for handling corrupted data with existing cycles
        if agent_id in visited:
            return False

        # Mark current agent as visited before exploring its children
        # This prevents re-visiting the same node in the current path
        visited.add(agent_id)

        # STEP 1: Query database for all direct children (subagents) of current agent
        # This gets the IDs of all agents that are immediate subagents
        stmt = select(Subagent.subagent_id).where(Subagent.agent_id == agent_id)
        result = await db.execute(stmt)
        subagent_ids = result.scalars().all()

        # STEP 2: Base case - check if descendant_id is a direct child
        # If we found the target in the immediate children, we're done!
        if descendant_id in subagent_ids:
            return True

        # STEP 3: Recursive case - check each subagent's subtree
        # For each child, recursively check if descendant_id exists in their tree
        # This explores the entire tree in a depth-first manner
        for sub_id in subagent_ids:
            # Recursively search this subagent's tree
            # Pass visited set to maintain cycle detection across recursive calls
            if await self._has_descendant(db, sub_id, descendant_id, visited):
                return True

        return False


# ============================================================================
# Singleton Instance
# ============================================================================

# Create singleton instance for dependency injection
subagent_service = SubagentService()
