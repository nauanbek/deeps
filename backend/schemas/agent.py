"""
Pydantic schemas for Agent API endpoints.

Defines request/response models for agent CRUD operations.
"""

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Base Schemas
# ============================================================================


class AgentBase(BaseModel):
    """Base schema for Agent with common fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Agent name")
    description: Optional[str] = Field(None, description="Agent description")
    model_provider: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Model provider (anthropic, openai, etc.)",
    )
    model_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Model name (claude-3-5-sonnet-20241022, gpt-4, etc.)",
    )
    temperature: float = Field(
        0.7, ge=0.0, le=1.0, description="Model temperature (0.0-1.0)"
    )
    max_tokens: Optional[int] = Field(
        None, gt=0, description="Maximum tokens for completion"
    )
    system_prompt: Optional[str] = Field(None, description="System prompt for agent")
    planning_enabled: bool = Field(
        False, description="Enable planning tool (write_todos)"
    )
    filesystem_enabled: bool = Field(
        False, description="Enable virtual filesystem middleware"
    )
    additional_config: dict[str, Any] = Field(
        default_factory=dict, description="Additional configuration as JSON"
    )
    langchain_tool_ids: Optional[List[int]] = Field(
        None, description="External LangChain tool configuration IDs"
    )


# ============================================================================
# Request Schemas
# ============================================================================


class AgentCreate(AgentBase):
    """Schema for creating a new agent."""

    pass


class AgentUpdate(BaseModel):
    """Schema for updating an existing agent (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    model_provider: Optional[str] = Field(None, min_length=1, max_length=50)
    model_name: Optional[str] = Field(None, min_length=1, max_length=255)
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(None, gt=0)
    system_prompt: Optional[str] = None
    planning_enabled: Optional[bool] = None
    filesystem_enabled: Optional[bool] = None
    additional_config: Optional[dict[str, Any]] = None
    langchain_tool_ids: Optional[List[int]] = None


# ============================================================================
# Response Schemas
# ============================================================================


class AgentResponse(AgentBase):
    """Schema for agent response (includes database fields)."""

    id: int
    created_by_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class AgentListResponse(BaseModel):
    """Schema for paginated list of agents."""

    agents: list[AgentResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class AgentDetailResponse(AgentResponse):
    """Schema for detailed agent response (includes relationships)."""

    tool_count: int = Field(..., description="Number of tools configured")
    subagent_count: int = Field(..., description="Number of subagents configured")
    execution_count: int = Field(..., description="Total number of executions")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Tool Association Schemas
# ============================================================================


class AgentToolCreate(BaseModel):
    """Schema for adding a tool to an agent."""

    tool_id: int = Field(..., gt=0, description="Tool ID to add")
    configuration_override: dict[str, Any] = Field(
        default_factory=dict,
        description="Tool-specific configuration override",
    )


class AgentToolResponse(BaseModel):
    """Schema for agent-tool association response."""

    agent_id: int
    tool_id: int
    tool_name: str
    tool_type: str
    configuration_override: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Note: Subagent Schemas
# ============================================================================
# Subagent schemas have been moved to schemas/subagent.py to reflect the
# updated database schema where subagents are agent-to-agent relationships
# rather than separate entities with JSONB configuration.


# ============================================================================
# Example Usage
# ============================================================================

# Example request body for creating an agent:
# {
#     "name": "My Claude Agent",
#     "description": "An agent for research tasks",
#     "model_provider": "anthropic",
#     "model_name": "claude-3-5-sonnet-20241022",
#     "temperature": 0.7,
#     "max_tokens": 4096,
#     "system_prompt": "You are a helpful research assistant.",
#     "planning_enabled": true,
#     "filesystem_enabled": false,
#     "additional_config": {
#         "max_iterations": 10,
#         "custom_param": "value"
#     }
# }

# Example response:
# {
#     "id": 123,
#     "name": "My Claude Agent",
#     "description": "An agent for research tasks",
#     "model_provider": "anthropic",
#     "model_name": "claude-3-5-sonnet-20241022",
#     "temperature": 0.7,
#     "max_tokens": 4096,
#     "system_prompt": "You are a helpful research assistant.",
#     "planning_enabled": true,
#     "filesystem_enabled": false,
#     "additional_config": {"max_iterations": 10, "custom_param": "value"},
#     "created_by_id": 1,
#     "created_at": "2025-01-08T12:00:00Z",
#     "updated_at": null,
#     "is_active": true
# }
