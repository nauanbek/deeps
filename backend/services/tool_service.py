"""
Tool service layer for managing tool CRUD operations.

Provides business logic for creating, reading, updating, and deleting tools
in the tool marketplace.
"""

from typing import Any, Optional

from loguru import logger
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.tool import Tool
from schemas.tool import ToolCreate, ToolUpdate


class ToolService:
    """Service layer for tool management."""

    async def create_tool(
        self,
        db: AsyncSession,
        tool_data: ToolCreate,
        created_by_id: int,
    ) -> Tool:
        """
        Create a new tool.

        Args:
            db: Database session
            tool_data: Tool creation data
            created_by_id: User creating the tool

        Returns:
            Created tool instance

        Raises:
            ValueError: If tool name already exists
        """
        # Check if tool name exists
        existing_query = select(Tool).where(Tool.name == tool_data.name)
        result = await db.execute(existing_query)
        existing_tool = result.scalar_one_or_none()

        if existing_tool:
            raise ValueError(f"Tool with name '{tool_data.name}' already exists")

        # Create tool
        tool = Tool(
            name=tool_data.name,
            description=tool_data.description,
            tool_type=tool_data.tool_type,
            configuration=tool_data.configuration or {},
            schema_definition=tool_data.schema_definition or {},
            created_by_id=created_by_id,
            is_active=True,
        )

        db.add(tool)
        await db.commit()
        await db.refresh(tool)

        logger.info(f"Created tool: {tool.name} (ID: {tool.id}, Type: {tool.tool_type})")

        return tool

    async def get_tool(
        self,
        db: AsyncSession,
        tool_id: int,
    ) -> Optional[Tool]:
        """
        Get tool by ID.

        Args:
            db: Database session
            tool_id: Tool ID

        Returns:
            Tool instance or None if not found
        """
        return await db.get(Tool, tool_id)

    async def list_tools(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        tool_type: Optional[str] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> list[Tool]:
        """
        List tools with optional filtering.

        Args:
            db: Database session
            skip: Pagination offset
            limit: Maximum results
            tool_type: Filter by tool type (builtin, custom, langgraph)
            search: Search in name and description
            is_active: Filter by active status

        Returns:
            List of tools
        """
        query = select(Tool)

        # Build filters
        conditions = []

        if tool_type:
            conditions.append(Tool.tool_type == tool_type)

        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    Tool.name.ilike(search_term),
                    Tool.description.ilike(search_term),
                )
            )

        if is_active is not None:
            conditions.append(Tool.is_active == is_active)

        if conditions:
            query = query.where(and_(*conditions))

        # Apply ordering and pagination
        query = query.order_by(Tool.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        tools = list(result.scalars().all())

        logger.debug(
            f"Listed tools: {len(tools)} results "
            f"(type={tool_type}, search={search}, active={is_active})"
        )

        return tools

    async def update_tool(
        self,
        db: AsyncSession,
        tool_id: int,
        tool_update: ToolUpdate,
    ) -> Tool:
        """
        Update tool.

        Args:
            db: Database session
            tool_id: Tool ID to update
            tool_update: Update data

        Returns:
            Updated tool instance

        Raises:
            ValueError: If tool not found
        """
        tool = await self.get_tool(db, tool_id)
        if not tool:
            raise ValueError(f"Tool {tool_id} not found")

        # Update fields
        update_data = tool_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tool, field, value)

        await db.commit()
        await db.refresh(tool)

        logger.info(f"Updated tool: {tool.name} (ID: {tool.id})")

        return tool

    async def delete_tool(
        self,
        db: AsyncSession,
        tool_id: int,
        hard_delete: bool = False,
    ) -> bool:
        """
        Delete tool (soft delete by default).

        Args:
            db: Database session
            tool_id: Tool ID to delete
            hard_delete: If True, permanently delete; if False, soft delete

        Returns:
            True if deleted, False if not found
        """
        tool = await self.get_tool(db, tool_id)
        if not tool:
            return False

        if hard_delete:
            await db.delete(tool)
            logger.info(f"Hard deleted tool: {tool.name} (ID: {tool.id})")
        else:
            tool.is_active = False
            logger.info(f"Soft deleted tool: {tool.name} (ID: {tool.id})")

        await db.commit()
        return True

    async def get_tool_categories(self, db: AsyncSession) -> list[str]:
        """
        Get list of tool types/categories.

        Args:
            db: Database session

        Returns:
            List of unique tool types
        """
        query = select(Tool.tool_type).distinct()
        result = await db.execute(query)
        categories = [row[0] for row in result.all()]

        logger.debug(f"Retrieved tool categories: {categories}")

        return categories

    async def count_tools(
        self,
        db: AsyncSession,
        tool_type: Optional[str] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> int:
        """
        Count tools with optional filtering.

        Args:
            db: Database session
            tool_type: Filter by tool type
            search: Search in name and description
            is_active: Filter by active status

        Returns:
            Total count of matching tools
        """
        query = select(Tool)

        # Build filters
        conditions = []

        if tool_type:
            conditions.append(Tool.tool_type == tool_type)

        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    Tool.name.ilike(search_term),
                    Tool.description.ilike(search_term),
                )
            )

        if is_active is not None:
            conditions.append(Tool.is_active == is_active)

        if conditions:
            query = query.where(and_(*conditions))

        result = await db.execute(query)
        return len(result.scalars().all())


# Singleton instance
tool_service = ToolService()
