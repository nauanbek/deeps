import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { AgentCard, AgentCardSkeleton } from '../AgentCard';
import type { Agent } from '../../../types/agent';

const mockAgent: Agent = {
  id: 1,
  name: 'Test Agent',
  description: 'This is a test agent description',
  system_prompt: 'You are a helpful assistant',
  model_provider: 'anthropic',
  model_name: 'claude-3-5-sonnet-20241022',
  temperature: 0.7,
  max_tokens: 4096,
  planning_enabled: true,
  filesystem_enabled: false,
  additional_config: {},
  is_active: true,
  created_by_id: 1,
  created_at: '2025-01-08T12:00:00Z',
  updated_at: '2025-01-08T13:00:00Z',
};

describe('AgentCard', () => {
  const mockOnEdit = jest.fn();
  const mockOnDelete = jest.fn();
  const mockOnExecute = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders agent information correctly', () => {
    render(
      <AgentCard
        agent={mockAgent}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onExecute={mockOnExecute}
      />
    );

    expect(screen.getByText('Test Agent')).toBeInTheDocument();
    expect(screen.getByText('This is a test agent description')).toBeInTheDocument();
    expect(screen.getByText('anthropic')).toBeInTheDocument();
    expect(screen.getByText('claude-3-5-sonnet-20241022')).toBeInTheDocument();
    expect(screen.getByText('0.7')).toBeInTheDocument();
    expect(screen.getByText('4,096')).toBeInTheDocument();
  });

  test('displays active status badge', () => {
    render(
      <AgentCard
        agent={mockAgent}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
      />
    );

    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  test('displays inactive status badge when agent is inactive', () => {
    const inactiveAgent = { ...mockAgent, is_active: false };
    render(
      <AgentCard
        agent={inactiveAgent}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
      />
    );

    expect(screen.getByText('Inactive')).toBeInTheDocument();
  });

  test('shows planning feature badge when enabled', () => {
    render(
      <AgentCard
        agent={mockAgent}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
      />
    );

    expect(screen.getByText('Planning')).toBeInTheDocument();
  });

  test('shows filesystem feature badge when enabled', () => {
    const agentWithFilesystem = { ...mockAgent, filesystem_enabled: true };
    render(
      <AgentCard
        agent={agentWithFilesystem}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
      />
    );

    expect(screen.getByText('Filesystem')).toBeInTheDocument();
  });

  test('shows "None" when no features enabled', () => {
    const agentWithoutFeatures = {
      ...mockAgent,
      planning_enabled: false,
      filesystem_enabled: false,
    };
    render(
      <AgentCard
        agent={agentWithoutFeatures}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
      />
    );

    expect(screen.getByText('None')).toBeInTheDocument();
  });

  test('truncates long descriptions', () => {
    const longDescription = 'A'.repeat(200);
    const agentWithLongDesc = { ...mockAgent, description: longDescription };
    render(
      <AgentCard
        agent={agentWithLongDesc}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
      />
    );

    const descElement = screen.getByText(/A+\.\.\./);
    expect(descElement.textContent?.length).toBeLessThan(longDescription.length);
  });

  test('calls onEdit when edit button clicked', () => {
    render(
      <AgentCard
        agent={mockAgent}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
      />
    );

    const editButton = screen.getByRole('button', { name: /edit test agent/i });
    fireEvent.click(editButton);
    expect(mockOnEdit).toHaveBeenCalledWith(mockAgent);
    expect(mockOnEdit).toHaveBeenCalledTimes(1);
  });

  test('calls onDelete when delete button clicked', () => {
    render(
      <AgentCard
        agent={mockAgent}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
      />
    );

    const deleteButton = screen.getByRole('button', { name: /delete test agent/i });
    fireEvent.click(deleteButton);
    expect(mockOnDelete).toHaveBeenCalledWith(mockAgent.id);
    expect(mockOnDelete).toHaveBeenCalledTimes(1);
  });

  test('calls onExecute when execute button clicked', () => {
    render(
      <AgentCard
        agent={mockAgent}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onExecute={mockOnExecute}
      />
    );

    const executeButton = screen.getByRole('button', { name: /execute test agent/i });
    fireEvent.click(executeButton);
    expect(mockOnExecute).toHaveBeenCalledWith(mockAgent.id);
    expect(mockOnExecute).toHaveBeenCalledTimes(1);
  });

  test('does not render execute button when onExecute is not provided', () => {
    render(
      <AgentCard
        agent={mockAgent}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
      />
    );

    const executeButton = screen.queryByRole('button', { name: /execute test agent/i });
    expect(executeButton).not.toBeInTheDocument();
  });

  test('displays formatted timestamp', () => {
    render(
      <AgentCard
        agent={mockAgent}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
      />
    );

    // Should show relative time like "X hours ago"
    expect(screen.getByText(/ago/i)).toBeInTheDocument();
  });

  test('uses created_at when updated_at is null', () => {
    const agentWithoutUpdate = { ...mockAgent, updated_at: null };
    render(
      <AgentCard
        agent={agentWithoutUpdate}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
      />
    );

    // Should still show a timestamp
    expect(screen.getByText(/ago/i)).toBeInTheDocument();
  });
});

describe('AgentCardSkeleton', () => {
  test('renders loading skeleton', () => {
    const { container } = render(<AgentCardSkeleton />);

    // Should have animate-pulse class
    const skeleton = container.querySelector('.animate-pulse');
    expect(skeleton).toBeInTheDocument();
  });
});
