"""
Tool Factory for loading and instantiating external tools.

This module provides the ToolFactory class which loads external tool
configurations from the database and creates LangChain tool instances
for agent execution.
"""

from typing import List, Optional

from langchain.tools import BaseTool
from loguru import logger
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from langchain_tools import (
    ElasticsearchTool,
    GitLabTool,
    HTTPClientTool,
    PostgreSQLTool,
)
from langchain_tools.execution_logger import wrap_tools_with_logging
from models.external_tool import ExternalToolConfig


class ToolFactory:
    """
    Factory for loading and instantiating external tools from database.

    Responsibilities:
    - Load external tool configurations from database
    - Instantiate tool wrappers (PostgreSQL, GitLab, Elasticsearch, HTTP)
    - Decrypt credentials automatically
    - Create LangChain tool instances
    - Validate tool configurations

    Usage:
        factory = ToolFactory()
        tools = await factory.get_tools_for_agent(agent_id, user_id, db)
    """

    # Tool type to class mapping
    TOOL_CLASSES = {
        "postgresql": PostgreSQLTool,
        "elasticsearch": ElasticsearchTool,
        "http": HTTPClientTool,
        "gitlab": GitLabTool,
    }

    async def get_tools_for_agent(
        self,
        agent_id: int,
        user_id: int,
        db: AsyncSession,
        tool_ids: Optional[List[int]] = None,
        execution_id: Optional[int] = None,
    ) -> List[BaseTool]:
        """
        Load and instantiate external tools for an agent.

        This method:
        1. Gets tool IDs from agent configuration or parameter
        2. Loads ExternalToolConfig records from database
        3. Validates tool ownership and active status
        4. Instantiates tool wrappers with decrypted credentials
        5. Creates LangChain tool instances
        6. Returns combined tool list

        Args:
            agent_id: Agent ID (for logging)
            user_id: User ID (for authorization)
            db: Database session
            tool_ids: Optional list of tool IDs to load (if not provided, loads from agent)
            execution_id: Optional execution ID for tool logging

        Returns:
            List[BaseTool]: List of LangChain tools ready for execution

        Raises:
            ValueError: If tool not found or validation fails
            ValueError: If unsupported tool type

        Example:
            tools = await factory.get_tools_for_agent(
                agent_id=123,
                user_id=1,
                db=session,
                tool_ids=[1, 2, 3]
            )
        """
        if not tool_ids:
            # No tools configured
            logger.info(f"No external tools configured for agent {agent_id}")
            return []

        # Load tool configurations from database
        stmt = select(ExternalToolConfig).where(
            and_(
                ExternalToolConfig.id.in_(tool_ids),
                ExternalToolConfig.user_id == user_id,
                ExternalToolConfig.is_active == True,
            )
        )

        result = await db.execute(stmt)
        tool_configs = result.scalars().all()

        if not tool_configs:
            logger.warning(
                f"No active tool configurations found for agent {agent_id}, "
                f"user {user_id}, tool_ids={tool_ids}"
            )
            return []

        # Track which tool IDs were found
        found_tool_ids = {config.id for config in tool_configs}
        missing_tool_ids = set(tool_ids) - found_tool_ids

        if missing_tool_ids:
            logger.warning(
                f"Some tool IDs not found or inactive for agent {agent_id}: "
                f"{missing_tool_ids}"
            )

        # Instantiate tools
        all_tools = []

        for tool_config in tool_configs:
            try:
                tools = await self._create_tools_from_config(tool_config)

                # Wrap tools with execution logging
                wrapped_tools = wrap_tools_with_logging(
                    tools=tools,
                    tool_config_id=tool_config.id,
                    tool_name=tool_config.tool_name,
                    tool_type=tool_config.tool_type,
                    user_id=user_id,
                    db_session=db,
                    agent_id=agent_id,
                    execution_id=execution_id,
                )

                all_tools.extend(wrapped_tools)
                logger.info(
                    f"Loaded {len(wrapped_tools)} tools from config '{tool_config.tool_name}' "
                    f"(type={tool_config.tool_type}, id={tool_config.id})"
                )
            except Exception as e:
                logger.error(
                    f"Failed to create tools from config '{tool_config.tool_name}' "
                    f"(id={tool_config.id}): {e}"
                )
                # Continue with other tools instead of failing completely
                continue

        logger.info(
            f"Successfully loaded {len(all_tools)} external tools for agent {agent_id}"
        )
        return all_tools

    async def _create_tools_from_config(
        self, tool_config: ExternalToolConfig
    ) -> List[BaseTool]:
        """
        Create LangChain tools from a tool configuration.

        Args:
            tool_config: Tool configuration from database

        Returns:
            List[BaseTool]: List of LangChain tools

        Raises:
            ValueError: If tool type is not supported
            Exception: If tool creation fails
        """
        # Get tool class
        tool_class = self.TOOL_CLASSES.get(tool_config.tool_type)
        if not tool_class:
            raise ValueError(f"Unsupported tool type: {tool_config.tool_type}")

        # Create tool wrapper instance
        # Note: Tool wrapper handles decryption automatically via BaseLangChainTool
        tool_wrapper = tool_class(tool_config.configuration)

        # Validate configuration
        await tool_wrapper.validate_config()

        # Create tools
        tools = await tool_wrapper.create_tools()

        return tools

    async def test_tool_connection(
        self, tool_id: int, user_id: int, db: AsyncSession
    ) -> dict:
        """
        Test connection to an external tool.

        Args:
            tool_id: Tool configuration ID
            user_id: User ID (for authorization)
            db: Database session

        Returns:
            dict: Connection test result with success status

        Raises:
            ValueError: If tool not found
        """
        # Load tool configuration
        stmt = select(ExternalToolConfig).where(
            and_(
                ExternalToolConfig.id == tool_id,
                ExternalToolConfig.user_id == user_id,
            )
        )

        result = await db.execute(stmt)
        tool_config = result.scalar_one_or_none()

        if not tool_config:
            raise ValueError(f"Tool configuration {tool_id} not found")

        # Get tool class
        tool_class = self.TOOL_CLASSES.get(tool_config.tool_type)
        if not tool_class:
            raise ValueError(f"Unsupported tool type: {tool_config.tool_type}")

        # Create tool wrapper and test connection
        tool_wrapper = tool_class(tool_config.configuration)
        result = await tool_wrapper.test_connection()

        return result

    def get_supported_tool_types(self) -> List[str]:
        """
        Get list of supported tool types.

        Returns:
            List[str]: List of supported tool type names
        """
        return list(self.TOOL_CLASSES.keys())

    def register_tool_type(self, tool_type: str, tool_class: type):
        """
        Register a custom tool type.

        Args:
            tool_type: Tool type name (e.g., "mongodb", "redis")
            tool_class: Tool wrapper class (must inherit from BaseLangChainTool)
        """
        self.TOOL_CLASSES[tool_type] = tool_class
        logger.info(f"Registered custom tool type: {tool_type}")


# Singleton instance for convenience
tool_factory = ToolFactory()
