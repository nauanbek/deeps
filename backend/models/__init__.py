"""
SQLAlchemy models for DeepAgents Control Platform.

Provides:
- User: User authentication and authorization
- Agent: AI agent configuration
- Tool: Tool registry for agent capabilities
- AgentTool: Many-to-many association between agents and tools
- Subagent: Hierarchical subagent configuration
- Execution: Agent execution tracking
- Trace: Granular execution event logging
- Plan: Agent execution plan storage (planning tool)
- Template: Pre-configured agent templates

Advanced configuration models:
- AgentBackendConfig: Backend storage configuration
- AgentMemoryNamespace: Long-term memory namespace configuration
- AgentMemoryFile: Persistent memory file storage
- AgentInterruptConfig: HITL interrupt configuration
- ExecutionApproval: HITL approval requests

External tools integration models:
- ExternalToolConfig: LangChain external tool configurations
- ToolExecutionLog: External tool execution audit logs

All models use async SQLAlchemy patterns with proper type hints.
"""

from .advanced_config import (
    AgentBackendConfig,
    AgentInterruptConfig,
    AgentMemoryFile,
    AgentMemoryNamespace,
    ExecutionApproval,
)
from .agent import Agent, AgentTool, Subagent
from .execution import Execution, Trace
from .external_tool import ExternalToolConfig, ToolExecutionLog
from .plan import Plan
from .template import Template
from .tool import Tool
from .user import User

__all__ = [
    "User",
    "Agent",
    "AgentTool",
    "Subagent",
    "Tool",
    "Template",
    "Execution",
    "Trace",
    "Plan",
    "AgentBackendConfig",
    "AgentMemoryNamespace",
    "AgentMemoryFile",
    "AgentInterruptConfig",
    "ExecutionApproval",
    "ExternalToolConfig",
    "ToolExecutionLog",
]
