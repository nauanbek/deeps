"""
Trace Formatting and Processing Utilities.

This module provides utilities for formatting, filtering, and analyzing
execution traces from deepagents runs.
"""

from datetime import datetime
from typing import Any, Dict, List


class TraceFormatter:
    """
    Utilities for formatting and processing trace events.

    Provides methods to:
    - Format traces for UI display
    - Extract specific event types
    - Calculate execution timelines
    - Generate execution summaries
    """

    @staticmethod
    def format_trace_for_ui(trace: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format trace event for frontend display.

        Args:
            trace: Raw trace data from database

        Returns:
            Formatted trace with UI-friendly structure
        """
        return {
            "id": trace.get("id"),
            "sequence": trace.get("sequence_number"),
            "timestamp": trace.get("timestamp"),
            "type": trace.get("event_type"),
            "content": TraceFormatter._format_content(
                trace.get("content"), trace.get("event_type")
            ),
        }

    @staticmethod
    def _format_content(content: Any, event_type: str) -> Dict[str, Any]:
        """Format content based on event type."""
        if event_type == "tool_call":
            return {
                "tool_name": content.get("tool_name", "unknown"),
                "arguments": content.get("arguments", {}),
            }
        elif event_type == "tool_result":
            return {
                "tool_name": content.get("tool_name", "unknown"),
                "result": content.get("result"),
                "duration_ms": content.get("duration_ms"),
            }
        elif event_type == "llm_response":
            return {
                "message": content.get("content", ""),
                "tokens": content.get("usage", {}),
            }
        else:
            return content if isinstance(content, dict) else {"data": content}

    @staticmethod
    def extract_tool_calls(traces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract all tool call events from traces.

        Args:
            traces: List of trace dictionaries

        Returns:
            List of tool call traces
        """
        return [
            trace for trace in traces if trace.get("event_type") == "tool_call"
        ]

    @staticmethod
    def extract_llm_responses(traces: List[Dict[str, Any]]) -> List[str]:
        """
        Extract all LLM response text from traces.

        Args:
            traces: List of trace dictionaries

        Returns:
            List of LLM response strings
        """
        responses = []
        for trace in traces:
            if trace.get("event_type") == "llm_response":
                content = trace.get("content", {})
                if isinstance(content, dict):
                    responses.append(content.get("content", ""))
                elif isinstance(content, str):
                    responses.append(content)
        return responses

    @staticmethod
    def calculate_execution_timeline(
        traces: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate timeline metrics from traces.

        Args:
            traces: List of trace dictionaries

        Returns:
            Dict with timeline metrics (duration, event_counts, etc.)
        """
        if not traces:
            return {
                "total_duration_ms": 0,
                "event_counts": {},
                "start_time": None,
                "end_time": None,
            }

        # Sort by timestamp
        sorted_traces = sorted(
            traces, key=lambda t: t.get("timestamp", datetime.min)
        )

        start_time = sorted_traces[0].get("timestamp")
        end_time = sorted_traces[-1].get("timestamp")

        # Calculate duration
        if isinstance(start_time, datetime) and isinstance(end_time, datetime):
            duration_ms = (end_time - start_time).total_seconds() * 1000
        else:
            duration_ms = 0

        # Count event types
        event_counts: Dict[str, int] = {}
        for trace in traces:
            event_type = trace.get("event_type", "unknown")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        return {
            "total_duration_ms": duration_ms,
            "event_counts": event_counts,
            "start_time": start_time,
            "end_time": end_time,
            "total_events": len(traces),
        }

    @staticmethod
    def generate_execution_summary(
        traces: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive execution summary.

        Args:
            traces: List of trace dictionaries

        Returns:
            Dict with execution summary
        """
        timeline = TraceFormatter.calculate_execution_timeline(traces)
        tool_calls = TraceFormatter.extract_tool_calls(traces)
        llm_responses = TraceFormatter.extract_llm_responses(traces)

        return {
            "timeline": timeline,
            "tool_usage": {
                "total_calls": len(tool_calls),
                "unique_tools": len(
                    set(
                        tc.get("content", {}).get("tool_name")
                        for tc in tool_calls
                        if isinstance(tc.get("content"), dict)
                    )
                ),
            },
            "llm_interactions": {
                "total_responses": len(llm_responses),
                "total_characters": sum(len(r) for r in llm_responses),
            },
        }
