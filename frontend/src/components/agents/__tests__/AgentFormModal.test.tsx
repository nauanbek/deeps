import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { AgentFormModal } from '../AgentFormModal';
import type { Agent } from '../../../types/agent';

// Mock Monaco Editor
jest.mock('@monaco-editor/react', () => ({
  __esModule: true,
  default: ({ value, onChange }: any) => (
    <textarea
      data-testid="monaco-editor"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  ),
}));

const mockAgent: Agent = {
  id: 1,
  name: 'Test Agent',
  description: 'Test description',
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

describe('AgentFormModal', () => {
  const mockOnClose = jest.fn();
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockOnSubmit.mockResolvedValue(undefined);
  });

  test('renders create modal correctly', () => {
    render(
      <AgentFormModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    expect(screen.getByRole('heading', { name: /create agent/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/model provider/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^create agent$/i })).toBeInTheDocument();
  });

  test('renders edit modal with agent data', () => {
    render(
      <AgentFormModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
        agent={mockAgent}
      />
    );

    expect(screen.getByRole('heading', { name: /edit agent/i })).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test Agent')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test description')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^update agent$/i })).toBeInTheDocument();
  });

  test('validates required fields', async () => {
    render(
      <AgentFormModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const nameInput = screen.getByLabelText(/name/i);
    const submitButton = screen.getByRole('button', { name: /create agent/i });

    // Clear the name field
    await userEvent.clear(nameInput);
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/name is required/i)).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  test('validates system prompt is required', async () => {
    render(
      <AgentFormModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const nameInput = screen.getByLabelText(/name/i);
    const systemPromptEditor = screen.getByTestId('monaco-editor');
    const submitButton = screen.getByRole('button', { name: /create agent/i });

    await userEvent.type(nameInput, 'Test Agent');
    await userEvent.clear(systemPromptEditor);

    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/system prompt is required/i)).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  test('validates temperature range', async () => {
    render(
      <AgentFormModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    // Fill in required fields first
    const nameInput = screen.getByLabelText(/^name/i);  // Label is just "Name", not "Agent Name"
    const descInput = screen.getByLabelText(/description/i);
    const temperatureSlider = screen.getByLabelText(/temperature:/i);
    const submitButton = screen.getByRole('button', { name: /create agent/i });

    fireEvent.change(nameInput, { target: { value: 'Test Agent' } });
    fireEvent.change(descInput, { target: { value: 'Test description' } });

    // Set temperature to value within valid range
    fireEvent.change(temperatureSlider, { target: { value: '0.7' } });
    fireEvent.click(submitButton);

    // Form should submit with valid temperature
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalled();
    });
  });

  test('submits form with valid data', async () => {
    render(
      <AgentFormModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const nameInput = screen.getByLabelText(/name/i);
    const descriptionInput = screen.getByLabelText(/description/i);
    const submitButton = screen.getByRole('button', { name: /create agent/i });

    await userEvent.type(nameInput, 'My New Agent');
    await userEvent.type(descriptionInput, 'A great agent');

    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalled();
    });

    const submittedData = mockOnSubmit.mock.calls[0][0];
    expect(submittedData.name).toBe('My New Agent');
    expect(submittedData.description).toBe('A great agent');
  });

  test('updates model options when provider changes', async () => {
    render(
      <AgentFormModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const providerSelect = screen.getByLabelText(/model provider/i);

    // Change to OpenAI
    fireEvent.change(providerSelect, { target: { value: 'openai' } });

    // Wait for the model select to update
    await waitFor(() => {
      const options = screen.getAllByRole('option');
      const hasGPT = options.some(option => option.textContent?.includes('GPT'));
      expect(hasGPT).toBe(true);
    });
  });

  test('toggles planning enabled', async () => {
    render(
      <AgentFormModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const planningCheckbox = screen.getByLabelText(/planning enabled/i);

    expect(planningCheckbox).not.toBeChecked();

    fireEvent.click(planningCheckbox);

    await waitFor(() => {
      expect(planningCheckbox).toBeChecked();
    });
  });

  test('toggles filesystem enabled', async () => {
    render(
      <AgentFormModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const filesystemCheckbox = screen.getByLabelText(/filesystem enabled/i);

    expect(filesystemCheckbox).not.toBeChecked();

    fireEvent.click(filesystemCheckbox);

    await waitFor(() => {
      expect(filesystemCheckbox).toBeChecked();
    });
  });

  test('shows loading state when submitting', async () => {
    render(
      <AgentFormModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
        isSubmitting={true}
      />
    );

    const submitButton = screen.getByRole('button', { name: /creating/i });
    expect(submitButton).toBeDisabled();
  });

  test('closes modal on cancel', () => {
    render(
      <AgentFormModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  test('does not close modal on submit error', async () => {
    mockOnSubmit.mockRejectedValue(new Error('Submit failed'));

    render(
      <AgentFormModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    const nameInput = screen.getByLabelText(/name/i);
    const submitButton = screen.getByRole('button', { name: /create agent/i });

    await userEvent.type(nameInput, 'Test');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalled();
    });

    expect(mockOnClose).not.toHaveBeenCalled();
  });

  test('updates form when agent prop changes', async () => {
    const { rerender } = render(
      <AgentFormModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />
    );

    expect(screen.getByDisplayValue('You are a helpful AI assistant.')).toBeInTheDocument();

    rerender(
      <AgentFormModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
        agent={mockAgent}
      />
    );

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Agent')).toBeInTheDocument();
    });
  });
});
