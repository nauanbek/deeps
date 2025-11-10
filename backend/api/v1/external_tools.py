"""
External Tools API endpoints.

Provides REST API for external tool configuration, connection testing,
and tool marketplace.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_active_user
from models.user import User
from schemas.external_tool import (
    ConnectionTestRequest,
    ConnectionTestResponse,
    ExternalToolConfigCreate,
    ExternalToolConfigListResponse,
    ExternalToolConfigResponse,
    ExternalToolConfigUpdate,
    ToolCatalogResponse,
    ToolUsageAnalytics,
)
from services.external_tool_service import external_tool_service

router = APIRouter(prefix="/external-tools", tags=["external-tools"])


@router.post(
    "/",
    response_model=ExternalToolConfigResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_tool_config(
    tool_data: ExternalToolConfigCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ExternalToolConfigResponse:
    """
    Create new external tool configuration.

    **Security:**
    - Credentials are automatically encrypted before storage
    - User can only access their own tool configurations

    **Example:**
    ```json
    {
      "tool_name": "postgres_prod",
      "tool_type": "postgresql",
      "provider": "langchain",
      "configuration": {
        "host": "localhost",
        "port": 5432,
        "database": "mydb",
        "username": "user",
        "password": "secret123"
      }
    }
    ```

    Args:
        tool_data: Tool configuration data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created tool configuration (credentials masked)

    Raises:
        HTTPException 401: Unauthorized
        HTTPException 409: Tool name already exists
        HTTPException 422: Invalid configuration
        HTTPException 500: Internal server error
    """
    try:
        tool_config = await external_tool_service.create_tool_config(
            db, current_user.id, tool_data
        )
        return ExternalToolConfigResponse.model_validate(tool_config)
    except ValueError as e:
        logger.warning(f"Tool config creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating tool config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/", response_model=ExternalToolConfigListResponse)
async def list_tool_configs(
    tool_type: Optional[str] = Query(None, description="Filter by tool type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ExternalToolConfigListResponse:
    """
    List user's external tool configurations.

    **Query Parameters:**
    - `tool_type`: Filter by type (postgresql, elasticsearch, http, gitlab)
    - `is_active`: Filter by active status
    - `page`: Page number (default: 1)
    - `page_size`: Items per page (default: 50, max: 100)

    Args:
        tool_type: Filter by tool type
        is_active: Filter by active status
        page: Page number
        page_size: Items per page
        current_user: Current authenticated user
        db: Database session

    Returns:
        Paginated list of tool configurations

    Raises:
        HTTPException 401: Unauthorized
        HTTPException 500: Internal server error
    """
    try:
        skip = (page - 1) * page_size

        # Get tool configs
        tool_configs = await external_tool_service.list_tool_configs(
            db=db,
            user_id=current_user.id,
            tool_type=tool_type,
            is_active=is_active,
            skip=skip,
            limit=page_size,
        )

        # Get total count
        total = await external_tool_service.count_tool_configs(
            db=db,
            user_id=current_user.id,
            tool_type=tool_type,
            is_active=is_active,
        )

        # Convert to response models
        items = [
            ExternalToolConfigResponse.model_validate(config)
            for config in tool_configs
        ]

        has_more = (skip + len(items)) < total

        return ExternalToolConfigListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more,
        )

    except Exception as e:
        logger.error(f"Error listing tool configs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/{tool_id}", response_model=ExternalToolConfigResponse)
async def get_tool_config(
    tool_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ExternalToolConfigResponse:
    """
    Get external tool configuration by ID.

    Args:
        tool_id: Tool configuration ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Tool configuration (credentials masked)

    Raises:
        HTTPException 401: Unauthorized
        HTTPException 404: Tool not found
        HTTPException 500: Internal server error
    """
    try:
        tool_config = await external_tool_service.get_tool_config(
            db, current_user.id, tool_id
        )

        if not tool_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool configuration {tool_id} not found",
            )

        return ExternalToolConfigResponse.model_validate(tool_config)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.put("/{tool_id}", response_model=ExternalToolConfigResponse)
async def update_tool_config(
    tool_id: int,
    tool_data: ExternalToolConfigUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ExternalToolConfigResponse:
    """
    Update external tool configuration.

    **Note:** Updating configuration resets test status to "not_tested".

    Args:
        tool_id: Tool configuration ID
        tool_data: Update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated tool configuration

    Raises:
        HTTPException 401: Unauthorized
        HTTPException 404: Tool not found
        HTTPException 409: Tool name conflict
        HTTPException 422: Invalid configuration
        HTTPException 500: Internal server error
    """
    try:
        tool_config = await external_tool_service.update_tool_config(
            db, current_user.id, tool_id, tool_data
        )

        if not tool_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool configuration {tool_id} not found",
            )

        return ExternalToolConfigResponse.model_validate(tool_config)

    except ValueError as e:
        logger.warning(f"Tool config update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tool config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool_config(
    tool_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete external tool configuration.

    **Warning:** This action cannot be undone. Agents using this tool
    will fail to execute.

    Args:
        tool_id: Tool configuration ID
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException 401: Unauthorized
        HTTPException 404: Tool not found
        HTTPException 500: Internal server error
    """
    try:
        deleted = await external_tool_service.delete_tool_config(
            db, current_user.id, tool_id
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool configuration {tool_id} not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tool config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/{tool_id}/test", response_model=ConnectionTestResponse)
async def test_tool_connection(
    tool_id: int,
    test_request: Optional[ConnectionTestRequest] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ConnectionTestResponse:
    """
    Test connection to external tool.

    **Use Cases:**
    - Test before saving (provide `configuration` in request body)
    - Test existing configuration (no request body)

    **Example:**
    ```json
    {
      "configuration": {
        "host": "new-host.example.com",
        "port": 5432,
        "database": "testdb",
        "username": "user",
        "password": "password"
      }
    }
    ```

    Args:
        tool_id: Tool configuration ID
        test_request: Optional config override for testing
        current_user: Current authenticated user
        db: Database session

    Returns:
        Connection test result

    Raises:
        HTTPException 401: Unauthorized
        HTTPException 404: Tool not found
        HTTPException 500: Internal server error
    """
    try:
        override_config = test_request.configuration if test_request else None

        result = await external_tool_service.test_connection(
            db, current_user.id, tool_id, override_config
        )

        return ConnectionTestResponse(**result)

    except ValueError as e:
        logger.warning(f"Tool connection test failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error testing tool connection: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


# ============================================================================
# Tool Catalog & Analytics
# ============================================================================


@router.get("/catalog/all", response_model=ToolCatalogResponse, tags=["tools"])
async def get_tool_catalog(
    current_user: User = Depends(get_current_active_user),
) -> ToolCatalogResponse:
    """
    Get tool catalog for marketplace.

    Returns available tools with configuration schemas, examples,
    and metadata for the Tool Marketplace UI.

    **Categories:**
    - database: PostgreSQL, MySQL, etc.
    - git: GitLab, GitHub
    - logs: Elasticsearch, Splunk
    - monitoring: Sentry, Datadog
    - http: Generic HTTP API clients

    Args:
        current_user: Current authenticated user

    Returns:
        Tool catalog with all available tools

    Raises:
        HTTPException 401: Unauthorized
        HTTPException 500: Internal server error
    """
    try:
        catalog_items = await external_tool_service.get_tool_catalog()

        return ToolCatalogResponse(
            langchain_tools=catalog_items,
            total=len(catalog_items),
        )

    except Exception as e:
        logger.error(f"Error getting tool catalog: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/analytics/usage", response_model=ToolUsageAnalytics, tags=["monitoring"])
async def get_tool_usage_analytics(
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ToolUsageAnalytics:
    """
    Get tool usage analytics.

    **Metrics:**
    - Total tool configurations
    - Active tool configurations
    - Total executions
    - Success rate
    - Per-tool statistics (executions, duration, success rate)

    Args:
        days: Number of days to analyze (default: 30, max: 90)
        current_user: Current authenticated user
        db: Database session

    Returns:
        Tool usage analytics

    Raises:
        HTTPException 401: Unauthorized
        HTTPException 500: Internal server error
    """
    try:
        analytics = await external_tool_service.get_tool_usage_analytics(
            db, current_user.id, days
        )

        return ToolUsageAnalytics(**analytics)

    except Exception as e:
        logger.error(f"Error getting tool usage analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
