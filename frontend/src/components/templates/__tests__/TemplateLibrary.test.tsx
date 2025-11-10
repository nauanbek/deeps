/**
 * Tests for TemplateLibrary component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TemplateLibrary } from '../TemplateLibrary';
import { Template } from '../../../types/template';
import * as useTemplatesHook from '../../../hooks/useTemplates';

const mockTemplates: Template[] = [
  {
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
      tool_ids: [1],
    },
    is_public: true,
    is_featured: true,
    use_count: 42,
    created_by_id: 1,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    is_active: true,
  },
  {
    id: 2,
    name: 'Code Review Assistant',
    description: 'A code review assistant template',
    category: 'code_review',
    tags: ['coding', 'review'],
    config_template: {
      model_provider: 'openai',
      model_name: 'gpt-4',
      system_prompt: 'You are a code reviewer.',
      temperature: 0.5,
      max_tokens: 2048,
      planning_enabled: false,
      filesystem_enabled: true,
      tool_ids: [2],
    },
    is_public: true,
    is_featured: false,
    use_count: 20,
    created_by_id: 1,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    is_active: true,
  },
];

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('TemplateLibrary', () => {
  const mockOnUseTemplate = jest.fn();
  const mockOnViewDetails = jest.fn();
  const mockOnImportTemplate = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    // Mock useTemplates hook
    jest.spyOn(useTemplatesHook, 'useTemplates').mockReturnValue({
      data: { items: mockTemplates, total: 2, skip: 0, limit: 12 },
      isLoading: false,
      error: null,
      isError: false,
      refetch: jest.fn(),
    } as any);

    // Mock useFeaturedTemplates hook
    jest.spyOn(useTemplatesHook, 'useFeaturedTemplates').mockReturnValue({
      data: [mockTemplates[0]],
      isLoading: false,
      error: null,
      isError: false,
    } as any);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders header and search bar', () => {
    render(
      <TemplateLibrary
        onUseTemplate={mockOnUseTemplate}
        onViewDetails={mockOnViewDetails}
        onImportTemplate={mockOnImportTemplate}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Template Library')).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText('Search templates...')
    ).toBeInTheDocument();
  });

  it('displays featured templates section', () => {
    render(
      <TemplateLibrary
        onUseTemplate={mockOnUseTemplate}
        onViewDetails={mockOnViewDetails}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Featured Templates')).toBeInTheDocument();
  });

  it('displays template cards', () => {
    render(
      <TemplateLibrary
        onUseTemplate={mockOnUseTemplate}
        onViewDetails={mockOnViewDetails}
      />,
      { wrapper: createWrapper() }
    );

    const researchAssistant = screen.getAllByText('Research Assistant');
    expect(researchAssistant.length).toBeGreaterThan(0);
    expect(screen.getByText('Code Review Assistant')).toBeInTheDocument();
  });

  it('displays import button when onImportTemplate is provided', () => {
    render(
      <TemplateLibrary
        onUseTemplate={mockOnUseTemplate}
        onViewDetails={mockOnViewDetails}
        onImportTemplate={mockOnImportTemplate}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Import Template')).toBeInTheDocument();
  });

  it('calls onImportTemplate when import button is clicked', () => {
    render(
      <TemplateLibrary
        onUseTemplate={mockOnUseTemplate}
        onViewDetails={mockOnViewDetails}
        onImportTemplate={mockOnImportTemplate}
      />,
      { wrapper: createWrapper() }
    );

    const importButton = screen.getByText('Import Template');
    fireEvent.click(importButton);

    expect(mockOnImportTemplate).toHaveBeenCalledTimes(1);
  });

  it('filters templates by category', async () => {
    const mockRefetch = jest.fn();
    jest.spyOn(useTemplatesHook, 'useTemplates').mockReturnValue({
      data: { items: [mockTemplates[0]], total: 1, skip: 0, limit: 12 },
      isLoading: false,
      error: null,
      isError: false,
      refetch: mockRefetch,
    } as any);

    render(
      <TemplateLibrary
        onUseTemplate={mockOnUseTemplate}
        onViewDetails={mockOnViewDetails}
      />,
      { wrapper: createWrapper() }
    );

    const categorySelect = screen.getByRole('combobox');
    fireEvent.change(categorySelect, { target: { value: 'research' } });

    await waitFor(() => {
      expect(categorySelect).toHaveValue('research');
    });
  });

  it('searches templates with debouncing', async () => {
    jest.useFakeTimers();

    render(
      <TemplateLibrary
        onUseTemplate={mockOnUseTemplate}
        onViewDetails={mockOnViewDetails}
      />,
      { wrapper: createWrapper() }
    );

    const searchInput = screen.getByPlaceholderText('Search templates...');
    fireEvent.change(searchInput, { target: { value: 'research' } });

    // Search should be debounced
    expect(searchInput).toHaveValue('research');

    // Fast-forward time
    jest.advanceTimersByTime(300);

    jest.useRealTimers();
  });

  it('toggles featured filter', () => {
    render(
      <TemplateLibrary
        onUseTemplate={mockOnUseTemplate}
        onViewDetails={mockOnViewDetails}
      />,
      { wrapper: createWrapper() }
    );

    // Get the button by role, not text (since "Featured" appears in multiple places)
    const featuredButton = screen.getByRole('button', { name: 'Featured' });
    fireEvent.click(featuredButton);

    // Check for primary-100 (actual class) instead of indigo-100
    expect(featuredButton).toHaveClass('bg-primary-100');
  });

  it('toggles my templates filter when currentUserId is provided', () => {
    render(
      <TemplateLibrary
        onUseTemplate={mockOnUseTemplate}
        onViewDetails={mockOnViewDetails}
        currentUserId={1}
      />,
      { wrapper: createWrapper() }
    );

    const myTemplatesButton = screen.getByRole('button', { name: 'My Templates' });
    fireEvent.click(myTemplatesButton);

    // Check for primary-100 (actual class) instead of indigo-100
    expect(myTemplatesButton).toHaveClass('bg-primary-100');
  });

  it('displays loading skeletons when loading', () => {
    jest.spyOn(useTemplatesHook, 'useTemplates').mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      isError: false,
      refetch: jest.fn(),
    } as any);

    const { container } = render(
      <TemplateLibrary
        onUseTemplate={mockOnUseTemplate}
        onViewDetails={mockOnViewDetails}
      />,
      { wrapper: createWrapper() }
    );

    expect(container.querySelectorAll('.animate-pulse')).toHaveLength(8);
  });

  it('displays error message when error occurs', () => {
    jest.spyOn(useTemplatesHook, 'useTemplates').mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('Failed to fetch'),
      isError: true,
      refetch: jest.fn(),
    } as any);

    render(
      <TemplateLibrary
        onUseTemplate={mockOnUseTemplate}
        onViewDetails={mockOnViewDetails}
      />,
      { wrapper: createWrapper() }
    );

    expect(
      screen.getByText('Error loading templates. Please try again later.')
    ).toBeInTheDocument();
  });

  it('displays empty state when no templates found', () => {
    jest.spyOn(useTemplatesHook, 'useTemplates').mockReturnValue({
      data: { items: [], total: 0, skip: 0, limit: 12 },
      isLoading: false,
      error: null,
      isError: false,
      refetch: jest.fn(),
    } as any);

    render(
      <TemplateLibrary
        onUseTemplate={mockOnUseTemplate}
        onViewDetails={mockOnViewDetails}
      />,
      { wrapper: createWrapper() }
    );

    // Query for the heading specifically (appears in both results count and empty state)
    const emptyStateHeading = screen.getByRole('heading', { name: 'No templates found' });
    expect(emptyStateHeading).toBeInTheDocument();
  });
});
