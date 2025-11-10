"""
Agent model for AI agent configuration and management.

Represents deepagents-based AI agents with their configuration,
including model selection, system prompts, and feature flags.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
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
    from .advanced_config import (
        AgentBackendConfig,
        AgentInterruptConfig,
        AgentMemoryNamespace,
    )
    from .execution import Execution
    from .tool import Tool
    from .user import User


class Agent(Base):
    """
    Represents an AI agent configuration.

    Agents are the core entity of the platform, representing
    deepagents-based AI agents with specific model configurations,
    system prompts, and enabled features.

    Features:
    - planning_enabled: Enables planning tool (write_todos)
    - filesystem_enabled: Enables virtual filesystem middleware

    Configuration is flexible to support different model providers
    (Anthropic, OpenAI, etc.) and their specific parameters.

    Relationships:
    - Many-to-one with User (agent creator)
    - Many-to-many with Tool (via AgentTool)
    - One-to-many with Subagent (hierarchical agents)
    - One-to-many with Execution (agent runs)
    """

    __tablename__ = "agents"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Core identification
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Model configuration
    model_provider: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # anthropic, openai, etc.
    model_name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # claude-3-5-sonnet-20241022, gpt-4, etc.

    # Model parameters
    temperature: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.7
    )  # 0.0-1.0
    max_tokens: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Optional, uses model default if not set

    # System prompt (can be very long, hence TEXT)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # deepagents feature flags
    planning_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    filesystem_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )

    # Additional configuration as JSON for future extensibility
    # Example: {"max_iterations": 10, "custom_params": {...}}
    additional_config: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )

    # External tools integration (LangChain tools)
    # Array of external_tool_configs.id values stored as JSON
    # Example: [1, 2, 3] -> PostgreSQL tool, GitLab tool, Elasticsearch tool
    # Using JSON type for SQLite/PostgreSQL compatibility
    langchain_tool_ids: Mapped[Optional[list[int]]] = mapped_column(
        JSON, nullable=True
    )

    # Foreign keys
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
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

    # Soft delete support
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)

    # Relationships
    created_by_user: Mapped["User"] = relationship(
        "User",
        back_populates="agents",
        foreign_keys=[created_by_id],
    )

    agent_tools: Mapped[list["AgentTool"]] = relationship(
        "AgentTool",
        back_populates="agent",
        cascade="all, delete-orphan",
    )

    subagents: Mapped[list["Subagent"]] = relationship(
        "Subagent",
        back_populates="parent_agent",
        foreign_keys="[Subagent.agent_id]",
        cascade="all, delete-orphan",
    )

    executions: Mapped[list["Execution"]] = relationship(
        "Execution",
        back_populates="agent",
        cascade="all, delete-orphan",
    )

    # Advanced configuration relationships
    backend_config: Mapped[Optional["AgentBackendConfig"]] = relationship(
        "AgentBackendConfig",
        back_populates="agent",
        cascade="all, delete-orphan",
        uselist=False,  # One-to-one relationship
    )

    memory_namespace: Mapped[Optional["AgentMemoryNamespace"]] = relationship(
        "AgentMemoryNamespace",
        back_populates="agent",
        cascade="all, delete-orphan",
        uselist=False,  # One-to-one relationship
    )

    interrupt_configs: Mapped[list["AgentInterruptConfig"]] = relationship(
        "AgentInterruptConfig",
        back_populates="agent",
        cascade="all, delete-orphan",
    )

    # Composite indexes for common query patterns
    __table_args__ = (
        Index("idx_agents_created_by_active", "created_by_id", "is_active"),
        Index("idx_agents_provider_model", "model_provider", "model_name"),
        Index("idx_agents_features", "planning_enabled", "filesystem_enabled"),
        Index("idx_agents_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name='{self.name}', model='{self.model_provider}/{self.model_name}')>"


class AgentTool(Base):
    """
    Many-to-many association between Agents and Tools.

    Links agents to the tools they can use, with optional
    per-agent configuration overrides for each tool.

    This allows the same tool to be configured differently
    for different agents (e.g., different API keys, timeouts).
    """

    __tablename__ = "agent_tools"

    # Composite primary key
    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tool_id: Mapped[int] = mapped_column(
        ForeignKey("tools.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Tool-specific configuration override for this agent
    # Overrides or extends the base tool configuration
    configuration_override: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )

    # Audit trail
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    agent: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="agent_tools",
    )

    tool: Mapped["Tool"] = relationship(
        "Tool",
        back_populates="agent_tools",
    )

    # Indexes for foreign keys (automatically created for composite PK)
    __table_args__ = (
        Index("idx_agent_tools_agent", "agent_id"),
        Index("idx_agent_tools_tool", "tool_id"),
    )

    def __repr__(self) -> str:
        return f"<AgentTool(agent_id={self.agent_id}, tool_id={self.tool_id})>"


class Subagent(Base):
    """
    Represents a subagent relationship for hierarchical delegation.

    Subagents allow parent agents to delegate tasks to specialized
    child agents (which are also Agent instances), enabling complex
    multi-agent workflows.

    This is a many-to-many relationship between agents, where one agent
    can have multiple subagents, and an agent can be a subagent for
    multiple parent agents.
    """

    __tablename__ = "subagents"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Parent agent relationship (the agent that delegates)
    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Subagent relationship (the agent being delegated to)
    subagent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Delegation configuration
    delegation_prompt: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Priority for subagent selection (higher = higher priority)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Audit trail
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    parent_agent: Mapped["Agent"] = relationship(
        "Agent",
        foreign_keys=[agent_id],
        back_populates="subagents",
    )

    subagent: Mapped["Agent"] = relationship(
        "Agent",
        foreign_keys=[subagent_id],
    )

    # Indexes
    __table_args__ = (
        Index("idx_subagents_agent_id", "agent_id"),
        Index("idx_subagents_subagent_id", "subagent_id"),
        Index(
            "idx_subagents_agent_subagent",
            "agent_id",
            "subagent_id",
            unique=True,
        ),
        Index("idx_subagents_priority", "agent_id", "priority"),
    )

    def __repr__(self) -> str:
        return f"<Subagent(id={self.id}, agent_id={self.agent_id}, subagent_id={self.subagent_id}, priority={self.priority})>"
