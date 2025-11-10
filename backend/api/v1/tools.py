"""
Tool API endpoints.

Provides REST API for tool marketplace CRUD operations.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_active_user
from models.user import User
from schemas.tool import (
    ToolCategoryResponse,
    ToolCreate,
    ToolListResponse,
    ToolResponse,
    ToolUpdate,
)
from services.tool_service import tool_service

router = APIRouter(prefix="/tools", tags=["tools"])


@router.post("/", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def create_tool(
    tool_data: ToolCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ToolResponse:
    """
    Create a new tool.

    Args:
        tool_data: Tool creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created tool

    Raises:
        HTTPException 401: Unauthorized
        HTTPException 409: Tool name already exists
        HTTPException 500: Internal server error
    """
    try:
        tool = await tool_service.create_tool(db, tool_data, current_user.id)
        return ToolResponse.model_validate(tool)
    except ValueError as e:
        logger.warning(f"Tool creation failed: {e}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating tool: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/", response_model=ToolListResponse)
async def list_tools(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items"),
    tool_type: Optional[str] = Query(None, description="Filter by tool type"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ToolListResponse:
    """
    List tools with optional filtering and pagination.

    Args:
        skip: Pagination offset
        limit: Maximum results per page
        tool_type: Filter by tool type (builtin, custom, langgraph)
        search: Search term for name/description
        is_active: Filter by active status
        db: Database session

    Returns:
        Paginated list of tools with metadata
    """
    try:
        # Get tools
        tools = await tool_service.list_tools(
            db=db,
            skip=skip,
            limit=limit,
            tool_type=tool_type,
            search=search,
            is_active=is_active,
        )

        # Get total count
        total = await tool_service.count_tools(
            db=db,
            tool_type=tool_type,
            search=search,
            is_active=is_active,
        )

        # Calculate pagination metadata
        page = skip // limit + 1 if limit > 0 else 1
        has_next = (skip + limit) < total

        return ToolListResponse(
            tools=[ToolResponse.model_validate(t) for t in tools],
            total=total,
            page=page,
            page_size=limit,
            has_next=has_next,
        )
    except Exception as e:
        logger.error(f"Error listing tools: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/categories", response_model=ToolCategoryResponse)
async def get_tool_categories(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ToolCategoryResponse:
    """
    Get list of tool categories/types.

    Args:
        db: Database session

    Returns:
        List of unique tool categories
    """
    try:
        categories = await tool_service.get_tool_categories(db)
        return ToolCategoryResponse(categories=categories)
    except Exception as e:
        logger.error(f"Error getting tool categories: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ToolResponse:
    """
    Get tool by ID.

    Args:
        tool_id: Tool ID
        db: Database session

    Returns:
        Tool details

    Raises:
        HTTPException 404: Tool not found
    """
    try:
        tool = await tool_service.get_tool(db, tool_id)
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool {tool_id} not found",
            )
        return ToolResponse.model_validate(tool)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool {tool_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.put("/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: int,
    tool_update: ToolUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ToolResponse:
    """
    Update tool.

    Args:
        tool_id: Tool ID to update
        tool_update: Update data
        db: Database session

    Returns:
        Updated tool

    Raises:
        HTTPException 404: Tool not found
        HTTPException 500: Internal server error
    """
    try:
        tool = await tool_service.update_tool(db, tool_id, tool_update)
        return ToolResponse.model_validate(tool)
    except ValueError as e:
        logger.warning(f"Tool update failed: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating tool {tool_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(
    tool_id: int,
    hard_delete: bool = Query(False, description="Permanently delete (vs soft delete)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete tool (soft delete by default).

    Args:
        tool_id: Tool ID to delete
        hard_delete: If True, permanently delete; if False, soft delete
        db: Database session

    Raises:
        HTTPException 404: Tool not found
    """
    try:
        success = await tool_service.delete_tool(db, tool_id, hard_delete)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool {tool_id} not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tool {tool_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
