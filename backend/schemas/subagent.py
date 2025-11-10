"""
Pydantic schemas for Subagent API endpoints.

Defines request/response models for subagent orchestration operations.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Base Schemas
# ============================================================================


class SubagentBase(BaseModel):
    """Base schema for Subagent with common fields."""

    subagent_id: int = Field(..., gt=0, description="ID of the agent to use as subagent")
    delegation_prompt: Optional[str] = Field(
        None, description="Optional system prompt override for this delegation"
    )
    priority: int = Field(
        0, description="Priority for subagent selection (higher = higher priority)"
    )


# ============================================================================
# Request Schemas
# ============================================================================


class SubagentCreate(SubagentBase):
    """Schema for creating a new subagent relationship."""

    pass


class SubagentUpdate(BaseModel):
    """Schema for updating an existing subagent relationship (all fields optional)."""

    delegation_prompt: Optional[str] = None
    priority: Optional[int] = None


# ============================================================================
# Response Schemas
# ============================================================================


class SubagentResponse(SubagentBase):
    """Schema for subagent response (includes database fields)."""

    id: int
    agent_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubagentWithAgentResponse(SubagentResponse):
    """Schema for subagent response with nested agent information."""

    subagent_name: str = Field(..., description="Name of the subagent")
    subagent_description: Optional[str] = Field(None, description="Description of the subagent")
    subagent_model_provider: str = Field(..., description="Model provider of the subagent")
    subagent_model_name: str = Field(..., description="Model name of the subagent")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Example Usage
# ============================================================================

# Example request body for adding a subagent to an agent:
# POST /api/v1/agents/1/subagents
# {
#     "subagent_id": 5,
#     "delegation_prompt": "You are a specialized code review agent",
#     "priority": 10
# }

# Example response:
# {
#     "id": 123,
#     "agent_id": 1,
#     "subagent_id": 5,
#     "delegation_prompt": "You are a specialized code review agent",
#     "priority": 10,
#     "created_at": "2025-01-08T12:00:00Z"
# }
