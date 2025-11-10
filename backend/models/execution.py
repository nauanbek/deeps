"""
Execution and Trace models for agent run tracking and monitoring.

Execution represents a single agent run, while Trace captures
individual events during execution for real-time streaming and analysis.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DECIMAL, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database import Base

if TYPE_CHECKING:
    from .advanced_config import ExecutionApproval
    from .agent import Agent
    from .plan import Plan
    from .user import User


class Execution(Base):
    """
    Represents a single execution (run) of an agent.

    Tracks the complete lifecycle of an agent execution including:
    - Input prompt and parameters
    - Execution status and timing
    - Token usage and cost estimation
    - Error information if failed

    Status values:
    - pending: Execution queued but not started
    - running: Currently executing
    - completed: Successfully completed
    - failed: Execution failed with error
    - cancelled: User-cancelled execution

    Relationships:
    - Many-to-one with Agent (which agent was executed)
    - Many-to-one with User (who initiated the execution)
    - One-to-many with Trace (execution events)
    """

    __tablename__ = "executions"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Foreign keys
    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Execution input
    input_prompt: Mapped[str] = mapped_column(Text, nullable=False)

    # Execution parameters (optional overrides for agent config)
    # Example: {"temperature": 0.9, "max_tokens": 2000}
    execution_params: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )

    # Execution status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", index=True
    )  # pending, running, completed, failed, cancelled

    # Timing information
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Token usage tracking
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Cost estimation (stored as DECIMAL for financial precision)
    # Precision: 10 digits total, 6 decimal places (e.g., 9999.999999)
    estimated_cost: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(10, 6), nullable=True
    )

    # Error information (only populated if status is 'failed')
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_traceback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Final output (stored as JSON for structured results)
    # Example: {"result": "...", "artifacts": [...]}
    output: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )

    # Audit trail
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    agent: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="executions",
    )

    created_by_user: Mapped["User"] = relationship(
        "User",
        back_populates="executions",
    )

    traces: Mapped[list["Trace"]] = relationship(
        "Trace",
        back_populates="execution",
        cascade="all, delete-orphan",
        order_by="Trace.sequence_number",
    )

    plans: Mapped[list["Plan"]] = relationship(
        "Plan",
        back_populates="execution",
        cascade="all, delete-orphan",
        order_by="Plan.version",
    )

    approvals: Mapped[list["ExecutionApproval"]] = relationship(
        "ExecutionApproval",
        back_populates="execution",
        cascade="all, delete-orphan",
    )

    # Composite indexes for common query patterns
    __table_args__ = (
        Index("idx_executions_agent_status", "agent_id", "status"),
        Index("idx_executions_user_created", "created_by_id", "created_at"),
        Index("idx_executions_status_started", "status", "started_at"),
        Index(
            "idx_executions_agent_started", "agent_id", "started_at"
        ),  # For timeline views
        Index(
            "idx_executions_cost", "estimated_cost"
        ),  # For cost analysis (partial index could be used)
    )

    def __repr__(self) -> str:
        return f"<Execution(id={self.id}, agent_id={self.agent_id}, status='{self.status}')>"


class Trace(Base):
    """
    Represents an individual event during agent execution.

    Traces capture the granular events that occur during execution,
    enabling real-time streaming to UI and post-execution analysis.

    Event types:
    - tool_call: Agent is calling a tool
    - tool_result: Tool execution completed
    - llm_call: Making an LLM API call
    - llm_response: Received LLM response
    - plan_update: Planning tool updated task list
    - error: Error occurred during execution
    - log: General log message
    - state_update: Agent state changed

    Content is stored as JSON for flexibility, as different
    event types require different data structures.

    Relationships:
    - Many-to-one with Execution (parent execution)
    """

    __tablename__ = "traces"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Foreign key
    execution_id: Mapped[int] = mapped_column(
        ForeignKey("executions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Ordering within execution
    sequence_number: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True
    )  # 0, 1, 2, 3, ...

    # Event metadata
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # tool_call, tool_result, llm_call, etc.

    # Event content (flexible JSON structure)
    # Examples:
    # - tool_call: {"tool_name": "search", "arguments": {"query": "..."}}
    # - tool_result: {"tool_name": "search", "result": {...}, "duration_ms": 123}
    # - llm_call: {"model": "claude-3-5-sonnet", "prompt_tokens": 100}
    # - llm_response: {"content": "...", "completion_tokens": 50}
    # - plan_update: {"todos": [...]}
    # - error: {"error_type": "ToolError", "message": "...", "traceback": "..."}
    content: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )

    # Audit trail (single timestamp sufficient for traces)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    execution: Mapped["Execution"] = relationship(
        "Execution",
        back_populates="traces",
    )

    # Composite indexes for common query patterns
    __table_args__ = (
        Index(
            "idx_traces_execution_sequence", "execution_id", "sequence_number"
        ),  # For ordered retrieval
        Index("idx_traces_execution_timestamp", "execution_id", "timestamp"),
        Index("idx_traces_execution_type", "execution_id", "event_type"),
        Index(
            "idx_traces_timestamp", "timestamp"
        ),  # For global timeline queries across executions
    )

    def __repr__(self) -> str:
        return f"<Trace(id={self.id}, execution_id={self.execution_id}, type='{self.event_type}', seq={self.sequence_number})>"
