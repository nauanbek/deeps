"""
Tool Execution Logger wrapper for tracking external tool usage.

This module provides a wrapper that logs all external tool executions
to the tool_execution_logs table for audit trails and analytics.
"""

import time
from datetime import datetime
from typing import Any, Optional

from langchain.tools import BaseTool
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.encryption import CredentialSanitizer
from core.metrics_external_tools import record_tool_execution
from models.external_tool import ToolExecutionLog


class ToolExecutionLoggerWrapper(BaseTool):
    """
    Wrapper that logs external tool executions to database.

    This wrapper:
    - Records execution start/end times
    - Tracks success/failure status
    - Sanitizes input parameters (removes credentials)
    - Measures execution duration
    - Records metrics to Prometheus
    - Saves to tool_execution_logs table

    Usage:
        tool = SomeLangChainTool()
        wrapped = ToolExecutionLoggerWrapper(
            tool=tool,
            tool_config_id=123,
            tool_name="my_postgres",
            tool_type="postgresql",
            user_id=1,
            db_session=db
        )
    """

    name: str = "tool_execution_logger"
    description: str = "Logs tool executions"

    # Custom fields for logging
    wrapped_tool: BaseTool
    tool_config_id: int
    tool_name: str
    tool_type: str
    user_id: int
    db_session: Optional[AsyncSession] = None
    agent_id: Optional[int] = None
    execution_id: Optional[int] = None

    def __init__(
        self,
        wrapped_tool: BaseTool,
        tool_config_id: int,
        tool_name: str,
        tool_type: str,
        user_id: int,
        db_session: Optional[AsyncSession] = None,
        agent_id: Optional[int] = None,
        execution_id: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize the execution logger wrapper.

        Args:
            wrapped_tool: The LangChain tool to wrap
            tool_config_id: External tool config ID
            tool_name: User-defined tool name
            tool_type: Tool type (postgresql, gitlab, etc.)
            user_id: User ID for ownership
            db_session: Database session for logging
            agent_id: Optional agent ID for context
            execution_id: Optional execution ID for context
            **kwargs: Additional BaseTool parameters
        """
        # Use wrapped tool's name and description
        super().__init__(
            name=wrapped_tool.name,
            description=wrapped_tool.description,
            wrapped_tool=wrapped_tool,
            tool_config_id=tool_config_id,
            tool_name=tool_name,
            tool_type=tool_type,
            user_id=user_id,
            db_session=db_session,
            agent_id=agent_id,
            execution_id=execution_id,
            **kwargs,
        )

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """
        Synchronous execution with logging.

        This method:
        1. Records start time
        2. Executes wrapped tool
        3. Records end time and duration
        4. Logs to database
        5. Records Prometheus metrics
        6. Returns result

        Args:
            *args: Positional arguments for tool
            **kwargs: Keyword arguments for tool

        Returns:
            Tool execution result
        """
        start_time = time.time()
        success = False
        error_message = None
        result = None

        try:
            # Execute wrapped tool
            result = self.wrapped_tool._run(*args, **kwargs)
            success = True
            return result

        except Exception as e:
            success = False
            error_message = str(e)
            logger.error(
                f"Tool execution failed: {self.tool_name} "
                f"(type={self.tool_type}): {error_message}"
            )
            raise

        finally:
            # Calculate duration
            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)

            # Log to database (best effort, don't fail if logging fails)
            try:
                self._log_execution(
                    input_params=kwargs,
                    output_result=result if success else None,
                    success=success,
                    duration_ms=duration_ms,
                    error_message=error_message,
                )
            except Exception as log_error:
                logger.error(f"Failed to log tool execution: {log_error}")

            # Record Prometheus metrics
            try:
                record_tool_execution(
                    tool_type=self.tool_type,
                    tool_name=self.tool_name,
                    duration_seconds=duration_ms / 1000,
                    success=success,
                    user_id=self.user_id,
                )
            except Exception as metric_error:
                logger.error(f"Failed to record tool execution metric: {metric_error}")

    async def _arun(self, *args: Any, **kwargs: Any) -> Any:
        """
        Asynchronous execution with logging.

        Same as _run but for async tools.

        Args:
            *args: Positional arguments for tool
            **kwargs: Keyword arguments for tool

        Returns:
            Tool execution result
        """
        start_time = time.time()
        success = False
        error_message = None
        result = None

        try:
            # Execute wrapped tool
            if hasattr(self.wrapped_tool, "_arun"):
                result = await self.wrapped_tool._arun(*args, **kwargs)
            else:
                # Fallback to sync if async not available
                result = self.wrapped_tool._run(*args, **kwargs)
            success = True
            return result

        except Exception as e:
            success = False
            error_message = str(e)
            logger.error(
                f"Tool execution failed: {self.tool_name} "
                f"(type={self.tool_type}): {error_message}"
            )
            raise

        finally:
            # Calculate duration
            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)

            # Log to database (best effort)
            try:
                await self._log_execution_async(
                    input_params=kwargs,
                    output_result=result if success else None,
                    success=success,
                    duration_ms=duration_ms,
                    error_message=error_message,
                )
            except Exception as log_error:
                logger.error(f"Failed to log tool execution: {log_error}")

            # Record Prometheus metrics
            try:
                record_tool_execution(
                    tool_type=self.tool_type,
                    tool_name=self.tool_name,
                    duration_seconds=duration_ms / 1000,
                    success=success,
                    user_id=self.user_id,
                )
            except Exception as metric_error:
                logger.error(f"Failed to record tool execution metric: {metric_error}")

    def _log_execution(
        self,
        input_params: dict,
        output_result: Any,
        success: bool,
        duration_ms: int,
        error_message: Optional[str] = None,
    ):
        """
        Log execution to database (synchronous).

        Args:
            input_params: Tool input parameters (will be sanitized)
            output_result: Tool output result
            success: Whether execution succeeded
            duration_ms: Execution duration in milliseconds
            error_message: Error message if failed
        """
        if not self.db_session:
            return

        # Sanitize input parameters
        sanitized_params = CredentialSanitizer.sanitize_dict(input_params)

        # Create log entry
        log_entry = ToolExecutionLog(
            tool_config_id=self.tool_config_id,
            tool_name=self.tool_name,
            tool_type=self.tool_type,
            user_id=self.user_id,
            agent_id=self.agent_id,
            execution_id=self.execution_id,
            input_params=sanitized_params,
            output_result=str(output_result)[:5000] if output_result else None,  # Limit to 5000 chars
            success=success,
            duration_ms=duration_ms,
            error_message=error_message,
            created_at=datetime.utcnow(),
        )

        # Note: This is synchronous, so we can't await
        # In production, you might want to use a background task queue
        try:
            # Convert to sync session if needed
            # For now, we'll just create the object
            # The actual database insertion will happen when the session commits
            self.db_session.add(log_entry)
        except Exception as e:
            logger.error(f"Failed to add tool execution log to session: {e}")

    async def _log_execution_async(
        self,
        input_params: dict,
        output_result: Any,
        success: bool,
        duration_ms: int,
        error_message: Optional[str] = None,
    ):
        """
        Log execution to database (asynchronous).

        Args:
            input_params: Tool input parameters (will be sanitized)
            output_result: Tool output result
            success: Whether execution succeeded
            duration_ms: Execution duration in milliseconds
            error_message: Error message if failed
        """
        if not self.db_session:
            return

        # Sanitize input parameters
        sanitized_params = CredentialSanitizer.sanitize_dict(input_params)

        # Create log entry
        log_entry = ToolExecutionLog(
            tool_config_id=self.tool_config_id,
            tool_name=self.tool_name,
            tool_type=self.tool_type,
            user_id=self.user_id,
            agent_id=self.agent_id,
            execution_id=self.execution_id,
            input_params=sanitized_params,
            output_result=str(output_result)[:5000] if output_result else None,  # Limit to 5000 chars
            success=success,
            duration_ms=duration_ms,
            error_message=error_message,
            created_at=datetime.utcnow(),
        )

        self.db_session.add(log_entry)
        await self.db_session.commit()


def wrap_tools_with_logging(
    tools: list[BaseTool],
    tool_config_id: int,
    tool_name: str,
    tool_type: str,
    user_id: int,
    db_session: Optional[AsyncSession] = None,
    agent_id: Optional[int] = None,
    execution_id: Optional[int] = None,
) -> list[BaseTool]:
    """
    Wrap a list of tools with execution logging.

    Args:
        tools: List of LangChain tools to wrap
        tool_config_id: External tool config ID
        tool_name: User-defined tool name
        tool_type: Tool type
        user_id: User ID
        db_session: Database session
        agent_id: Optional agent ID
        execution_id: Optional execution ID

    Returns:
        List of wrapped tools with logging
    """
    wrapped_tools = []

    for tool in tools:
        wrapped = ToolExecutionLoggerWrapper(
            wrapped_tool=tool,
            tool_config_id=tool_config_id,
            tool_name=tool_name,
            tool_type=tool_type,
            user_id=user_id,
            db_session=db_session,
            agent_id=agent_id,
            execution_id=execution_id,
        )
        wrapped_tools.append(wrapped)

    return wrapped_tools
