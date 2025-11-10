"""
Tool Registry for managing LangChain tools available to agents.

This module provides a registry pattern for managing tools that can be
attached to deepagents instances.
"""

from typing import Dict, List, Optional

from langchain.tools import BaseTool


class ToolRegistry:
    """
    Registry for LangChain tools available to agents.

    Provides centralized management of tools including:
    - Built-in tools registration
    - Custom tool registration
    - Tool retrieval and listing
    - Tool instance creation for agents
    """

    def __init__(self):
        """Initialize the tool registry with built-in tools."""
        self.tools: Dict[str, BaseTool] = {}
        self._register_builtin_tools()

    def _register_builtin_tools(self):
        """
        Register built-in LangChain tools.

        This method registers metadata for built-in deepagents tools.
        deepagents provides these tools automatically when enabled:
        - Planning tools (write_todos)
        - Filesystem tools (read_file, write_file, edit_file, etc.)
        - LangGraph/LangChain tools
        """
        # Note: These are metadata descriptions of built-in tools.
        # Actual tool instances are provided by deepagents framework.
        pass

    def list_builtin_tools(self) -> List[Dict[str, str]]:
        """
        List all built-in tools available through deepagents.

        Returns:
            List of tool metadata dictionaries with name, description, type, and category
        """
        builtin_tools = [
            # Planning tools
            {
                "name": "write_todos",
                "description": "Create or update a task plan with structured todos. "
                              "Enables structured task decomposition and planning.",
                "type": "builtin",
                "category": "planning",
            },
            # Filesystem tools
            {
                "name": "read_file",
                "description": "Read the contents of a file from the virtual filesystem.",
                "type": "builtin",
                "category": "filesystem",
            },
            {
                "name": "write_file",
                "description": "Write content to a file in the virtual filesystem.",
                "type": "builtin",
                "category": "filesystem",
            },
            {
                "name": "edit_file",
                "description": "Edit an existing file in the virtual filesystem using search/replace.",
                "type": "builtin",
                "category": "filesystem",
            },
            {
                "name": "list_directory",
                "description": "List files and directories in the virtual filesystem.",
                "type": "builtin",
                "category": "filesystem",
            },
            {
                "name": "create_directory",
                "description": "Create a new directory in the virtual filesystem.",
                "type": "builtin",
                "category": "filesystem",
            },
            {
                "name": "delete_file",
                "description": "Delete a file from the virtual filesystem.",
                "type": "builtin",
                "category": "filesystem",
            },
        ]
        return builtin_tools

    def register_tool(self, name: str, tool: BaseTool):
        """
        Register a custom tool.

        Args:
            name: Unique name for the tool
            tool: LangChain BaseTool instance
        """
        self.tools[name] = tool

    def unregister_tool(self, name: str) -> bool:
        """
        Unregister a tool by name.

        Args:
            name: Name of the tool to remove

        Returns:
            True if tool was removed, False if not found
        """
        if name in self.tools:
            del self.tools[name]
            return True
        return False

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get tool by name.

        Args:
            name: Name of the tool

        Returns:
            BaseTool instance or None if not found
        """
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        """
        List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self.tools.keys())

    def get_tool_info(self, name: str) -> Optional[Dict[str, str]]:
        """
        Get tool information.

        Args:
            name: Name of the tool

        Returns:
            Dict with tool name and description, or None if not found
        """
        tool = self.tools.get(name)
        if tool:
            return {
                "name": tool.name,
                "description": tool.description,
            }
        return None

    def create_tools_for_agent(self, tool_names: List[str]) -> List[BaseTool]:
        """
        Create tool instances for an agent.

        Args:
            tool_names: List of tool names to include

        Returns:
            List of BaseTool instances

        Raises:
            ValueError: If any tool name is not found
        """
        tools = []
        for name in tool_names:
            tool = self.get_tool(name)
            if tool is None:
                raise ValueError(f"Tool '{name}' not found in registry")
            tools.append(tool)
        return tools

    def register_from_database(self, tool_configs: List[Dict]):
        """
        Register tools from database configurations.

        Args:
            tool_configs: List of tool configuration dictionaries
                         Each should have 'name', 'type', 'configuration'
        """
        # This would dynamically create tools from DB configs
        # Implementation depends on tool type system
        for config in tool_configs:
            tool_type = config.get("type")
            tool_name = config.get("name")

            # Example: could instantiate different tool types
            # based on the tool_type field
            # tool = self._create_tool_from_config(config)
            # self.register_tool(tool_name, tool)
            pass


# Singleton instance for convenience
tool_registry = ToolRegistry()
