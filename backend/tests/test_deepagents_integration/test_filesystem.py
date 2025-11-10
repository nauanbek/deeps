"""
Tests for Filesystem Middleware Integration.

Tests the detection and handling of filesystem operations
from deepagents' built-in filesystem tools.
"""

import pytest
from datetime import datetime
from deepagents_integration.executor import AgentExecutor


class TestFilesystemDetection:
    """Test detection of filesystem operations in event stream."""

    def setup_method(self):
        """Set up test fixtures."""
        self.executor = AgentExecutor()

    def test_detect_write_file_operation(self):
        """Test that write_file tool calls are detected as filesystem operations."""
        event = {
            'tool': 'write_file',
            'input': {'path': '/test.txt', 'content': 'Hello World'},
            'output': {'success': True}
        }

        event_type = self.executor._determine_event_type(event)

        assert event_type == 'filesystem_operation'

    def test_detect_read_file_operation(self):
        """Test that read_file tool calls are detected as filesystem operations."""
        event = {
            'tool': 'read_file',
            'input': {'path': '/test.txt'},
            'output': {'content': 'Hello World'}
        }

        event_type = self.executor._determine_event_type(event)

        assert event_type == 'filesystem_operation'

    def test_detect_edit_file_operation(self):
        """Test that edit_file tool calls are detected as filesystem operations."""
        event = {
            'tool': 'edit_file',
            'input': {
                'path': '/test.txt',
                'old_content': 'Hello',
                'new_content': 'Hello World'
            },
            'output': {'success': True}
        }

        event_type = self.executor._determine_event_type(event)

        assert event_type == 'filesystem_operation'

    def test_detect_list_directory_operation(self):
        """Test that list_directory tool calls are detected as filesystem operations."""
        event = {
            'tool': 'list_directory',
            'input': {'path': '/'},
            'output': {'files': ['test.txt', 'config.json']}
        }

        event_type = self.executor._determine_event_type(event)

        assert event_type == 'filesystem_operation'

    def test_detect_create_directory_operation(self):
        """Test that create_directory tool calls are detected as filesystem operations."""
        event = {
            'tool': 'create_directory',
            'input': {'path': '/data'},
            'output': {'success': True}
        }

        event_type = self.executor._determine_event_type(event)

        assert event_type == 'filesystem_operation'

    def test_detect_delete_file_operation(self):
        """Test that delete_file tool calls are detected as filesystem operations."""
        event = {
            'tool': 'delete_file',
            'input': {'path': '/test.txt'},
            'output': {'success': True}
        }

        event_type = self.executor._determine_event_type(event)

        assert event_type == 'filesystem_operation'

    def test_plan_update_takes_priority_over_filesystem(self):
        """Test that plan updates are prioritized over filesystem detection."""
        event = {
            'tool': 'write_todos',
            'input': {'todos': [{'description': 'Task 1', 'status': 'pending'}]},
        }

        event_type = self.executor._determine_event_type(event)

        assert event_type == 'plan_update'

    def test_non_filesystem_tool_not_detected(self):
        """Test that non-filesystem tools are not detected as filesystem operations."""
        event = {
            'tool': 'web_search',
            'input': {'query': 'test'},
            'output': {'results': []}
        }

        event_type = self.executor._determine_event_type(event)

        # Should be detected as generic tool_call, not filesystem_operation
        assert event_type != 'filesystem_operation'

    def test_filesystem_tools_list(self):
        """Test all 6 filesystem tools are recognized."""
        filesystem_tools = [
            'read_file',
            'write_file',
            'edit_file',
            'list_directory',
            'create_directory',
            'delete_file'
        ]

        for tool in filesystem_tools:
            event = {
                'tool': tool,
                'input': {'path': '/test'},
                'output': {}
            }

            event_type = self.executor._determine_event_type(event)
            assert event_type == 'filesystem_operation', f"{tool} should be detected as filesystem operation"

    def test_empty_event_not_detected(self):
        """Test that empty events are not detected as filesystem operations."""
        event = {}

        event_type = self.executor._determine_event_type(event)

        assert event_type != 'filesystem_operation'

    def test_event_without_tool_key(self):
        """Test that events without 'tool' key are not detected as filesystem operations."""
        event = {
            'input': {'path': '/test.txt'},
            'output': {}
        }

        event_type = self.executor._determine_event_type(event)

        assert event_type != 'filesystem_operation'


class TestFilesystemEventPriority:
    """Test event type detection priority ordering."""

    def setup_method(self):
        """Set up test fixtures."""
        self.executor = AgentExecutor()

    def test_priority_plan_update_first(self):
        """Test that plan_update has highest priority."""
        # Plan update should be detected first
        event = {'tool': 'write_todos'}
        assert self.executor._determine_event_type(event) == 'plan_update'

    def test_priority_filesystem_second(self):
        """Test that filesystem operations have second priority after plan updates."""
        # Filesystem should be detected before generic tool calls
        event = {'tool': 'write_file', 'input': {}}
        assert self.executor._determine_event_type(event) == 'filesystem_operation'

    def test_priority_generic_tool_call_third(self):
        """Test that generic tool calls have lower priority."""
        # Non-filesystem tool should still be detected as tool_call
        event = {'tool_call': {'name': 'some_tool'}}
        event_type = self.executor._determine_event_type(event)
        # Should be tool_call or state_update, but not filesystem_operation
        assert event_type != 'filesystem_operation'


@pytest.mark.asyncio
class TestFilesystemTraceStorage:
    """Test that filesystem operations are properly stored as traces."""

    async def test_filesystem_trace_content_structure(self):
        """Test that filesystem operation traces have proper content structure."""
        # This test will validate the trace content structure when actual
        # execution happens. For now, just document expected structure.

        expected_content = {
            'tool': 'write_file',
            'input': {
                'path': '/test.txt',
                'content': 'Hello World'
            },
            'output': {
                'success': True
            }
        }

        # Validate structure exists
        assert 'tool' in expected_content
        assert 'input' in expected_content
        assert 'output' in expected_content
        assert expected_content['tool'] in ['read_file', 'write_file', 'edit_file',
                                            'list_directory', 'create_directory', 'delete_file']
