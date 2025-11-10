"""
Template API endpoints for CRUD operations and template management.

Provides RESTful API endpoints for managing templates:
- POST /templates/ - Create a new template
- GET /templates/ - List templates with pagination, filtering, and search
- GET /templates/{template_id} - Get template by ID
- PUT /templates/{template_id} - Update template configuration
- DELETE /templates/{template_id} - Delete template (soft or hard)
- GET /templates/categories - Get list of categories
- GET /templates/featured - Get featured templates
- GET /templates/popular - Get popular templates
- POST /templates/{template_id}/use - Increment use count
- POST /templates/{template_id}/create-agent - Create agent from template
- POST /templates/import - Import template from JSON
- GET /templates/{template_id}/export - Export template as JSON
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_active_user
from models.user import User
from schemas.agent import AgentResponse
from schemas.template import (
    AgentFromTemplateCreate,
    TemplateCategoryResponse,
    TemplateCreate,
    TemplateExport,
    TemplateImport,
    TemplateListResponse,
    TemplateResponse,
    TemplateUpdate,
)
from services.template_service import (
    DuplicateTemplateNameError,
    TemplateNotFoundError,
    TemplateService,
    TemplateValidationError,
)

# Create router with prefix and tags
router = APIRouter(prefix="/templates", tags=["templates"])

# Initialize service
template_service = TemplateService()


# ============================================================================
# POST /templates/ - Create Template
# ============================================================================


@router.post("/", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new template.

    Requires authentication.

    Args:
        template_data: Template creation data
        current_user: Current authenticated user
        db: Database session (injected)

    Returns:
        Created template with all fields

    Raises:
        400: Validation error (invalid data)
        401: Unauthorized (no valid JWT token)
        409: Conflict (duplicate name)
        500: Internal server error
    """
    try:
        template = await template_service.create_template(
            db=db,
            template_data=template_data,
            created_by_id=current_user.id,
        )
        return template
    except DuplicateTemplateNameError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except TemplateValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}",
        )


# ============================================================================
# GET /templates/ - List Templates
# ============================================================================


@router.get("/", response_model=TemplateListResponse)
async def list_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    is_public: Optional[bool] = Query(None, description="Filter by public/private"),
    is_featured: Optional[bool] = Query(None, description="Filter by featured status"),
    search: Optional[str] = Query(None, description="Search in name, description, tags"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records"),
    db: AsyncSession = Depends(get_db),
):
    """
    List templates with filtering, search, and pagination.

    Public endpoint (no authentication required).

    Query Parameters:
        - category: Filter by category (research, coding, etc.)
        - is_public: Filter by public (true) or private (false)
        - is_featured: Filter by featured status
        - search: Full-text search in name, description, and tags
        - skip: Pagination offset (default: 0)
        - limit: Page size (default: 20, max: 100)

    Returns:
        Paginated list of templates with metadata
    """
    try:
        templates, total = await template_service.list_templates(
            db=db,
            category=category,
            is_public=is_public,
            is_featured=is_featured,
            search=search,
            skip=skip,
            limit=limit,
        )

        page = (skip // limit) + 1 if limit > 0 else 1
        has_next = (skip + limit) < total

        return TemplateListResponse(
            templates=templates,
            total=total,
            page=page,
            page_size=limit,
            has_next=has_next,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list templates: {str(e)}",
        )


# ============================================================================
# GET /templates/categories - Get Categories
# ============================================================================


@router.get("/categories", response_model=TemplateCategoryResponse)
async def get_categories(
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of template categories.

    Public endpoint (no authentication required).

    Returns:
        List of distinct categories
    """
    try:
        categories = await template_service.get_categories(db=db)
        return TemplateCategoryResponse(
            categories=categories,
            total=len(categories),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get categories: {str(e)}",
        )


# ============================================================================
# GET /templates/featured - Get Featured Templates
# ============================================================================


@router.get("/featured", response_model=list[TemplateResponse])
async def get_featured_templates(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of templates"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get featured templates.

    Public endpoint (no authentication required).

    Args:
        limit: Maximum number of templates to return (default: 10, max: 50)

    Returns:
        List of featured templates
    """
    try:
        templates = await template_service.get_featured_templates(
            db=db,
            limit=limit,
        )
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get featured templates: {str(e)}",
        )


# ============================================================================
# GET /templates/popular - Get Popular Templates
# ============================================================================


@router.get("/popular", response_model=list[TemplateResponse])
async def get_popular_templates(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of templates"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get popular templates by use count.

    Public endpoint (no authentication required).

    Args:
        limit: Maximum number of templates to return (default: 10, max: 50)

    Returns:
        List of popular templates
    """
    try:
        templates = await template_service.get_popular_templates(
            db=db,
            limit=limit,
        )
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get popular templates: {str(e)}",
        )

@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a template by ID.

    Public endpoint (no authentication required).

    Args:
        template_id: Template ID
        db: Database session (injected)

    Returns:
        Template with all fields

    Raises:
        404: Template not found
        500: Internal server error
    """
    try:
        template = await template_service.get_template(db=db, template_id=template_id)
        return template
    except TemplateNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template: {str(e)}",
        )


# ============================================================================
# PUT /templates/{template_id} - Update Template
# ============================================================================


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    template_update: TemplateUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a template.

    Requires authentication. Only template creator or admin can update.

    Args:
        template_id: Template ID to update
        template_update: Template update data (all fields optional)
        current_user: Current authenticated user
        db: Database session (injected)

    Returns:
        Updated template

    Raises:
        400: Validation error
        401: Unauthorized
        403: Forbidden (not template creator)
        404: Template not found
        409: Conflict (duplicate name)
        500: Internal server error
    """
    try:
        # Get existing template to check ownership
        existing_template = await template_service.get_template(db, template_id)

        # Check if user is the creator (simple ownership check)
        # TODO: Add admin role check when RBAC is implemented
        if existing_template.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this template",
            )

        # Update template
        template = await template_service.update_template(
            db=db,
            template_id=template_id,
            template_update=template_update,
        )
        return template

    except TemplateNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except DuplicateTemplateNameError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except TemplateValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update template: {str(e)}",
        )


# ============================================================================
# DELETE /templates/{template_id} - Delete Template
# ============================================================================


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    hard_delete: bool = Query(False, description="Permanently delete (default: soft delete)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a template.

    Requires authentication. Only template creator or admin can delete.

    Args:
        template_id: Template ID to delete
        hard_delete: If true, permanently delete; if false, soft delete
        current_user: Current authenticated user
        db: Database session (injected)

    Raises:
        401: Unauthorized
        403: Forbidden (not template creator)
        404: Template not found
        500: Internal server error
    """
    try:
        # Get existing template to check ownership
        existing_template = await template_service.get_template(db, template_id)

        # Check if user is the creator
        if existing_template.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this template",
            )

        # Delete template
        await template_service.delete_template(
            db=db,
            template_id=template_id,
            hard_delete=hard_delete,
        )

    except TemplateNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete template: {str(e)}",
        )



# ============================================================================
# POST /templates/{template_id}/use - Increment Use Count
# ============================================================================


@router.post("/{template_id}/use", response_model=TemplateResponse)
async def increment_use_count(
    template_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Increment template use count.

    Public endpoint (no authentication required).
    Called when a template is used to create an agent.

    Args:
        template_id: Template ID
        db: Database session (injected)

    Returns:
        Updated template

    Raises:
        404: Template not found
        500: Internal server error
    """
    try:
        template = await template_service.increment_use_count(
            db=db,
            template_id=template_id,
        )
        return template
    except TemplateNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to increment use count: {str(e)}",
        )


# ============================================================================
# POST /templates/{template_id}/create-agent - Create Agent from Template
# ============================================================================


@router.post(
    "/{template_id}/create-agent",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_agent_from_template(
    template_id: int,
    agent_data: AgentFromTemplateCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create an agent from a template.

    Requires authentication.

    Args:
        template_id: Template ID (must match agent_data.template_id)
        agent_data: Agent creation data with template ID and overrides
        current_user: Current authenticated user
        db: Database session (injected)

    Returns:
        Created agent

    Raises:
        400: Validation error or template_id mismatch
        401: Unauthorized
        404: Template not found
        500: Internal server error
    """
    try:
        # Validate template_id matches
        if agent_data.template_id != template_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Template ID in path does not match template ID in request body",
            )

        # Create agent from template
        agent = await template_service.create_agent_from_template(
            db=db,
            agent_data=agent_data,
            user_id=current_user.id,
        )
        return agent

    except TemplateNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except TemplateValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agent from template: {str(e)}",
        )


# ============================================================================
# POST /templates/import - Import Template
# ============================================================================


@router.post("/import", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def import_template(
    template_data: TemplateImport,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Import a template from JSON.

    Requires authentication.

    Args:
        template_data: Template import data
        current_user: Current authenticated user
        db: Database session (injected)

    Returns:
        Created template

    Raises:
        400: Validation error
        401: Unauthorized
        409: Conflict (duplicate name)
        500: Internal server error
    """
    try:
        template = await template_service.import_template(
            db=db,
            template_data=template_data,
            created_by_id=current_user.id,
        )
        return template

    except DuplicateTemplateNameError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except TemplateValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import template: {str(e)}",
        )


# ============================================================================
# GET /templates/{template_id}/export - Export Template
# ============================================================================


@router.get("/{template_id}/export", response_model=TemplateExport)
async def export_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Export a template as JSON.

    Public endpoint (no authentication required).

    Args:
        template_id: Template ID to export
        db: Database session (injected)

    Returns:
        Template export data

    Raises:
        404: Template not found
        500: Internal server error
    """
    try:
        template_export = await template_service.export_template(
            db=db,
            template_id=template_id,
        )
        return template_export

    except TemplateNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export template: {str(e)}",
        )
