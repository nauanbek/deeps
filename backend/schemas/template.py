"""
Pydantic schemas for Template API endpoints.

Defines request/response models for template CRUD operations,
import/export, and agent creation from templates.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================================
# Enums
# ============================================================================


class TemplateCategory(str, Enum):
    """Valid template categories."""

    RESEARCH = "research"
    CODING = "coding"
    CUSTOMER_SUPPORT = "customer_support"
    DATA_ANALYSIS = "data_analysis"
    CONTENT_WRITING = "content_writing"
    CODE_REVIEW = "code_review"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    GENERAL = "general"


# ============================================================================
# Configuration Template Schema
# ============================================================================


class ConfigTemplate(BaseModel):
    """Schema for agent configuration template."""

    model_provider: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Model provider (anthropic, openai, etc.)",
    )
    model_name: str = Field(
        ..., min_length=1, max_length=255, description="Model name"
    )
    system_prompt: str = Field(..., min_length=1, description="System prompt template")
    temperature: float = Field(
        0.7, ge=0.0, le=1.0, description="Model temperature (0.0-1.0)"
    )
    max_tokens: Optional[int] = Field(
        None, gt=0, description="Maximum tokens for completion"
    )
    planning_enabled: bool = Field(
        False, description="Enable planning tool (write_todos)"
    )
    filesystem_enabled: bool = Field(
        False, description="Enable virtual filesystem middleware"
    )
    tool_ids: list[int] = Field(
        default_factory=list, description="List of tool IDs to include"
    )
    additional_config: dict[str, Any] = Field(
        default_factory=dict, description="Additional configuration as JSON"
    )


# ============================================================================
# Base Schemas
# ============================================================================


class TemplateBase(BaseModel):
    """Base schema for Template with common fields."""

    name: str = Field(
        ..., min_length=3, max_length=200, description="Template name (unique)"
    )
    description: str = Field(
        ..., min_length=10, max_length=5000, description="Template description"
    )
    category: TemplateCategory = Field(..., description="Template category")
    tags: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Searchable tags (max 10)",
    )
    config_template: ConfigTemplate = Field(
        ..., description="Agent configuration template"
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate tags list."""
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")
        # Remove duplicates and empty strings
        tags = [tag.strip() for tag in v if tag.strip()]
        return list(dict.fromkeys(tags))  # Remove duplicates while preserving order


# ============================================================================
# Request Schemas
# ============================================================================


class TemplateCreate(TemplateBase):
    """Schema for creating a new template."""

    is_public: bool = Field(True, description="Make template public")
    is_featured: bool = Field(False, description="Mark as featured template")


class TemplateUpdate(BaseModel):
    """Schema for updating an existing template (all fields optional)."""

    name: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    category: Optional[TemplateCategory] = None
    tags: Optional[list[str]] = Field(None, max_length=10)
    config_template: Optional[ConfigTemplate] = None
    is_public: Optional[bool] = None
    is_featured: Optional[bool] = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Validate tags list."""
        if v is None:
            return None
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")
        # Remove duplicates and empty strings
        tags = [tag.strip() for tag in v if tag.strip()]
        return list(dict.fromkeys(tags))  # Remove duplicates while preserving order


# ============================================================================
# Response Schemas
# ============================================================================


class TemplateResponse(TemplateBase):
    """Schema for template response (includes database fields)."""

    id: int
    is_public: bool
    is_featured: bool
    use_count: int
    created_by_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TemplateListResponse(BaseModel):
    """Schema for paginated list of templates."""

    templates: list[TemplateResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class TemplateCategoryResponse(BaseModel):
    """Schema for category list response."""

    categories: list[str]
    total: int


# ============================================================================
# Import/Export Schemas
# ============================================================================


class TemplateImport(BaseModel):
    """Schema for importing template from JSON."""

    name: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    category: TemplateCategory
    tags: list[str] = Field(default_factory=list, max_length=10)
    config_template: ConfigTemplate
    is_public: bool = Field(True)
    is_featured: bool = Field(False)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate tags list."""
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")
        tags = [tag.strip() for tag in v if tag.strip()]
        return list(dict.fromkeys(tags))


class TemplateExport(BaseModel):
    """Schema for exporting template to JSON."""

    name: str
    description: str
    category: str
    tags: list[str]
    config_template: dict[str, Any]
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata (use_count, created_at, etc.)",
    )

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Agent Creation from Template
# ============================================================================


class AgentFromTemplateCreate(BaseModel):
    """Schema for creating an agent from a template."""

    template_id: int = Field(..., gt=0, description="Template ID to use")
    name: str = Field(
        ..., min_length=1, max_length=255, description="Agent name (override)"
    )
    description: Optional[str] = Field(
        None, description="Agent description (override)"
    )
    # Allow overriding any config template fields
    config_overrides: dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration overrides (optional)",
    )


# ============================================================================
# Example Usage
# ============================================================================

# Example request body for creating a template:
# {
#     "name": "Research Assistant Pro",
#     "description": "Advanced research assistant specialized in gathering...",
#     "category": "research",
#     "tags": ["research", "analysis", "information-gathering"],
#     "config_template": {
#         "model_provider": "anthropic",
#         "model_name": "claude-3-5-sonnet-20241022",
#         "system_prompt": "You are an expert research assistant...",
#         "temperature": 0.7,
#         "max_tokens": 4096,
#         "planning_enabled": true,
#         "filesystem_enabled": true,
#         "tool_ids": [1, 2, 3],
#         "additional_config": {"max_iterations": 15}
#     },
#     "is_public": true,
#     "is_featured": true
# }

# Example response:
# {
#     "id": 1,
#     "name": "Research Assistant Pro",
#     "description": "Advanced research assistant...",
#     "category": "research",
#     "tags": ["research", "analysis", "information-gathering"],
#     "config_template": {...},
#     "is_public": true,
#     "is_featured": true,
#     "use_count": 0,
#     "created_by_id": 1,
#     "created_at": "2025-01-08T12:00:00Z",
#     "updated_at": null,
#     "is_active": true
# }
