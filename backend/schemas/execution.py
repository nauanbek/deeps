"""
Pydantic schemas for Execution and Trace API requests and responses.

Provides validation and serialization for:
- Execution creation requests
- Execution responses with status and metrics
- Trace event responses for real-time streaming
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ExecutionCreate(BaseModel):
    """
    Request schema for creating an execution.

    Attributes:
        agent_id: ID of the agent to execute
        prompt: User input prompt for the agent
        execution_params: Optional overrides for agent parameters
    """

    agent_id: int = Field(..., description="ID of agent to execute", gt=0)
    prompt: str = Field(..., min_length=1, description="User input prompt")
    execution_params: Dict[str, Any] = Field(
        default_factory=dict, description="Optional execution parameter overrides"
    )


class ExecutionResponse(BaseModel):
    """
    Response schema for execution.

    Contains complete execution information including:
    - Execution metadata (ID, agent, timestamps)
    - Status and error information
    - Token usage and cost estimation
    """

    id: int
    agent_id: int
    input_prompt: str
    execution_params: Dict[str, Any]
    status: str  # pending, running, completed, failed, cancelled
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_tokens: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    estimated_cost: Optional[Decimal] = None
    error_message: Optional[str] = None
    output: Dict[str, Any]
    created_at: datetime
    created_by_id: int

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class TraceResponse(BaseModel):
    """
    Response schema for trace event.

    Represents a single trace event during execution,
    used for real-time streaming and post-execution analysis.

    Attributes:
        id: Trace ID
        execution_id: Parent execution ID
        sequence_number: Order within execution (0, 1, 2, ...)
        timestamp: When the event occurred
        event_type: Type of event (tool_call, llm_response, etc.)
        content: Event data (flexible JSON structure)
        created_at: Database creation timestamp
    """

    id: int
    execution_id: int
    sequence_number: int
    timestamp: datetime
    event_type: str
    content: Dict[str, Any]
    created_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ExecutionListParams(BaseModel):
    """
    Query parameters for listing executions.

    Attributes:
        agent_id: Filter by agent ID
        status: Filter by execution status
        skip: Pagination offset
        limit: Pagination limit
    """

    agent_id: Optional[int] = Field(None, description="Filter by agent ID")
    status: Optional[str] = Field(None, description="Filter by status")
    skip: int = Field(0, ge=0, description="Pagination offset")
    limit: int = Field(100, ge=1, le=1000, description="Pagination limit")


class TraceListParams(BaseModel):
    """
    Query parameters for listing traces.

    Attributes:
        skip: Pagination offset
        limit: Pagination limit
    """

    skip: int = Field(0, ge=0, description="Pagination offset")
    limit: int = Field(1000, ge=1, le=10000, description="Pagination limit")
