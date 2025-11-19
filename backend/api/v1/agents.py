"""
Agent API endpoints for CRUD operations.

Provides RESTful API endpoints for managing agents:
- POST /agents/ - Create a new agent
- GET /agents/ - List agents with pagination and filters
- GET /agents/{agent_id} - Get agent by ID
- PUT /agents/{agent_id} - Update agent configuration
- DELETE /agents/{agent_id} - Delete agent (soft or hard)
- POST /agents/{agent_id}/tools - Add tools to agent
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_active_user
from models.user import User
from schemas.agent import AgentCreate, AgentResponse, AgentUpdate
from schemas.subagent import SubagentCreate, SubagentResponse, SubagentUpdate
from services.agent_service import (
    AgentNotFoundError,
    AgentValidationError,
    ToolNotFoundError,
    agent_service,
)
from services.subagent_service import (
    AgentNotFoundError as SubagentAgentNotFoundError,
    CircularDependencyError,
    SelfReferenceError,
    SubagentNotFoundError,
    subagent_service,
)

# Create router with prefix and tags
router = APIRouter(prefix="/agents", tags=["agents"])


# ============================================================================
# Helper Functions - Authorization
# ============================================================================


async def get_agent_or_403(
    agent_id: int,
    user_id: int,
    db: AsyncSession,
) -> "Agent":
    """
    Get agent and verify ownership, raise 403 if not owner.

    This function ensures multi-tenancy isolation by verifying that
    the requesting user owns the agent before returning it.

    Args:
        agent_id: Agent ID to fetch
        user_id: Current user ID (from JWT token)
        db: Database session

    Returns:
        Agent: The agent if user is the owner

    Raises:
        404: Agent not found
        403: User doesn't own this agent (access denied)
    """
    from models.agent import Agent

    agent = await agent_service.get_agent(db=db, agent_id=agent_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id {agent_id} not found",
        )

    # Critical security check: Verify ownership
    if agent.created_by_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this agent",
        )

    return agent


# ============================================================================
# POST /agents/ - Create Agent
# ============================================================================


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new agent configuration.

    Args:
        agent_data: Agent creation data
        current_user: Current authenticated user
        db: Database session (injected)

    Returns:
        Created agent with all fields

    Raises:
        400: Validation error (invalid data)
        401: Unauthorized (no valid JWT token)
        409: Conflict (duplicate name)
        500: Internal server error
    """
    try:
        agent = await agent_service.create_agent(
            db=db,
            agent_data=agent_data,
            created_by_id=current_user.id,
        )
        return agent
    except AgentValidationError as e:
        if "already exists" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agent: {str(e)}",
        )


# ============================================================================
# GET /agents/ - List Agents
# ============================================================================


@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    is_active: Optional[bool] = Query(
        None, description="Filter by active status (default: true)"
    ),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all agents with pagination and filters.

    Args:
        skip: Number of records to skip (default: 0)
        limit: Maximum records to return (default: 100, max: 1000)
        is_active: Filter by active status (default: only active agents)
        current_user: Current authenticated user
        db: Database session (injected)

    Returns:
        List of agents matching criteria

    Raises:
        401: Unauthorized (no valid JWT token)
        500: Internal server error
    """
    try:
        agents = await agent_service.list_agents(
            db=db,
            skip=skip,
            limit=limit,
            is_active=is_active,
        )
        return agents
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list agents: {str(e)}",
        )


# ============================================================================
# GET /agents/{agent_id} - Get Agent by ID
# ============================================================================


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get agent by ID.

    Args:
        agent_id: Agent ID
        current_user: Current authenticated user
        db: Database session (injected)

    Returns:
        Agent with specified ID

    Raises:
        401: Unauthorized (no valid JWT token)
        403: Forbidden (not agent owner)
        404: Agent not found
        500: Internal server error
    """
    try:
        # Verify ownership before returning agent
        agent = await get_agent_or_403(agent_id, current_user.id, db)
        return agent
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent: {str(e)}",
        )


# ============================================================================
# PUT /agents/{agent_id} - Update Agent
# ============================================================================


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    agent_update: AgentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update agent configuration.

    Args:
        agent_id: Agent ID to update
        agent_update: Update data (only provided fields are updated)
        current_user: Current authenticated user
        db: Database session (injected)

    Returns:
        Updated agent

    Raises:
        400: Validation error
        401: Unauthorized (no valid JWT token)
        403: Forbidden (not agent owner)
        404: Agent not found
        409: Conflict (duplicate name)
        500: Internal server error
    """
    try:
        # Verify ownership before updating
        await get_agent_or_403(agent_id, current_user.id, db)

        agent = await agent_service.update_agent(
            db=db,
            agent_id=agent_id,
            agent_update=agent_update,
        )
        return agent
    except HTTPException:
        raise
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AgentValidationError as e:
        if "already exists" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agent: {str(e)}",
        )


# ============================================================================
# DELETE /agents/{agent_id} - Delete Agent
# ============================================================================


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: int,
    hard_delete: bool = Query(
        False, description="Permanently delete agent (default: soft delete)"
    ),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete agent (soft delete by default).

    Args:
        agent_id: Agent ID to delete
        hard_delete: If True, permanently delete. If False, soft delete (is_active=False)
        current_user: Current authenticated user
        db: Database session (injected)

    Returns:
        No content (204)

    Raises:
        401: Unauthorized (no valid JWT token)
        403: Forbidden (not agent owner)
        404: Agent not found
        500: Internal server error
    """
    try:
        # Verify ownership before deleting
        await get_agent_or_403(agent_id, current_user.id, db)

        await agent_service.delete_agent(
            db=db,
            agent_id=agent_id,
            hard_delete=hard_delete,
        )
        return None
    except HTTPException:
        raise
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete agent: {str(e)}",
        )


# ============================================================================
# POST /agents/{agent_id}/tools - Add Tools to Agent
# ============================================================================


@router.post("/{agent_id}/tools", response_model=AgentResponse)
async def add_tools_to_agent(
    agent_id: int,
    tool_data: dict,  # Expects {"tool_ids": [1, 2, 3]}
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Associate tools with an agent.

    Args:
        agent_id: Agent ID
        tool_data: Dictionary with "tool_ids" list
        current_user: Current authenticated user
        db: Database session (injected)

    Returns:
        Updated agent

    Raises:
        400: Invalid request data
        401: Unauthorized (no valid JWT token)
        403: Forbidden (not agent owner)
        404: Agent or tool not found
        500: Internal server error
    """
    try:
        # Verify ownership before modifying tools
        await get_agent_or_403(agent_id, current_user.id, db)

        # Extract tool_ids from request
        tool_ids = tool_data.get("tool_ids", [])

        if not tool_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="tool_ids is required and must not be empty",
            )

        agent = await agent_service.add_tools_to_agent(
            db=db,
            agent_id=agent_id,
            tool_ids=tool_ids,
        )
        return agent
    except HTTPException:
        raise
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ToolNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add tools to agent: {str(e)}",
        )


# ============================================================================
# POST /agents/{agent_id}/subagents - Add Subagent to Agent
# ============================================================================


@router.post(
    "/{agent_id}/subagents",
    response_model=SubagentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_subagent_to_agent(
    agent_id: int,
    subagent_data: SubagentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a subagent to an agent for hierarchical delegation.

    Args:
        agent_id: ID of the parent agent
        subagent_data: Subagent configuration
        current_user: Current authenticated user
        db: Database session (injected)

    Returns:
        Created subagent relationship

    Raises:
        400: Validation error (self-reference, circular dependency)
        401: Unauthorized (no valid JWT token)
        403: Forbidden (not agent owner)
        404: Agent or subagent not found
        409: Conflict (duplicate relationship)
        500: Internal server error
    """
    try:
        # Verify ownership before adding subagent
        await get_agent_or_403(agent_id, current_user.id, db)

        subagent = await subagent_service.add_subagent_to_agent(
            db=db,
            agent_id=agent_id,
            subagent_data=subagent_data,
        )
        return subagent
    except HTTPException:
        raise
    except SubagentAgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except SelfReferenceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except CircularDependencyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ValueError as e:
        if "already exists" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add subagent to agent: {str(e)}",
        )


# ============================================================================
# GET /agents/{agent_id}/subagents - List Agent Subagents
# ============================================================================


@router.get("/{agent_id}/subagents", response_model=List[SubagentResponse])
async def list_agent_subagents(
    agent_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all subagents for an agent.

    Args:
        agent_id: ID of the parent agent
        current_user: Current authenticated user
        db: Database session (injected)

    Returns:
        List of subagent relationships ordered by priority (descending)

    Raises:
        401: Unauthorized (no valid JWT token)
        403: Forbidden (not agent owner)
        404: Agent not found
        500: Internal server error
    """
    try:
        # Verify ownership before listing subagents
        await get_agent_or_403(agent_id, current_user.id, db)

        subagents = await subagent_service.list_agent_subagents(
            db=db,
            agent_id=agent_id,
        )
        return subagents
    except HTTPException:
        raise
    except SubagentAgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list agent subagents: {str(e)}",
        )


# ============================================================================
# DELETE /agents/{agent_id}/subagents/{subagent_id} - Remove Subagent
# ============================================================================


@router.delete("/{agent_id}/subagents/{subagent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_subagent_from_agent(
    agent_id: int,
    subagent_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove a subagent from an agent.

    Args:
        agent_id: ID of the parent agent
        subagent_id: ID of the subagent to remove
        current_user: Current authenticated user
        db: Database session (injected)

    Returns:
        No content (204)

    Raises:
        401: Unauthorized (no valid JWT token)
        403: Forbidden (not agent owner)
        404: Agent or subagent relationship not found
        500: Internal server error
    """
    try:
        # Verify ownership before removing subagent
        await get_agent_or_403(agent_id, current_user.id, db)

        await subagent_service.remove_subagent_from_agent(
            db=db,
            agent_id=agent_id,
            subagent_id=subagent_id,
        )
        return None
    except HTTPException:
        raise
    except SubagentAgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except SubagentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove subagent from agent: {str(e)}",
        )


# ============================================================================
# PUT /agents/{agent_id}/subagents/{subagent_id} - Update Subagent Config
# ============================================================================


@router.put("/{agent_id}/subagents/{subagent_id}", response_model=SubagentResponse)
async def update_subagent_config(
    agent_id: int,
    subagent_id: int,
    update_data: SubagentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update subagent configuration.

    Args:
        agent_id: ID of the parent agent
        subagent_id: ID of the subagent
        update_data: Update data (only provided fields are updated)
        current_user: Current authenticated user
        db: Database session (injected)

    Returns:
        Updated subagent relationship

    Raises:
        401: Unauthorized (no valid JWT token)
        403: Forbidden (not agent owner)
        404: Agent or subagent relationship not found
        500: Internal server error
    """
    try:
        # Verify ownership before updating subagent
        await get_agent_or_403(agent_id, current_user.id, db)

        subagent = await subagent_service.update_subagent_config(
            db=db,
            agent_id=agent_id,
            subagent_id=subagent_id,
            update_data=update_data,
        )
        return subagent
    except HTTPException:
        raise
    except SubagentAgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except SubagentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update subagent configuration: {str(e)}",
        )


# ============================================================================
# PUT /agents/{agent_id}/tools - Update Agent External Tools
# ============================================================================


@router.put("/{agent_id}/tools", response_model=AgentResponse)
async def update_agent_tools(
    agent_id: int,
    langchain_tool_ids: List[int],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update agent's external tool configurations.

    **Request Body:**
    ```json
    [1, 2, 3]  // Array of external_tool_configs.id
    ```

    **Validation:**
    - All tool IDs must belong to the current user
    - Tool configurations must be active
    - Tool IDs must exist in external_tool_configs table

    Args:
        agent_id: Agent ID to update
        langchain_tool_ids: List of external tool config IDs
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated agent with tool configurations

    Raises:
        HTTPException 401: Unauthorized
        HTTPException 403: Forbidden (not agent owner)
        HTTPException 404: Agent not found
        HTTPException 422: Invalid tool IDs
        HTTPException 500: Internal server error
    """
    try:
        # Verify ownership before updating tools
        await get_agent_or_403(agent_id, current_user.id, db)

        # Validate that all tools belong to current user
        from models.external_tool import ExternalToolConfig
        from sqlalchemy import select, and_

        if langchain_tool_ids:
            stmt = select(ExternalToolConfig).where(
                and_(
                    ExternalToolConfig.id.in_(langchain_tool_ids),
                    ExternalToolConfig.user_id == current_user.id,
                    ExternalToolConfig.is_active == True,
                )
            )
            result = await db.execute(stmt)
            found_tools = result.scalars().all()

            if len(found_tools) != len(langchain_tool_ids):
                found_ids = [tool.id for tool in found_tools]
                missing_ids = set(langchain_tool_ids) - set(found_ids)
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid tool IDs: {missing_ids}. Tools must belong to current user and be active.",
                )

        # Update agent
        from schemas.agent import AgentUpdate

        update_data = AgentUpdate(langchain_tool_ids=langchain_tool_ids)
        agent = await agent_service.update_agent(
            db=db,
            agent_id=agent_id,
            agent_update=update_data,
            user_id=current_user.id,
        )

        return agent

    except HTTPException:
        raise
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agent tools: {str(e)}",
        )
