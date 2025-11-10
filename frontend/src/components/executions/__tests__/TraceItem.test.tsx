import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { TraceItem } from '../TraceItem';
import type { ExecutionTrace } from '../../../types/execution';

describe('TraceItem', () => {
  const baseTrace: ExecutionTrace = {
    execution_id: 1,
    sequence_number: 0,
    event_type: 'llm_call',
    content: {},
    timestamp: '2024-01-15T10:30:00Z',
  };

  it('renders llm_call trace correctly', () => {
    const trace: ExecutionTrace = {
      ...baseTrace,
      event_type: 'llm_call',
      content: {
        model: 'claude-3-5-sonnet-20241022',
        temperature: 0.7,
        max_tokens: 2000,
      },
    };

    render(<TraceItem trace={trace} index={0} />);

    expect(screen.getByText(/LLM Call/i)).toBeInTheDocument();
    expect(screen.getByText(/claude-3-5-sonnet-20241022/i)).toBeInTheDocument();
    expect(screen.getByText(/0.7/)).toBeInTheDocument();
  });

  it('renders llm_response trace correctly', () => {
    const trace: ExecutionTrace = {
      ...baseTrace,
      event_type: 'llm_response',
      content: {
        content: 'Paris is the capital of France.',
        tokens: 150,
      },
    };

    render(<TraceItem trace={trace} index={1} />);

    expect(screen.getByText(/LLM Response/i)).toBeInTheDocument();
    expect(screen.getByText(/Paris is the capital of France/i)).toBeInTheDocument();
    expect(screen.getByText(/150/)).toBeInTheDocument();
  });

  it('renders tool_call trace correctly', () => {
    const trace: ExecutionTrace = {
      ...baseTrace,
      event_type: 'tool_call',
      content: {
        tool: 'calculator',
        input: { expression: '2+2' },
      },
    };

    render(<TraceItem trace={trace} index={2} />);

    expect(screen.getByText(/Tool Call/i)).toBeInTheDocument();
    expect(screen.getByText(/calculator/i)).toBeInTheDocument();
  });

  it('renders tool_result trace correctly', () => {
    const trace: ExecutionTrace = {
      ...baseTrace,
      event_type: 'tool_result',
      content: {
        result: '4',
        success: true,
      },
    };

    render(<TraceItem trace={trace} index={3} />);

    expect(screen.getByText(/Tool Result/i)).toBeInTheDocument();
    expect(screen.getByText(/"4"/)).toBeInTheDocument();
  });

  it('renders error trace correctly', () => {
    const trace: ExecutionTrace = {
      ...baseTrace,
      event_type: 'error',
      content: {
        message: 'API key not configured',
        error_type: 'ConfigurationError',
      },
    };

    render(<TraceItem trace={trace} index={4} />);

    expect(screen.getAllByText(/Error/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/API key not configured/i)).toBeInTheDocument();
  });

  it('renders plan_update trace correctly', () => {
    const trace: ExecutionTrace = {
      ...baseTrace,
      event_type: 'plan_update',
      content: {
        plan: ['Task 1: Research topic', 'Task 2: Write summary'],
      },
    };

    render(<TraceItem trace={trace} index={5} />);

    expect(screen.getByText(/Plan Update/i)).toBeInTheDocument();
    expect(screen.getByText(/Task 1: Research topic/i)).toBeInTheDocument();
  });

  it('formats timestamp correctly', () => {
    const trace: ExecutionTrace = {
      ...baseTrace,
      timestamp: '2024-01-15T14:23:01Z',
    };

    render(<TraceItem trace={trace} index={0} />);

    // Should display time in format HH:mm:ss (actual time depends on timezone)
    expect(screen.getByText(/\d{2}:\d{2}:\d{2}/)).toBeInTheDocument();
  });

  it('displays step number correctly', () => {
    const trace: ExecutionTrace = {
      ...baseTrace,
      sequence_number: 5,
    };

    render(<TraceItem trace={trace} index={5} />);

    expect(screen.getByText(/\[5\]/)).toBeInTheDocument();
  });

  it('toggles content visibility when clicked', () => {
    const trace: ExecutionTrace = {
      ...baseTrace,
      event_type: 'llm_call',
      content: {
        model: 'claude-3-5-sonnet-20241022',
        temperature: 0.7,
      },
    };

    render(<TraceItem trace={trace} index={0} />);

    // Content should be visible initially
    expect(screen.getByText(/claude-3-5-sonnet-20241022/i)).toBeInTheDocument();

    // Click to collapse
    const header = screen.getByRole('button');
    fireEvent.click(header);

    // Content should be hidden
    expect(screen.queryByText(/claude-3-5-sonnet-20241022/i)).not.toBeInTheDocument();

    // Click to expand again
    fireEvent.click(header);

    // Content should be visible again
    expect(screen.getByText(/claude-3-5-sonnet-20241022/i)).toBeInTheDocument();
  });

  it('applies correct color badge for each trace type', () => {
    const traceTypes: Array<ExecutionTrace['event_type']> = [
      'llm_call',
      'llm_response',
      'tool_call',
      'tool_result',
      'error',
      'plan_update',
    ];

    traceTypes.forEach((type) => {
      const trace: ExecutionTrace = {
        ...baseTrace,
        event_type: type,
      };

      const { container } = render(<TraceItem trace={trace} index={0} />);

      // Each trace type should have a badge with appropriate color
      const badge = container.querySelector('.rounded-full');
      expect(badge).toBeInTheDocument();
    });
  });

  it('renders JSON data with syntax highlighting', () => {
    const trace: ExecutionTrace = {
      ...baseTrace,
      event_type: 'tool_call',
      content: {
        tool: 'test_tool',
        input: { key: 'value', number: 42 },
      },
    };

    const { container } = render(<TraceItem trace={trace} index={0} />);

    // Should render JSON content in a pre tag
    const preElements = container.querySelectorAll('pre');
    expect(preElements.length).toBeGreaterThan(0);

    // Check that the JSON is formatted
    const preText = preElements[0].textContent;
    expect(preText).toContain('key');
    expect(preText).toContain('value');
  });

  it('handles missing or null data gracefully', () => {
    const trace: ExecutionTrace = {
      ...baseTrace,
      content: {},
    };

    render(<TraceItem trace={trace} index={0} />);

    // Should render without crashing
    expect(screen.getByText(/LLM Call/i)).toBeInTheDocument();
  });

  it('truncates long content appropriately', () => {
    const longContent = 'A'.repeat(500);
    const trace: ExecutionTrace = {
      ...baseTrace,
      event_type: 'llm_response',
      content: {
        content: longContent,
      },
    };

    render(<TraceItem trace={trace} index={0} />);

    // Should display truncated content with ellipsis
    const contentElement = screen.getByText(/A{3,}/);
    expect(contentElement).toBeInTheDocument();
  });
});
