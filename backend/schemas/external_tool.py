"""
Pydantic schemas for External Tools API.

Request/response models for external tool configuration,
testing, and management.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Tool Configuration Schemas
# ============================================================================


class ExternalToolConfigBase(BaseModel):
    """Base schema for external tool configuration."""

    tool_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Unique tool name for this user (e.g., 'postgres_prod', 'gitlab_company')"
    )
    tool_type: str = Field(
        ...,
        description="Tool type: postgresql, gitlab, elasticsearch, http"
    )
    provider: str = Field(
        default="langchain",
        description="Tool provider: langchain (composio support later)"
    )
    configuration: Dict[str, Any] = Field(
        ...,
        description="Tool-specific configuration (credentials will be encrypted)"
    )

    @field_validator("tool_type")
    @classmethod
    def validate_tool_type(cls, v: str) -> str:
        """Validate tool_type is supported."""
        valid_types = ["postgresql", "gitlab", "elasticsearch", "http"]
        if v not in valid_types:
            raise ValueError(
                f"Invalid tool_type '{v}'. Must be one of: {', '.join(valid_types)}"
            )
        return v

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate provider is supported."""
        valid_providers = ["langchain"]  # composio support later
        if v not in valid_providers:
            raise ValueError(
                f"Invalid provider '{v}'. Must be one of: {', '.join(valid_providers)}"
            )
        return v


class ExternalToolConfigCreate(ExternalToolConfigBase):
    """Schema for creating external tool configuration."""
    pass


class ExternalToolConfigUpdate(BaseModel):
    """Schema for updating external tool configuration."""

    tool_name: Optional[str] = Field(None, min_length=1, max_length=255)
    configuration: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ExternalToolConfigResponse(ExternalToolConfigBase):
    """Schema for external tool configuration response."""

    id: int
    user_id: int
    is_active: bool
    last_tested_at: Optional[datetime] = None
    test_status: Optional[str] = None
    test_error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @field_validator("configuration", mode="before")
    @classmethod
    def sanitize_configuration(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize configuration to hide encrypted credentials."""
        from core.encryption import CredentialSanitizer

        return CredentialSanitizer.sanitize_dict(v)


# ============================================================================
# Connection Test Schemas
# ============================================================================


class ConnectionTestRequest(BaseModel):
    """Schema for connection test request (optional config override)."""

    configuration: Optional[Dict[str, Any]] = Field(
        None,
        description="Override configuration for testing (useful before saving)"
    )


class ConnectionTestResponse(BaseModel):
    """Schema for connection test response."""

    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    tested_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Tool Catalog Schemas
# ============================================================================


class ToolCatalogItem(BaseModel):
    """Schema for tool catalog item (marketplace)."""

    tool_type: str
    provider: str
    name: str
    description: str
    category: str  # database, git, logs, monitoring, http
    icon: Optional[str] = None
    required_fields: List[str]
    optional_fields: List[str]
    example_configuration: Dict[str, Any]


class ToolCatalogResponse(BaseModel):
    """Schema for tool catalog response."""

    langchain_tools: List[ToolCatalogItem]
    total: int


# ============================================================================
# Agent Tools Association Schemas
# ============================================================================


class AgentToolsUpdate(BaseModel):
    """Schema for updating agent's external tools."""

    langchain_tool_ids: List[int] = Field(
        default_factory=list,
        description="List of external_tool_configs.id to associate with agent"
    )


class AgentToolsResponse(BaseModel):
    """Schema for agent tools response."""

    agent_id: int
    langchain_tool_ids: List[int]
    tools: List[ExternalToolConfigResponse] = Field(
        default_factory=list,
        description="Full tool configurations for the agent"
    )


# ============================================================================
# Tool Execution Log Schemas
# ============================================================================


class ToolExecutionLogResponse(BaseModel):
    """Schema for tool execution log response."""

    id: int
    user_id: int
    agent_id: Optional[int] = None
    execution_id: Optional[int] = None
    tool_config_id: Optional[int] = None
    tool_name: str
    tool_type: str
    tool_provider: str
    input_params: Dict[str, Any]
    output_summary: Optional[str] = None
    success: bool
    error_message: Optional[str] = None
    duration_ms: int
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("input_params", mode="before")
    @classmethod
    def sanitize_input_params(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize input params to hide sensitive data."""
        from core.encryption import CredentialSanitizer

        return CredentialSanitizer.sanitize_dict(v)


# ============================================================================
# Tool Usage Analytics Schemas
# ============================================================================


class ToolUsageStats(BaseModel):
    """Schema for tool usage statistics."""

    tool_name: str
    tool_type: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float = Field(..., ge=0.0, le=1.0)
    avg_duration_ms: float
    last_execution_at: Optional[datetime] = None


class ToolUsageAnalytics(BaseModel):
    """Schema for tool usage analytics response."""

    total_tools: int
    active_tools: int
    total_executions: int
    success_rate: float
    tools: List[ToolUsageStats]
    time_range: str = Field(
        default="last_30_days",
        description="Time range for analytics"
    )


# ============================================================================
# List Response with Pagination
# ============================================================================


class ExternalToolConfigListResponse(BaseModel):
    """Schema for paginated list of tool configurations."""

    items: List[ExternalToolConfigResponse]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
    has_more: bool


class ToolExecutionLogListResponse(BaseModel):
    """Schema for paginated list of tool execution logs."""

    items: List[ToolExecutionLogResponse]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
    has_more: bool
