"""
External Tool models for LangChain tools integration.

Represents user-configured external tools (PostgreSQL, GitLab, Elasticsearch, HTTP APIs)
with encrypted credentials and execution logging.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database import Base

if TYPE_CHECKING:
    from .user import User


class ExternalToolConfig(Base):
    """
    Represents a user's external tool configuration.

    External tools are LangChain-based integrations (PostgreSQL, GitLab,
    Elasticsearch, HTTP APIs) configured with encrypted credentials.

    Each user can have multiple tool configurations, and agents can
    reference these tools via langchain_tool_ids.

    Security:
    - Credentials encrypted with Fernet (AES 128 CBC)
    - Multi-tenancy: All queries filter by user_id
    - Audit trail: All CRUD operations logged
    """

    __tablename__ = "external_tool_configs"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Foreign keys
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Tool identification
    tool_name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )  # e.g., "postgres_prod", "gitlab_company"

    tool_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # postgresql, gitlab, elasticsearch, http

    provider: Mapped[str] = mapped_column(
        String(50), nullable=False, default="langchain"
    )  # langchain (for now, composio later)

    # Tool configuration (JSONB with encrypted credentials)
    # Example for PostgreSQL: {
    #   "host": "localhost",
    #   "port": 5432,
    #   "database": "mydb",
    #   "username": "user",
    #   "password": "***ENCRYPTED***",  // Fernet-encrypted
    #   "ssl_mode": "require"
    # }
    configuration: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False
    )

    # Status tracking
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )

    # Connection test results
    last_tested_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    test_status: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # success, failed, not_tested
    test_error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    # Audit trail
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="external_tool_configs",
    )

    # Composite indexes for common query patterns
    __table_args__ = (
        Index("idx_external_tool_configs_user_active", "user_id", "is_active"),
        Index("idx_external_tool_configs_user_tool_name", "user_id", "tool_name", unique=True),
        Index("idx_external_tool_configs_tool_type", "tool_type"),
        Index("idx_external_tool_configs_provider", "provider"),
    )

    def __repr__(self) -> str:
        return f"<ExternalToolConfig(id={self.id}, user_id={self.user_id}, tool_name='{self.tool_name}', tool_type='{self.tool_type}')>"


class ToolExecutionLog(Base):
    """
    Logs every external tool execution for audit and analytics.

    Tracks tool usage, performance, success/failure rates, and errors
    for security auditing, debugging, and cost tracking.

    Retention: 30 days (configurable)
    """

    __tablename__ = "tool_execution_logs"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Foreign keys
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    execution_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("executions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    tool_config_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("external_tool_configs.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Tool execution details
    tool_name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    tool_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    tool_provider: Mapped[str] = mapped_column(
        String(50), nullable=False
    )

    # Execution data (sanitized - no sensitive info)
    input_params: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False
    )  # Sanitized input parameters

    output_summary: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Summary of output (not full output for large results)

    # Status
    success: Mapped[bool] = mapped_column(
        Boolean, nullable=False, index=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    # Performance metrics
    duration_ms: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # Execution duration in milliseconds

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    agent: Mapped[Optional["Agent"]] = relationship("Agent")
    execution: Mapped[Optional["Execution"]] = relationship("Execution")
    tool_config: Mapped[Optional["ExternalToolConfig"]] = relationship("ExternalToolConfig")

    # Composite indexes for analytics queries
    __table_args__ = (
        Index("idx_tool_execution_logs_user_created", "user_id", "created_at"),
        Index("idx_tool_execution_logs_agent_created", "agent_id", "created_at"),
        Index("idx_tool_execution_logs_execution", "execution_id"),
        Index("idx_tool_execution_logs_tool_name_success", "tool_name", "success"),
        Index("idx_tool_execution_logs_tool_type_created", "tool_type", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ToolExecutionLog(id={self.id}, tool_name='{self.tool_name}', success={self.success}, duration_ms={self.duration_ms})>"
