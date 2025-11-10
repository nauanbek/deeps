"""
Template Service Layer for business logic.

Handles all template-related business operations including:
- Template CRUD operations
- Search and filtering
- Import/export functionality
- Agent creation from templates
- Usage tracking
"""

from typing import Any, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent import Agent
from models.template import Template
from models.tool import Tool
from schemas.agent import AgentCreate
from schemas.template import (
    AgentFromTemplateCreate,
    TemplateCreate,
    TemplateExport,
    TemplateImport,
    TemplateUpdate,
)


# ============================================================================
# Custom Exceptions
# ============================================================================


class TemplateServiceError(Exception):
    """Base exception for template service errors."""

    pass


class TemplateNotFoundError(TemplateServiceError):
    """Raised when a template is not found."""

    def __init__(self, template_id: int):
        self.template_id = template_id
        super().__init__(f"Template with id {template_id} not found")


class TemplateValidationError(TemplateServiceError):
    """Raised when template validation fails."""

    pass


class DuplicateTemplateNameError(TemplateServiceError):
    """Raised when template name already exists."""

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Template with name '{name}' already exists")


# ============================================================================
# Template Service
# ============================================================================


class TemplateService:
    """
    Service layer for template management business logic.

    Provides methods for:
    - Creating templates with validation
    - Retrieving templates by ID, name, or listing with filters
    - Updating template configurations
    - Soft/hard deleting templates
    - Searching templates
    - Importing/exporting templates
    - Creating agents from templates
    - Tracking usage statistics
    """

    async def create_template(
        self,
        db: AsyncSession,
        template_data: TemplateCreate,
        created_by_id: int,
    ) -> Template:
        """
        Create a new template.

        Args:
            db: Database session
            template_data: Template creation data
            created_by_id: ID of user creating the template

        Returns:
            Created template instance

        Raises:
            DuplicateTemplateNameError: If template name already exists
            TemplateValidationError: If validation fails
        """
        # Validate template name uniqueness
        await self._validate_name_unique(db, template_data.name)

        # Validate tools referenced in config_template
        await self._validate_tool_ids(
            db, template_data.config_template.tool_ids
        )

        # Create template instance
        template = Template(
            name=template_data.name,
            description=template_data.description,
            category=template_data.category.value,
            tags=template_data.tags,
            config_template=template_data.config_template.model_dump(),
            is_public=template_data.is_public,
            is_featured=template_data.is_featured,
            use_count=0,
            created_by_id=created_by_id,
            is_active=True,
        )

        db.add(template)
        await db.flush()
        await db.refresh(template)

        return template

    async def get_template(
        self,
        db: AsyncSession,
        template_id: int,
        include_inactive: bool = False,
    ) -> Template:
        """
        Get a template by ID.

        Args:
            db: Database session
            template_id: Template ID
            include_inactive: Whether to include soft-deleted templates

        Returns:
            Template instance

        Raises:
            TemplateNotFoundError: If template not found
        """
        query = select(Template).where(Template.id == template_id)

        if not include_inactive:
            query = query.where(Template.is_active == True)

        result = await db.execute(query)
        template = result.scalar_one_or_none()

        if not template:
            raise TemplateNotFoundError(template_id)

        return template

    async def get_template_by_name(
        self,
        db: AsyncSession,
        name: str,
        include_inactive: bool = False,
    ) -> Optional[Template]:
        """
        Get a template by name.

        Args:
            db: Database session
            name: Template name
            include_inactive: Whether to include soft-deleted templates

        Returns:
            Template instance or None if not found
        """
        query = select(Template).where(Template.name == name)

        if not include_inactive:
            query = query.where(Template.is_active == True)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def list_templates(
        self,
        db: AsyncSession,
        category: Optional[str] = None,
        is_public: Optional[bool] = None,
        is_featured: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Template], int]:
        """
        List templates with filtering and pagination.

        Args:
            db: Database session
            category: Filter by category
            is_public: Filter by public/private
            is_featured: Filter by featured status
            search: Search in name, description, and tags
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return

        Returns:
            Tuple of (templates list, total count)
        """
        # Build base query
        query = select(Template).where(Template.is_active == True)

        # Apply filters
        if category:
            query = query.where(Template.category == category)

        if is_public is not None:
            query = query.where(Template.is_public == is_public)

        if is_featured is not None:
            query = query.where(Template.is_featured == is_featured)

        if search:
            search_term = f"%{search.lower()}%"
            query = query.where(
                or_(
                    func.lower(Template.name).like(search_term),
                    func.lower(Template.description).like(search_term),
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination and ordering
        query = query.order_by(Template.use_count.desc(), Template.created_at.desc())
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        templates = list(result.scalars().all())

        return templates, total

    async def update_template(
        self,
        db: AsyncSession,
        template_id: int,
        template_update: TemplateUpdate,
    ) -> Template:
        """
        Update an existing template.

        Args:
            db: Database session
            template_id: Template ID to update
            template_update: Template update data

        Returns:
            Updated template instance

        Raises:
            TemplateNotFoundError: If template not found
            DuplicateTemplateNameError: If new name conflicts
            TemplateValidationError: If validation fails
        """
        # Get existing template
        template = await self.get_template(db, template_id)

        # Validate name uniqueness if changed
        if template_update.name and template_update.name != template.name:
            await self._validate_name_unique(db, template_update.name)

        # Validate tool IDs if config_template is being updated
        if template_update.config_template:
            await self._validate_tool_ids(
                db, template_update.config_template.tool_ids
            )

        # Update fields
        update_data = template_update.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "category" and value:
                # Convert enum to string
                setattr(template, field, value.value)
            elif field == "config_template" and value:
                # Convert Pydantic model to dict
                setattr(template, field, value.model_dump())
            else:
                setattr(template, field, value)

        await db.flush()
        await db.refresh(template)

        return template

    async def delete_template(
        self,
        db: AsyncSession,
        template_id: int,
        hard_delete: bool = False,
    ) -> None:
        """
        Delete a template (soft or hard delete).

        Args:
            db: Database session
            template_id: Template ID to delete
            hard_delete: If True, permanently delete; if False, soft delete

        Raises:
            TemplateNotFoundError: If template not found
        """
        template = await self.get_template(db, template_id)

        if hard_delete:
            await db.delete(template)
        else:
            template.is_active = False

        await db.flush()

    async def count_templates(
        self,
        db: AsyncSession,
        category: Optional[str] = None,
        is_public: Optional[bool] = None,
        is_featured: Optional[bool] = None,
    ) -> int:
        """
        Count templates with filters.

        Args:
            db: Database session
            category: Filter by category
            is_public: Filter by public/private
            is_featured: Filter by featured status

        Returns:
            Count of templates matching filters
        """
        query = select(func.count()).select_from(Template).where(Template.is_active == True)

        if category:
            query = query.where(Template.category == category)

        if is_public is not None:
            query = query.where(Template.is_public == is_public)

        if is_featured is not None:
            query = query.where(Template.is_featured == is_featured)

        result = await db.execute(query)
        return result.scalar_one()

    async def get_categories(self, db: AsyncSession) -> list[str]:
        """
        Get list of distinct template categories.

        Args:
            db: Database session

        Returns:
            List of category names
        """
        query = (
            select(Template.category)
            .where(Template.is_active == True)
            .distinct()
            .order_by(Template.category)
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_featured_templates(
        self,
        db: AsyncSession,
        limit: int = 10,
    ) -> list[Template]:
        """
        Get featured templates.

        Args:
            db: Database session
            limit: Maximum number of templates to return

        Returns:
            List of featured templates
        """
        query = (
            select(Template)
            .where(and_(Template.is_active == True, Template.is_featured == True))
            .order_by(Template.use_count.desc(), Template.created_at.desc())
            .limit(limit)
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_popular_templates(
        self,
        db: AsyncSession,
        limit: int = 10,
    ) -> list[Template]:
        """
        Get popular templates by use count.

        Args:
            db: Database session
            limit: Maximum number of templates to return

        Returns:
            List of popular templates
        """
        query = (
            select(Template)
            .where(Template.is_active == True)
            .order_by(Template.use_count.desc(), Template.created_at.desc())
            .limit(limit)
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    async def search_templates(
        self,
        db: AsyncSession,
        query_text: str,
        limit: int = 20,
    ) -> list[Template]:
        """
        Full-text search for templates.

        Searches in name, description, and tags.

        Args:
            db: Database session
            query_text: Search query
            limit: Maximum number of results

        Returns:
            List of matching templates
        """
        search_term = f"%{query_text.lower()}%"

        query = (
            select(Template)
            .where(
                and_(
                    Template.is_active == True,
                    or_(
                        func.lower(Template.name).like(search_term),
                        func.lower(Template.description).like(search_term),
                    ),
                )
            )
            .order_by(Template.use_count.desc(), Template.created_at.desc())
            .limit(limit)
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    async def increment_use_count(
        self,
        db: AsyncSession,
        template_id: int,
    ) -> Template:
        """
        Increment template use count.

        Args:
            db: Database session
            template_id: Template ID

        Returns:
            Updated template instance

        Raises:
            TemplateNotFoundError: If template not found
        """
        template = await self.get_template(db, template_id)
        template.use_count += 1

        await db.flush()
        await db.refresh(template)

        return template

    async def import_template(
        self,
        db: AsyncSession,
        template_data: TemplateImport,
        created_by_id: int,
    ) -> Template:
        """
        Import a template from JSON.

        Args:
            db: Database session
            template_data: Template import data
            created_by_id: ID of user importing the template

        Returns:
            Created template instance

        Raises:
            DuplicateTemplateNameError: If template name already exists
            TemplateValidationError: If validation fails
        """
        # Convert to TemplateCreate schema
        create_data = TemplateCreate(
            name=template_data.name,
            description=template_data.description,
            category=template_data.category,
            tags=template_data.tags,
            config_template=template_data.config_template,
            is_public=template_data.is_public,
            is_featured=template_data.is_featured,
        )

        return await self.create_template(db, create_data, created_by_id)

    async def export_template(
        self,
        db: AsyncSession,
        template_id: int,
    ) -> TemplateExport:
        """
        Export a template to JSON.

        Args:
            db: Database session
            template_id: Template ID to export

        Returns:
            Template export data

        Raises:
            TemplateNotFoundError: If template not found
        """
        template = await self.get_template(db, template_id)

        return TemplateExport(
            name=template.name,
            description=template.description,
            category=template.category,
            tags=template.tags,
            config_template=template.config_template,
            metadata={
                "use_count": template.use_count,
                "is_featured": template.is_featured,
                "created_at": template.created_at.isoformat(),
            },
        )

    async def create_agent_from_template(
        self,
        db: AsyncSession,
        agent_data: AgentFromTemplateCreate,
        user_id: int,
    ) -> Agent:
        """
        Create an agent from a template.

        Args:
            db: Database session
            agent_data: Agent creation data with template ID
            user_id: ID of user creating the agent

        Returns:
            Created agent instance

        Raises:
            TemplateNotFoundError: If template not found
            TemplateValidationError: If validation fails
        """
        # Get template
        template = await self.get_template(db, agent_data.template_id)

        # Increment template use count
        await self.increment_use_count(db, template.id)

        # Merge template config with overrides
        config = template.config_template.copy()
        if agent_data.config_overrides:
            config.update(agent_data.config_overrides)

        # Create agent data from template
        agent_create = AgentCreate(
            name=agent_data.name,
            description=agent_data.description or template.description,
            model_provider=config.get("model_provider"),
            model_name=config.get("model_name"),
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens"),
            system_prompt=config.get("system_prompt"),
            planning_enabled=config.get("planning_enabled", False),
            filesystem_enabled=config.get("filesystem_enabled", False),
            additional_config=config.get("additional_config", {}),
        )

        # Create agent instance
        agent = Agent(
            name=agent_create.name,
            description=agent_create.description,
            model_provider=agent_create.model_provider,
            model_name=agent_create.model_name,
            temperature=agent_create.temperature,
            max_tokens=agent_create.max_tokens,
            system_prompt=agent_create.system_prompt,
            planning_enabled=agent_create.planning_enabled,
            filesystem_enabled=agent_create.filesystem_enabled,
            additional_config=agent_create.additional_config,
            created_by_id=user_id,
            is_active=True,
        )

        db.add(agent)
        await db.flush()
        await db.refresh(agent)

        # Add tools from template if specified
        tool_ids = config.get("tool_ids", [])
        if tool_ids:
            from models.agent import AgentTool

            for tool_id in tool_ids:
                # Verify tool exists
                tool_query = select(Tool).where(
                    and_(Tool.id == tool_id, Tool.is_active == True)
                )
                tool_result = await db.execute(tool_query)
                tool = tool_result.scalar_one_or_none()

                if tool:
                    agent_tool = AgentTool(
                        agent_id=agent.id,
                        tool_id=tool_id,
                        configuration_override={},
                    )
                    db.add(agent_tool)

        await db.flush()
        await db.refresh(agent)

        return agent

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    async def _validate_name_unique(
        self,
        db: AsyncSession,
        name: str,
        exclude_id: Optional[int] = None,
    ) -> None:
        """
        Validate that template name is unique.

        Args:
            db: Database session
            name: Template name to validate
            exclude_id: Template ID to exclude from check (for updates)

        Raises:
            DuplicateTemplateNameError: If name already exists
        """
        query = select(Template).where(
            and_(Template.name == name, Template.is_active == True)
        )

        if exclude_id:
            query = query.where(Template.id != exclude_id)

        result = await db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            raise DuplicateTemplateNameError(name)

    async def _validate_tool_ids(
        self,
        db: AsyncSession,
        tool_ids: list[int],
    ) -> None:
        """
        Validate that all tool IDs exist and are active.

        Args:
            db: Database session
            tool_ids: List of tool IDs to validate

        Raises:
            TemplateValidationError: If any tool ID is invalid
        """
        if not tool_ids:
            return

        # Query for all tool IDs
        query = select(Tool.id).where(
            and_(Tool.id.in_(tool_ids), Tool.is_active == True)
        )

        result = await db.execute(query)
        existing_ids = set(result.scalars().all())

        # Check if all tool IDs exist
        missing_ids = set(tool_ids) - existing_ids
        if missing_ids:
            raise TemplateValidationError(
                f"Invalid tool IDs: {sorted(missing_ids)}"
            )
