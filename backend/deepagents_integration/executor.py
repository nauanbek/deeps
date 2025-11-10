"""
Agent Executor for running deepagents and collecting traces.

This module provides the AgentExecutor class which handles:
- Agent execution with streaming support
- Trace collection and storage
- State management and error handling
- Token usage tracking
"""

from datetime import datetime
from typing import Any, AsyncIterator, Dict, Optional

from langgraph.graph.state import CompiledStateGraph
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.execution import Execution, Trace


class AgentExecutor:
    """
    Executor for running deepagents and collecting traces.

    Responsibilities:
    - Execute agents with input prompts
    - Stream execution events in real-time
    - Collect and save traces to database
    - Track execution status and errors
    - Calculate token usage and costs
    """

    async def execute_agent(
        self,
        agent: CompiledStateGraph,
        prompt: str,
        execution_id: int,
        db: AsyncSession,
        stream: bool = True,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Execute an agent and yield trace events.

        Args:
            agent: Compiled deepagents graph instance
            prompt: User input prompt
            execution_id: Database execution ID for trace storage
            db: Database session
            stream: Whether to stream events

        Yields:
            Trace events as dictionaries with event_type and content
        """
        sequence_number = 0

        try:
            # Update execution status to running
            await self._update_execution_status(db, execution_id, "running")
            await self._set_execution_start_time(db, execution_id)

            # Execute agent with streaming
            if stream:
                async for event in agent.astream({"messages": [{"role": "user", "content": prompt}]}):
                    # Create trace data
                    trace_data = {
                        "sequence_number": sequence_number,
                        "timestamp": datetime.utcnow(),
                        "event_type": self._determine_event_type(event),
                        "content": event,
                    }

                    # Save trace to database
                    await self._save_trace(db, execution_id, trace_data)

                    # Yield to WebSocket/caller
                    yield {
                        "sequence_number": sequence_number,
                        "timestamp": trace_data["timestamp"].isoformat(),
                        "event_type": trace_data["event_type"],
                        "content": event,
                    }
                    sequence_number += 1
            else:
                # Non-streaming execution
                result = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
                trace_data = {
                    "sequence_number": 0,
                    "timestamp": datetime.utcnow(),
                    "event_type": "completion",
                    "content": result,
                }
                await self._save_trace(db, execution_id, trace_data)
                yield {
                    "sequence_number": 0,
                    "timestamp": trace_data["timestamp"].isoformat(),
                    "event_type": "completion",
                    "content": result,
                }

            # Update execution as completed
            await self._update_execution_status(db, execution_id, "completed")
            await self._set_execution_end_time(db, execution_id)

        except Exception as e:
            await self._update_execution_status(
                db, execution_id, "failed", error_message=str(e)
            )
            await self._set_execution_end_time(db, execution_id)
            raise

    async def _update_execution_status(
        self,
        db: AsyncSession,
        execution_id: int,
        status: str,
        error_message: Optional[str] = None,
    ):
        """Update execution status in database."""
        stmt = (
            update(Execution)
            .where(Execution.id == execution_id)
            .values(status=status, error_message=error_message)
        )
        await db.execute(stmt)
        await db.commit()

    async def _set_execution_start_time(self, db: AsyncSession, execution_id: int):
        """Set execution start time."""
        stmt = (
            update(Execution)
            .where(Execution.id == execution_id)
            .values(started_at=datetime.utcnow())
        )
        await db.execute(stmt)
        await db.commit()

    async def _set_execution_end_time(self, db: AsyncSession, execution_id: int):
        """Set execution end time."""
        stmt = (
            update(Execution)
            .where(Execution.id == execution_id)
            .values(completed_at=datetime.utcnow())
        )
        await db.execute(stmt)
        await db.commit()

    async def _save_trace(
        self, db: AsyncSession, execution_id: int, trace_data: Dict[str, Any]
    ):
        """Save trace event to database."""
        trace = Trace(
            execution_id=execution_id,
            sequence_number=trace_data["sequence_number"],
            timestamp=trace_data["timestamp"],
            event_type=trace_data["event_type"],
            content=trace_data["content"],
        )
        db.add(trace)
        await db.commit()

    def _determine_event_type(self, event: Any) -> str:
        """
        Determine the event type from the event data.

        Maps LangGraph/deepagents event types to our trace types.

        Event types (priority order):
        - plan_update: write_todos tool calls or plan state updates (highest priority)
        - filesystem_operation: File system tool operations (read_file, write_file, etc.)
        - tool_call: Other tool invocations
        - tool_result: Tool execution results
        - llm_response: LLM message responses
        - llm_call: LLM invocation events
        - state_update: Generic state changes
        """
        if isinstance(event, dict):
            # Check for planning events first (highest priority)
            # write_todos tool call
            if "tool" in event and event.get("tool") == "write_todos":
                return "plan_update"

            # Plan state update from deepagents
            if "type" in event and event.get("type") == "plan_state":
                return "plan_update"

            # Check for filesystem operations (second priority)
            if "tool" in event:
                tool_name = event.get("tool", "")

                # deepagents filesystem tools (6 built-in tools)
                filesystem_tools = [
                    'read_file',
                    'write_file',
                    'edit_file',
                    'list_directory',
                    'create_directory',
                    'delete_file'
                ]

                if tool_name in filesystem_tools:
                    return "filesystem_operation"

            # Check for other tool events
            if "tool_calls" in event or "tool_call" in event:
                return "tool_call"

            if "tool_output" in event or "tool_result" in event:
                return "tool_result"

            # Check for LLM events
            if "llm_call" in event:
                return "llm_call"

            if "messages" in event or "llm_response" in event:
                return "llm_response"

        return "state_update"

    async def calculate_token_usage(
        self, db: AsyncSession, execution_id: int
    ) -> Dict[str, int]:
        """
        Calculate total token usage from traces.

        Returns:
            Dict with prompt_tokens, completion_tokens, total_tokens
        """
        # Fetch all traces for the execution
        stmt = select(Trace).where(Trace.execution_id == execution_id)
        result = await db.execute(stmt)
        traces = result.scalars().all()

        prompt_tokens = 0
        completion_tokens = 0

        for trace in traces:
            if isinstance(trace.content, dict):
                if "usage" in trace.content:
                    usage = trace.content["usage"]
                    prompt_tokens += usage.get("prompt_tokens", 0)
                    completion_tokens += usage.get("completion_tokens", 0)

        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }

    async def estimate_cost(
        self,
        model_provider: str,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """
        Estimate execution cost based on token usage.

        Args:
            model_provider: Provider name (anthropic, openai)
            model_name: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            Estimated cost in USD
        """
        # Simplified pricing (update with actual prices)
        pricing = {
            "anthropic": {
                "claude-3-5-sonnet-20241022": {
                    "prompt": 0.003 / 1000,  # $3 per 1M tokens
                    "completion": 0.015 / 1000,  # $15 per 1M tokens
                },
            },
            "openai": {
                "gpt-4": {
                    "prompt": 0.03 / 1000,  # $30 per 1M tokens
                    "completion": 0.06 / 1000,  # $60 per 1M tokens
                },
            },
        }

        if model_provider not in pricing:
            return 0.0

        model_pricing = pricing[model_provider].get(model_name, {})
        if not model_pricing:
            return 0.0

        prompt_cost = prompt_tokens * model_pricing.get("prompt", 0)
        completion_cost = completion_tokens * model_pricing.get("completion", 0)

        return prompt_cost + completion_cost


# Singleton instance for convenience
agent_executor = AgentExecutor()
