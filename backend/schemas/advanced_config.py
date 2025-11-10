"""
Pydantic schemas for Advanced Configuration API endpoints.

Defines request/response models for backend configs, memory management,
and HITL configurations.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================================
# Backend Configuration Schemas
# ============================================================================


class BackendConfigBase(BaseModel):
    """Base schema for backend configuration."""

    backend_type: Literal["state", "filesystem", "store", "composite"] = Field(
        ..., description="Backend storage type"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Backend-specific configuration"
    )


class BackendConfigCreate(BackendConfigBase):
    """Schema for creating backend configuration."""

    @field_validator("config")
    @classmethod
    def validate_config(cls, v: Dict[str, Any], info) -> Dict[str, Any]:
        """Validate backend config based on type."""
        backend_type = info.data.get("backend_type")

        if backend_type == "filesystem":
            # Validate filesystem config
            if "root_dir" in v and ".." in v["root_dir"]:
                raise ValueError("root_dir cannot contain '..' (path traversal)")

        elif backend_type == "composite":
            # Validate composite routes
            if "routes" not in v or not isinstance(v["routes"], dict):
                raise ValueError("Composite backend requires 'routes' dictionary")

        return v


class BackendConfigUpdate(BaseModel):
    """Schema for updating backend configuration."""

    backend_type: Optional[
        Literal["state", "filesystem", "store", "composite"]
    ] = None
    config: Optional[Dict[str, Any]] = None

    @field_validator("config")
    @classmethod
    def validate_config(cls, v: Optional[Dict[str, Any]], info) -> Optional[Dict[str, Any]]:
        """Validate backend config if provided."""
        if v is None:
            return v

        backend_type = info.data.get("backend_type")
        if backend_type == "filesystem" and "root_dir" in v and ".." in v["root_dir"]:
            raise ValueError("root_dir cannot contain '..' (path traversal)")

        return v


class BackendConfigResponse(BackendConfigBase):
    """Schema for backend configuration response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# ============================================================================
# Memory Namespace Schemas
# ============================================================================


class MemoryNamespaceBase(BaseModel):
    """Base schema for memory namespace."""

    namespace: str = Field(..., min_length=1, max_length=255, description="Unique namespace identifier")
    store_type: Literal["postgresql", "redis", "custom"] = Field(
        "postgresql", description="Store type"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Store-specific configuration"
    )


class MemoryNamespaceCreate(BaseModel):
    """Schema for creating memory namespace (namespace auto-generated)."""

    store_type: Literal["postgresql", "redis", "custom"] = Field(
        "postgresql", description="Store type"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Store-specific configuration"
    )


class MemoryNamespaceResponse(MemoryNamespaceBase):
    """Schema for memory namespace response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class MemoryFileResponse(BaseModel):
    """Schema for memory file response."""

    model_config = ConfigDict(from_attributes=True)

    key: str = Field(..., description="File key (path)")
    size_bytes: int = Field(..., description="File size in bytes")
    content_type: Optional[str] = Field(None, description="Content type")
    created_at: datetime
    updated_at: datetime


class MemoryFileListResponse(BaseModel):
    """Schema for memory file list response."""

    namespace: str
    files: List[MemoryFileResponse]
    total_files: int
    total_size_bytes: int


class MemoryFileContentResponse(BaseModel):
    """Schema for memory file content response."""

    key: str
    value: str = Field(..., description="File content")
    size_bytes: int
    content_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class MemoryFileCreate(BaseModel):
    """Schema for creating memory file."""

    key: str = Field(..., min_length=1, max_length=1024, description="File key (path)")
    value: str = Field(..., description="File content")
    content_type: Optional[str] = Field("text/plain", description="Content type")


# ============================================================================
# HITL Interrupt Configuration Schemas
# ============================================================================


class InterruptConfigBase(BaseModel):
    """Base schema for interrupt configuration."""

    tool_name: str = Field(..., min_length=1, max_length=255, description="Tool name to interrupt on")
    allowed_decisions: List[Literal["approve", "edit", "reject"]] = Field(
        ..., min_length=1, description="Allowed decisions for this tool"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Additional interrupt configuration"
    )

    @field_validator("allowed_decisions")
    @classmethod
    def validate_decisions(cls, v: List[str]) -> List[str]:
        """Ensure unique decisions."""
        if len(v) != len(set(v)):
            raise ValueError("allowed_decisions must contain unique values")
        return v


class InterruptConfigCreate(InterruptConfigBase):
    """Schema for creating interrupt configuration."""

    pass


class InterruptConfigUpdate(BaseModel):
    """Schema for updating interrupt configuration."""

    allowed_decisions: Optional[List[Literal["approve", "edit", "reject"]]] = None
    config: Optional[Dict[str, Any]] = None

    @field_validator("allowed_decisions")
    @classmethod
    def validate_decisions(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Ensure unique decisions if provided."""
        if v is not None and len(v) != len(set(v)):
            raise ValueError("allowed_decisions must contain unique values")
        return v


class InterruptConfigResponse(InterruptConfigBase):
    """Schema for interrupt configuration response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class InterruptConfigListResponse(BaseModel):
    """Schema for interrupt configuration list response."""

    configs: List[InterruptConfigResponse]
    total: int


# ============================================================================
# Execution Approval Schemas
# ============================================================================


class ApprovalDecision(BaseModel):
    """Schema for approval decision."""

    decision: Literal["approve", "reject", "edit"] = Field(
        ..., description="Decision: approve, reject, or edit"
    )
    edited_args: Optional[Dict[str, Any]] = Field(
        None, description="Edited tool arguments (required if decision='edit')"
    )
    reason: Optional[str] = Field(None, description="Optional reason for decision")

    @field_validator("edited_args")
    @classmethod
    def validate_edited_args(cls, v: Optional[Dict[str, Any]], info) -> Optional[Dict[str, Any]]:
        """Ensure edited_args provided if decision is 'edit'."""
        decision = info.data.get("decision")
        if decision == "edit" and not v:
            raise ValueError("edited_args required when decision='edit'")
        return v


class ApprovalResponse(BaseModel):
    """Schema for approval response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    execution_id: int
    tool_name: str
    tool_args: Dict[str, Any]
    status: Literal["pending", "approved", "rejected", "edited"]
    decision_data: Dict[str, Any]
    decided_by_id: Optional[int] = None
    decided_at: Optional[datetime] = None
    created_at: datetime


class ApprovalListResponse(BaseModel):
    """Schema for approval list response."""

    approvals: List[ApprovalResponse]
    total: int
    pending_count: int


# ============================================================================
# Combined Configuration Schemas
# ============================================================================


class MemoryFilesInfo(BaseModel):
    """Information about memory files."""

    total_files: int = 0
    files: List[MemoryFileResponse] = Field(default_factory=list)


class InterruptConfigsInfo(BaseModel):
    """Information about interrupt configs."""

    total: int = 0
    configs: List[InterruptConfigResponse] = Field(default_factory=list)


class AgentAdvancedConfigResponse(BaseModel):
    """Combined response for all advanced configurations."""

    backend_config: Optional[BackendConfigResponse] = None
    memory_namespace: Optional[MemoryNamespaceResponse] = None
    memory_files: MemoryFilesInfo = Field(default_factory=MemoryFilesInfo)
    interrupt_configs: InterruptConfigsInfo = Field(default_factory=InterruptConfigsInfo)


class AgentAdvancedConfigUpdate(BaseModel):
    """Update multiple advanced configurations at once."""

    backend_config: Optional[BackendConfigCreate] = None
    memory_namespace: Optional[MemoryNamespaceCreate] = None
    interrupt_configs: Optional[List[InterruptConfigCreate]] = None
