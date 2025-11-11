"""
Mock deepagents module to unblock testing.

This is a temporary mock implementation to allow tests to run while the actual
deepagents package dependency is resolved.

TODO: Replace with actual deepagents package once available.
"""

from typing import Any, Callable, Dict, List, Optional, Protocol


def create_deep_agent(
    model: Any,
    tools: Optional[List[Any]] = None,
    planning: bool = False,
    filesystem: bool = False,
    system_prompt: str = "",
    backend: Optional[Any] = None,
    **kwargs
) -> Any:
    """
    Mock implementation of create_deep_agent.

    Returns a mock agent object that can be used for testing.
    """
    from unittest.mock import MagicMock

    agent = MagicMock()
    agent.model = model
    agent.tools = tools or []
    agent.planning = planning
    agent.filesystem = filesystem
    agent.system_prompt = system_prompt
    agent.backend = backend

    # Mock astream method for execution
    async def mock_astream(inputs, config=None):
        """Mock async stream for agent execution."""
        yield {
            "type": "llm_response",
            "content": "Mock response from deepagents mock",
            "timestamp": "2025-11-11T00:00:00Z"
        }

    agent.astream = mock_astream
    agent.compile = MagicMock(return_value=agent)

    return agent


__all__ = ["create_deep_agent"]
