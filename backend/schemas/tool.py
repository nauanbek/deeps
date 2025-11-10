"""
Pydantic schemas for Tool API endpoints.

Defines request/response models for tool CRUD operations.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Base Schemas
# ============================================================================


class ToolBase(BaseModel):
    """Base schema for Tool with common fields."""

    name: str = Field(..., min_length=1, max_length=100, description="Tool name")
    description: Optional[str] = Field(None, description="Tool description")
    tool_type: str = Field(
        ...,
        description="Tool type: builtin, custom, or langgraph",
    )
    configuration: Optional[dict[str, Any]] = Field(
        default_factory=dict,
        description="Tool-specific configuration",
    )
    schema_definition: Optional[dict[str, Any]] = Field(
        default_factory=dict,
        description="Tool schema (inputs, outputs)",
    )


# ============================================================================
# Request Schemas
# ============================================================================


class ToolCreate(ToolBase):
    """Schema for creating a new tool."""

    pass


class ToolUpdate(BaseModel):
    """Schema for updating an existing tool (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    tool_type: Optional[str] = None
    configuration: Optional[dict[str, Any]] = None
    schema_definition: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None


# ============================================================================
# Response Schemas
# ============================================================================


class ToolResponse(ToolBase):
    """Schema for tool response (includes database fields)."""

    id: int
    is_active: bool
    created_by_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ToolListResponse(BaseModel):
    """Schema for paginated list of tools."""

    tools: list[ToolResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class ToolCategoryResponse(BaseModel):
    """Schema for tool categories response."""

    categories: list[str]


# ============================================================================
# Example Usage
# ============================================================================

# Example request body for creating a tool:
# {
#     "name": "calculator",
#     "description": "Performs mathematical calculations",
#     "tool_type": "builtin",
#     "configuration": {
#         "precision": 10
#     },
#     "schema_definition": {
#         "input": {
#             "type": "object",
#             "properties": {
#                 "expression": {"type": "string"}
#             }
#         },
#         "output": {
#             "type": "object",
#             "properties": {
#                 "result": {"type": "number"}
#             }
#         }
#     }
# }

# Example response:
# {
#     "id": 1,
#     "name": "calculator",
#     "description": "Performs mathematical calculations",
#     "tool_type": "builtin",
#     "configuration": {"precision": 10},
#     "schema_definition": {
#         "input": {...},
#         "output": {...}
#     },
#     "is_active": true,
#     "created_by_id": 1,
#     "created_at": "2025-01-08T12:00:00Z",
#     "updated_at": null
# }
