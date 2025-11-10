"""
User model for authentication and authorization.

Represents platform users who create and manage agents.
Currently designed for single-user, but extensible to multi-user.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database import Base

if TYPE_CHECKING:
    from .agent import Agent
    from .execution import Execution
    from .external_tool import ExternalToolConfig
    from .template import Template
    from .tool import Tool


class User(Base):
    """
    Represents a platform user.

    Users can create and manage agents, tools, and view executions.
    Authentication is handled via username/password with JWT tokens.

    Relationships:
    - One-to-many with Agent (agents created by user)
    - One-to-many with Tool (tools created by user)
    - One-to-many with Execution (executions initiated by user)
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Authentication fields
    username: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

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
    agents: Mapped[list["Agent"]] = relationship(
        "Agent",
        back_populates="created_by_user",
        foreign_keys="Agent.created_by_id",
        cascade="all, delete-orphan",
    )

    tools: Mapped[list["Tool"]] = relationship(
        "Tool",
        back_populates="created_by_user",
        cascade="all, delete-orphan",
    )

    executions: Mapped[list["Execution"]] = relationship(
        "Execution",
        back_populates="created_by_user",
        cascade="all, delete-orphan",
    )

    templates: Mapped[list["Template"]] = relationship(
        "Template",
        back_populates="created_by_user",
        cascade="all, delete-orphan",
    )

    external_tool_configs: Mapped[list["ExternalToolConfig"]] = relationship(
        "ExternalToolConfig",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # Composite indexes
    __table_args__ = (
        Index("idx_users_active", "is_active"),
        Index("idx_users_username_active", "username", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
