"""
Plan model for agent execution plan storage.

Represents agent execution plans created using the deepagents planning tool.
Plans can be updated during execution as the agent progresses through tasks.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database import Base

if TYPE_CHECKING:
    from .execution import Execution


class Plan(Base):
    """
    Agent execution plan storage.

    Stores plans created by agents using the write_todos planning tool.
    Plans can be versioned to track updates during execution.

    A plan consists of a list of todos, each with:
    - id: Unique identifier within the plan
    - description: What needs to be done
    - status: Current state (pending, in_progress, completed, blocked)

    Example plan structure:
    {
        "todos": [
            {"id": 1, "description": "Research topic", "status": "completed"},
            {"id": 2, "description": "Write summary", "status": "in_progress"},
            {"id": 3, "description": "Review and edit", "status": "pending"}
        ]
    }
    """

    __tablename__ = "plans"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Foreign key to execution
    execution_id: Mapped[int] = mapped_column(
        ForeignKey("executions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Plan version - incremented when plan is updated
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Plan data - array of todo objects
    # Each todo has: {id, description, status}
    # Status can be: pending, in_progress, completed, blocked
    todos: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Audit trail
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    execution: Mapped["Execution"] = relationship("Execution", back_populates="plans")

    # Indexes for common query patterns
    __table_args__ = (
        Index("idx_plans_execution", "execution_id"),
        Index("idx_plans_execution_version", "execution_id", "version"),
        Index("idx_plans_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Plan(id={self.id}, execution_id={self.execution_id}, version={self.version}, todos={len(self.todos.get('todos', []))})>"
