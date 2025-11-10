"""
Advanced configuration models for deepagents integration.

Models for backend configuration, long-term memory, HITL workflows,
and execution approvals.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database import Base

if TYPE_CHECKING:
    from .agent import Agent
    from .execution import Execution


class AgentBackendConfig(Base):
    """
    Backend storage configuration for agents.

    Supports multiple backend types:
    - state: Ephemeral in-state storage (default)
    - filesystem: Real or virtual filesystem access
    - store: Persistent cross-thread storage
    - composite: Hybrid storage with routing rules

    Configuration is stored as JSON to accommodate backend-specific settings.
    """

    __tablename__ = "agent_backend_configs"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Foreign key
    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,  # One backend config per agent
    )

    # Backend type
    backend_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # 'state', 'filesystem', 'store', 'composite'

    # Backend-specific configuration (JSON)
    # Examples:
    # - FilesystemBackend: {"root_dir": "/workspace", "virtual_mode": false}
    # - StoreBackend: {"namespace": "agent_123", "store_type": "postgresql"}
    # - CompositeBackend: {"routes": {"/memories/": "store", "/scratch/": "state"}}
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Audit trail
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )

    # Relationships
    agent: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="backend_config",
        foreign_keys=[agent_id],
    )

    # Indexes
    __table_args__ = (
        Index("idx_backend_configs_agent", "agent_id"),
        Index("idx_backend_configs_type", "backend_type"),
    )

    def __repr__(self) -> str:
        return f"<AgentBackendConfig(id={self.id}, agent_id={self.agent_id}, type='{self.backend_type}')>"


class AgentMemoryNamespace(Base):
    """
    Memory namespace configuration for long-term agent memory.

    Manages persistent storage namespaces for agents using StoreBackend.
    Each agent can have a dedicated namespace for /memories/ routing.

    Store types:
    - postgresql: PostgreSQL-backed store
    - redis: Redis-backed store
    - custom: Custom store implementation
    """

    __tablename__ = "agent_memory_namespaces"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Foreign key
    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,  # One namespace per agent
    )

    # Namespace (must be unique across all agents)
    namespace: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )

    # Store type
    store_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="postgresql"
    )  # 'postgresql', 'redis', 'custom'

    # Store-specific configuration
    # Examples:
    # - PostgreSQL: {"table_name": "agent_memory_files"}
    # - Redis: {"key_prefix": "agent:123:memory:"}
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Audit trail
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )

    # Relationships
    agent: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="memory_namespace",
        foreign_keys=[agent_id],
    )

    # Indexes
    __table_args__ = (
        Index("idx_memory_namespaces_agent", "agent_id"),
        Index("idx_memory_namespaces_namespace", "namespace"),
        Index("idx_memory_namespaces_store_type", "store_type"),
    )

    def __repr__(self) -> str:
        return f"<AgentMemoryNamespace(id={self.id}, namespace='{self.namespace}', agent_id={self.agent_id})>"


class AgentMemoryFile(Base):
    """
    Storage for long-term memory files in StoreBackend.

    Files stored in /memories/ path are persisted here across
    agent executions and threads.
    """

    __tablename__ = "agent_memory_files"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Namespace (links to AgentMemoryNamespace)
    namespace: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )

    # File key (path within /memories/)
    # Example: "context.md", "notes/project_info.txt"
    key: Mapped[str] = mapped_column(String(1024), nullable=False, index=True)

    # File content (stored as TEXT for text files, JSON for structured data)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    # File metadata
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    content_type: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # 'text/plain', 'application/json', etc.

    # Audit trail
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
    )

    # Composite unique constraint (namespace + key must be unique)
    __table_args__ = (
        UniqueConstraint("namespace", "key", name="uq_namespace_key"),
        Index("idx_memory_files_namespace", "namespace"),
        Index("idx_memory_files_namespace_key", "namespace", "key"),
        Index("idx_memory_files_updated", "updated_at"),
    )

    def __repr__(self) -> str:
        return f"<AgentMemoryFile(namespace='{self.namespace}', key='{self.key}', size={self.size_bytes})>"


class AgentInterruptConfig(Base):
    """
    Human-in-the-Loop (HITL) interrupt configuration for agent tools.

    Defines which tools require human approval before execution
    and what decisions are allowed (approve, edit, reject).

    This enables safety gates for destructive operations.
    """

    __tablename__ = "agent_interrupt_configs"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Foreign key
    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Tool name to interrupt on
    tool_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Allowed decisions (JSON array)
    # Examples:
    # - ["approve", "reject"]
    # - ["approve", "edit", "reject"]
    allowed_decisions: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )

    # Additional configuration
    # Examples:
    # - {"require_reason": true, "timeout_seconds": 300}
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Audit trail
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )

    # Relationships
    agent: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="interrupt_configs",
        foreign_keys=[agent_id],
    )

    # Composite unique constraint (one config per agent+tool)
    __table_args__ = (
        UniqueConstraint("agent_id", "tool_name", name="uq_agent_tool_interrupt"),
        Index("idx_interrupt_configs_agent", "agent_id"),
        Index("idx_interrupt_configs_tool", "tool_name"),
        Index("idx_interrupt_configs_agent_tool", "agent_id", "tool_name"),
    )

    def __repr__(self) -> str:
        return f"<AgentInterruptConfig(id={self.id}, agent_id={self.agent_id}, tool='{self.tool_name}')>"


class ExecutionApproval(Base):
    """
    Represents a pending or completed HITL approval request.

    When an agent execution hits an interrupt_on tool, it creates
    an approval request and pauses until a human makes a decision.

    Status values:
    - pending: Waiting for human decision
    - approved: Human approved, execution resumed
    - rejected: Human rejected, execution stopped
    - edited: Human edited args, execution resumed with new args
    """

    __tablename__ = "execution_approvals"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Foreign key
    execution_id: Mapped[int] = mapped_column(
        ForeignKey("executions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Tool information
    tool_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Original tool arguments (JSON)
    tool_args: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )

    # Approval status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", index=True
    )  # 'pending', 'approved', 'rejected', 'edited'

    # Decision data
    # If decision='edited', contains edited arguments
    # If decision='rejected', may contain rejection reason
    decision_data: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )

    # Decision metadata
    decided_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decided_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Audit trail
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    execution: Mapped["Execution"] = relationship(
        "Execution",
        back_populates="approvals",
        foreign_keys=[execution_id],
    )

    # Indexes for common query patterns
    __table_args__ = (
        Index("idx_approvals_execution", "execution_id"),
        Index("idx_approvals_status", "status"),
        Index("idx_approvals_execution_status", "execution_id", "status"),
        Index(
            "idx_approvals_pending", "status", "created_at"
        ),  # For pending approval queue
        Index("idx_approvals_tool", "tool_name"),
    )

    def __repr__(self) -> str:
        return f"<ExecutionApproval(id={self.id}, execution_id={self.execution_id}, tool='{self.tool_name}', status='{self.status}')>"
