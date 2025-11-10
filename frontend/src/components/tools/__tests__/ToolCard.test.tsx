/**
 * ToolCard component tests
 */

import { render, screen, fireEvent } from '@testing-library/react';
import ToolCard from '../ToolCard';
import type { Tool } from '../../../types/tool';

describe('ToolCard', () => {
  const mockTool: Tool = {
    id: 1,
    name: 'Calculator',
    description: 'Performs mathematical calculations',
    tool_type: 'builtin',
    configuration: { precision: 10 },
    schema_definition: {},
    is_active: true,
    created_by_id: 1,
    created_at: '2025-01-08T12:00:00Z',
    updated_at: '2025-01-08T12:00:00Z',
  };

  const mockOnEdit = jest.fn();
  const mockOnDelete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders tool name', () => {
    render(<ToolCard tool={mockTool} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    expect(screen.getByText('Calculator')).toBeInTheDocument();
  });

  test('renders tool description', () => {
    render(<ToolCard tool={mockTool} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    expect(screen.getByText('Performs mathematical calculations')).toBeInTheDocument();
  });

  test('renders tool type badge', () => {
    render(<ToolCard tool={mockTool} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    expect(screen.getByText('builtin')).toBeInTheDocument();
  });

  test('displays default text when description is null', () => {
    const toolWithoutDescription: Tool = {
      ...mockTool,
      description: null,
    };
    render(<ToolCard tool={toolWithoutDescription} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    expect(screen.getByText('No description provided')).toBeInTheDocument();
  });

  test('displays configuration count when configuration exists', () => {
    render(<ToolCard tool={mockTool} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    expect(screen.getByText('1 configuration option')).toBeInTheDocument();
  });

  test('displays correct plural for multiple configuration options', () => {
    const toolWithMultipleConfigs: Tool = {
      ...mockTool,
      configuration: { precision: 10, maxValue: 100 },
    };
    render(<ToolCard tool={toolWithMultipleConfigs} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    expect(screen.getByText('2 configuration options')).toBeInTheDocument();
  });

  test('does not display configuration count when configuration is null', () => {
    const toolWithoutConfig: Tool = {
      ...mockTool,
      configuration: null,
    };
    render(<ToolCard tool={toolWithoutConfig} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    expect(screen.queryByText(/configuration option/)).not.toBeInTheDocument();
  });

  test('does not display configuration count when configuration is empty', () => {
    const toolWithEmptyConfig: Tool = {
      ...mockTool,
      configuration: {},
    };
    render(<ToolCard tool={toolWithEmptyConfig} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    expect(screen.queryByText(/configuration option/)).not.toBeInTheDocument();
  });

  test('calls onEdit when edit button is clicked', () => {
    render(<ToolCard tool={mockTool} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    const editButton = screen.getByRole('button', { name: /edit calculator/i });
    fireEvent.click(editButton);
    expect(mockOnEdit).toHaveBeenCalledTimes(1);
  });

  test('calls onDelete when delete button is clicked', () => {
    render(<ToolCard tool={mockTool} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    const deleteButton = screen.getByRole('button', { name: /delete calculator/i });
    fireEvent.click(deleteButton);
    expect(mockOnDelete).toHaveBeenCalledTimes(1);
  });

  test('applies correct styling for builtin tool type', () => {
    render(<ToolCard tool={mockTool} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    const badge = screen.getByText('builtin');
    expect(badge).toHaveClass('bg-blue-100', 'text-blue-800', 'border-blue-200');
  });

  test('applies correct styling for custom tool type', () => {
    const customTool: Tool = {
      ...mockTool,
      tool_type: 'custom',
    };
    render(<ToolCard tool={customTool} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    const badge = screen.getByText('custom');
    expect(badge).toHaveClass('bg-purple-100', 'text-purple-800', 'border-purple-200');
  });

  test('applies correct styling for langgraph tool type', () => {
    const langgraphTool: Tool = {
      ...mockTool,
      tool_type: 'langgraph',
    };
    render(<ToolCard tool={langgraphTool} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    const badge = screen.getByText('langgraph');
    expect(badge).toHaveClass('bg-green-100', 'text-green-800', 'border-green-200');
  });

  test('renders wrench icon', () => {
    const { container } = render(<ToolCard tool={mockTool} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    const icon = container.querySelector('svg');
    expect(icon).toBeInTheDocument();
  });

  test('renders edit and delete buttons', () => {
    render(<ToolCard tool={mockTool} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    expect(screen.getByText('Edit')).toBeInTheDocument();
    expect(screen.getByText('Delete')).toBeInTheDocument();
  });

  test('has proper accessibility attributes on edit button', () => {
    render(<ToolCard tool={mockTool} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    const editButton = screen.getByRole('button', { name: /edit calculator/i });
    expect(editButton).toHaveAttribute('aria-label', 'Edit Calculator');
  });

  test('has proper accessibility attributes on delete button', () => {
    render(<ToolCard tool={mockTool} onEdit={mockOnEdit} onDelete={mockOnDelete} />);
    const deleteButton = screen.getByRole('button', { name: /delete calculator/i });
    expect(deleteButton).toHaveAttribute('aria-label', 'Delete Calculator');
  });
});
