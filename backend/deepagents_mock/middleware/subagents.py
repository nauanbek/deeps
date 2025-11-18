"""
Mock deepagents.middleware.subagents module.

Provides SubAgent class for hierarchical agent delegation.
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class SubAgent:
    """
    Mock SubAgent for hierarchical delegation.

    Represents a sub-agent that can be delegated to by a parent agent.
    """

    name: str
    description: str
    agent: Any
    config: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.config is None:
            self.config = {}


__all__ = ["SubAgent"]
