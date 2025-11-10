/**
 * Tests for CreateAgentFromTemplateModal component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CreateAgentFromTemplateModal } from '../CreateAgentFromTemplateModal';
import { Template } from '../../../types/template';

const mockTemplate: Template = {
  id: 1,
  name: 'Research Assistant',
  description: 'A research assistant template',
  category: 'research',
  tags: ['research', 'analysis'],
  config_template: {
    model_provider: 'anthropic',
    model_name: 'claude-3-5-sonnet-20241022',
    system_prompt: 'You are a research assistant.',
    temperature: 0.7,
    max_tokens: 4096,
    planning_enabled: true,
    filesystem_enabled: true,
    tool_ids: [1, 2, 3],
  },
  is_public: true,
  is_featured: true,
  use_count: 42,
  created_by_id: 1,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  is_active: true,
};

describe('CreateAgentFromTemplateModal', () => {
  const mockOnClose = jest.fn();
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('does not render when isOpen is false', () => {
    render(
      <CreateAgentFromTemplateModal
        template={mockTemplate}
        isOpen={false}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    expect(screen.queryByText('Create Agent from Template')).not.toBeInTheDocument();
  });

  it('renders modal when isOpen is true', () => {
    render(
      <CreateAgentFromTemplateModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    expect(screen.getByText('Create Agent from Template')).toBeInTheDocument();
  });

  it('pre-fills form with template data', () => {
    render(
      <CreateAgentFromTemplateModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const nameInput = screen.getByLabelText(/Agent Name/i) as HTMLInputElement;
    const descriptionInput = screen.getByLabelText(/Description/i) as HTMLTextAreaElement;
    const temperatureInput = screen.getByLabelText(/Temperature/i) as HTMLInputElement;
    const maxTokensInput = screen.getByLabelText(/Max Tokens/i) as HTMLInputElement;

    expect(nameInput.value).toBe('Research Assistant');
    expect(descriptionInput.value).toBe('A research assistant template');
    expect(temperatureInput.value).toBe('0.7');
    expect(maxTokensInput.value).toBe('4096');
  });

  it('displays template reference information', () => {
    render(
      <CreateAgentFromTemplateModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    expect(screen.getByText(/Template: Research Assistant/i)).toBeInTheDocument();
  });

  it('displays configuration preview', () => {
    render(
      <CreateAgentFromTemplateModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    expect(screen.getByText('Final Configuration Preview')).toBeInTheDocument();
    expect(screen.getByText('claude-3-5-sonnet-20241022')).toBeInTheDocument();
    expect(screen.getByText('anthropic')).toBeInTheDocument();
  });

  it('allows editing agent name', () => {
    render(
      <CreateAgentFromTemplateModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const nameInput = screen.getByLabelText(/Agent Name/i) as HTMLInputElement;
    fireEvent.change(nameInput, { target: { value: 'My Custom Agent' } });

    expect(nameInput.value).toBe('My Custom Agent');
  });

  it('allows editing description', () => {
    render(
      <CreateAgentFromTemplateModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const descriptionInput = screen.getByLabelText(/Description/i) as HTMLTextAreaElement;
    fireEvent.change(descriptionInput, { target: { value: 'Custom description' } });

    expect(descriptionInput.value).toBe('Custom description');
  });

  it('allows editing temperature', () => {
    render(
      <CreateAgentFromTemplateModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const temperatureInput = screen.getByLabelText(/Temperature/i) as HTMLInputElement;
    fireEvent.change(temperatureInput, { target: { value: '0.9' } });

    expect(temperatureInput.value).toBe('0.9');
  });

  it('allows editing max tokens', () => {
    render(
      <CreateAgentFromTemplateModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const maxTokensInput = screen.getByLabelText(/Max Tokens/i) as HTMLInputElement;
    fireEvent.change(maxTokensInput, { target: { value: '8192' } });

    expect(maxTokensInput.value).toBe('8192');
  });

  it('submits form with correct data', async () => {
    render(
      <CreateAgentFromTemplateModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const nameInput = screen.getByLabelText(/Agent Name/i);
    fireEvent.change(nameInput, { target: { value: 'My Agent' } });

    const submitButton = screen.getByText('Create Agent');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledTimes(1);
      expect(mockOnSubmit).toHaveBeenCalledWith(1, {
        template_id: 1,
        name: 'My Agent',
        description: 'A research assistant template',
        config_overrides: {
          temperature: 0.7,
          max_tokens: 4096,
        },
      });
    });
  });

  it('disables submit button when name is empty', () => {
    render(
      <CreateAgentFromTemplateModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const nameInput = screen.getByLabelText(/Agent Name/i);
    fireEvent.change(nameInput, { target: { value: '' } });

    const submitButton = screen.getByText('Create Agent');
    expect(submitButton).toBeDisabled();
  });

  it('disables form when loading', () => {
    render(
      <CreateAgentFromTemplateModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
        isLoading={true}
      />
    );

    const nameInput = screen.getByLabelText(/Agent Name/i);
    const submitButton = screen.getByText('Creating...');

    expect(nameInput).toBeDisabled();
    expect(submitButton).toBeDisabled();
  });

  it('calls onClose when cancel button is clicked', () => {
    render(
      <CreateAgentFromTemplateModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when close icon is clicked', () => {
    render(
      <CreateAgentFromTemplateModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const closeButton = screen.getByLabelText('Close modal');
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });
});
