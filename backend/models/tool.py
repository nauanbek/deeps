"""
Tool model for agent tool registry.

Represents tools that can be attached to agents for extended capabilities.
Supports builtin tools, custom tools, and LangGraph tools.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database import Base

if TYPE_CHECKING:
    from .agent import AgentTool
    from .user import User


class Tool(Base):
    """
    Represents a tool that agents can use.

    Tools extend agent capabilities with functions like web search,
    code execution, database queries, API calls, etc.

    Tool types:
    - builtin: Pre-configured tools from deepagents/LangChain
    - custom: User-defined custom tools
    - langgraph: LangGraph-specific tools

    Configuration is stored in JSONB for flexibility, allowing
    each tool type to have different configuration requirements.

    Relationships:
    - Many-to-one with User (tool creator)
    - Many-to-many with Agent (via AgentTool)
    """

    __tablename__ = "tools"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Core fields
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Tool classification
    tool_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # builtin, custom, langgraph

    # Configuration stored as JSON for flexibility
    # Example: {"api_key": "...", "base_url": "...", "timeout": 30}
    configuration: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )

    # Tool schema definition (JSON Schema format)
    # Defines input parameters, types, and validation rules
    schema_definition: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )

    # Foreign keys
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Audit trail
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
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
        back_populates="tools",
    )

    agent_tools: Mapped[list["AgentTool"]] = relationship(
        "AgentTool",
        back_populates="tool",
        cascade="all, delete-orphan",
    )

    # Composite indexes for common query patterns
    __table_args__ = (
        Index("idx_tools_type_active", "tool_type", "is_active"),
        Index("idx_tools_name_type", "name", "tool_type"),
        Index("idx_tools_created_by", "created_by_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Tool(id={self.id}, name='{self.name}', type='{self.tool_type}')>"
