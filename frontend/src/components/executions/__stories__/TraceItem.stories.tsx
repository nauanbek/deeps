import type { Meta, StoryObj } from '@storybook/react';
import { TraceItem } from '../TraceItem';

const meta = {
  title: 'Components/Executions/TraceItem',
  component: TraceItem,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof TraceItem>;

export default meta;
type Story = StoryObj<typeof meta>;

export const ToolCall: Story = {
  args: {
    trace: {
      id: 1,
      execution_id: 1,
      sequence_number: 1,
      event_type: 'tool_call',
      content: {
        tool_name: 'web_search',
        arguments: { query: 'latest AI news' },
      },
      timestamp: '2025-11-10T12:00:00Z',
      created_at: '2025-11-10T12:00:00Z',
    },
    index: 0,
  },
};

export const ToolResult: Story = {
  args: {
    trace: {
      id: 2,
      execution_id: 1,
      sequence_number: 2,
      event_type: 'tool_result',
      content: {
        tool_name: 'web_search',
        result: 'Found 10 articles about AI developments...',
      },
      timestamp: '2025-11-10T12:00:05Z',
      created_at: '2025-11-10T12:00:05Z',
    },
    index: 1,
  },
};

export const LLMCall: Story = {
  args: {
    trace: {
      id: 3,
      execution_id: 1,
      sequence_number: 3,
      event_type: 'llm_call',
      content: {
        model: 'claude-3-5-sonnet-20241022',
        prompt: 'Summarize the latest AI news...',
      },
      timestamp: '2025-11-10T12:00:10Z',
      created_at: '2025-11-10T12:00:10Z',
    },
    index: 2,
  },
};

export const LLMResponse: Story = {
  args: {
    trace: {
      id: 4,
      execution_id: 1,
      sequence_number: 4,
      event_type: 'llm_response',
      content: {
        response: 'Here is a summary of the latest AI developments...',
        tokens_used: 256,
      },
      timestamp: '2025-11-10T12:00:15Z',
      created_at: '2025-11-10T12:00:15Z',
    },
    index: 3,
  },
};

export const PlanUpdate: Story = {
  args: {
    trace: {
      id: 5,
      execution_id: 1,
      sequence_number: 5,
      event_type: 'plan_update',
      content: {
        tasks: [
          { id: 1, title: 'Search for AI news', status: 'completed' },
          { id: 2, title: 'Analyze findings', status: 'in_progress' },
          { id: 3, title: 'Generate summary', status: 'pending' },
        ],
      },
      timestamp: '2025-11-10T12:00:20Z',
      created_at: '2025-11-10T12:00:20Z',
    },
    index: 4,
  },
};

export const ErrorTrace: Story = {
  args: {
    trace: {
      id: 6,
      execution_id: 1,
      sequence_number: 6,
      event_type: 'error',
      content: {
        error_message: 'API rate limit exceeded',
        error_type: 'RateLimitError',
      },
      timestamp: '2025-11-10T12:00:25Z',
      created_at: '2025-11-10T12:00:25Z',
    },
    index: 5,
  },
};

export const AgentStart: Story = {
  args: {
    trace: {
      id: 7,
      execution_id: 1,
      sequence_number: 0,
      event_type: 'agent_start',
      content: {
        agent_name: 'Research Assistant',
        input_text: 'Find latest AI news',
      },
      timestamp: '2025-11-10T12:00:00Z',
      created_at: '2025-11-10T12:00:00Z',
    },
    index: 0,
  },
};

export const AgentEnd: Story = {
  args: {
    trace: {
      id: 8,
      execution_id: 1,
      sequence_number: 10,
      event_type: 'agent_end',
      content: {
        status: 'completed',
        tokens_used: 1024,
      },
      timestamp: '2025-11-10T12:00:45Z',
      created_at: '2025-11-10T12:00:45Z',
    },
    index: 6,
  },
};

export const FilesystemOperation: Story = {
  args: {
    trace: {
      id: 9,
      execution_id: 1,
      sequence_number: 7,
      event_type: 'filesystem_operation',
      content: {
        operation: 'write_file',
        path: '/tmp/output.txt',
        size: 2048,
      },
      timestamp: '2025-11-10T12:00:35Z',
      created_at: '2025-11-10T12:00:35Z',
    },
    index: 7,
  },
};
