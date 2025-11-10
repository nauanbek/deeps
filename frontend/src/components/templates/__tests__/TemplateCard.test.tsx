/**
 * Tests for TemplateCard component
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { TemplateCard, TemplateCardSkeleton } from '../TemplateCard';
import { Template } from '../../../types/template';

const mockTemplate: Template = {
  id: 1,
  name: 'Research Assistant',
  description:
    'A powerful research assistant that can help you find and analyze information from various sources.',
  category: 'research',
  tags: ['research', 'analysis', 'web-search', 'data-processing'],
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

describe('TemplateCard', () => {
  const mockOnUseTemplate = jest.fn();
  const mockOnViewDetails = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders template information correctly', () => {
    render(
      <TemplateCard
        template={mockTemplate}
        onUseTemplate={mockOnUseTemplate}
        onViewDetails={mockOnViewDetails}
      />
    );

    expect(screen.getByText('Research Assistant')).toBeInTheDocument();
    expect(
      screen.getByText(/powerful research assistant/i)
    ).toBeInTheDocument();
    expect(screen.getByText('Research')).toBeInTheDocument();
    expect(screen.getByText('42 uses')).toBeInTheDocument();
    expect(screen.getByText('Claude')).toBeInTheDocument();
  });

  it('displays featured badge when template is featured', () => {
    render(
      <TemplateCard
        template={mockTemplate}
        onUseTemplate={mockOnUseTemplate}
        onViewDetails={mockOnViewDetails}
      />
    );

    expect(screen.getByText('Featured')).toBeInTheDocument();
  });

  it('does not display featured badge when template is not featured', () => {
    const nonFeaturedTemplate = { ...mockTemplate, is_featured: false };

    render(
      <TemplateCard
        template={nonFeaturedTemplate}
        onUseTemplate={mockOnUseTemplate}
        onViewDetails={mockOnViewDetails}
      />
    );

    expect(screen.queryByText('Featured')).not.toBeInTheDocument();
  });

  it('displays first 3 tags and shows count of remaining tags', () => {
    render(
      <TemplateCard
        template={mockTemplate}
        onUseTemplate={mockOnUseTemplate}
        onViewDetails={mockOnViewDetails}
      />
    );

    expect(screen.getByText('research')).toBeInTheDocument();
    expect(screen.getByText('analysis')).toBeInTheDocument();
    expect(screen.getByText('web-search')).toBeInTheDocument();
    expect(screen.getByText('+1 more')).toBeInTheDocument();
  });

  it('truncates long descriptions', () => {
    const longDescription =
      'A'.repeat(150) + ' This text should be truncated and not visible';
    const templateWithLongDesc = {
      ...mockTemplate,
      description: longDescription,
    };

    render(
      <TemplateCard
        template={templateWithLongDesc}
        onUseTemplate={mockOnUseTemplate}
        onViewDetails={mockOnViewDetails}
      />
    );

    const description = screen.getByText(/A{100}\.\.\.$/);
    expect(description).toBeInTheDocument();
    expect(screen.queryByText('This text should be truncated')).not.toBeInTheDocument();
  });

  it('displays correct provider name for OpenAI', () => {
    const openAiTemplate = {
      ...mockTemplate,
      config_template: {
        ...mockTemplate.config_template,
        model_provider: 'openai' as const,
      },
    };

    render(
      <TemplateCard
        template={openAiTemplate}
        onUseTemplate={mockOnUseTemplate}
        onViewDetails={mockOnViewDetails}
      />
    );

    expect(screen.getByText('OpenAI')).toBeInTheDocument();
  });

  it('calls onUseTemplate when Use Template button is clicked', () => {
    render(
      <TemplateCard
        template={mockTemplate}
        onUseTemplate={mockOnUseTemplate}
        onViewDetails={mockOnViewDetails}
      />
    );

    const useButton = screen.getByText('Use Template');
    fireEvent.click(useButton);

    expect(mockOnUseTemplate).toHaveBeenCalledTimes(1);
    expect(mockOnUseTemplate).toHaveBeenCalledWith(mockTemplate);
  });

  it('calls onViewDetails when view details button is clicked', () => {
    render(
      <TemplateCard
        template={mockTemplate}
        onUseTemplate={mockOnUseTemplate}
        onViewDetails={mockOnViewDetails}
      />
    );

    const viewButton = screen.getByLabelText('View details');
    fireEvent.click(viewButton);

    expect(mockOnViewDetails).toHaveBeenCalledTimes(1);
    expect(mockOnViewDetails).toHaveBeenCalledWith(mockTemplate);
  });
});

describe('TemplateCardSkeleton', () => {
  it('renders loading skeleton', () => {
    const { container } = render(<TemplateCardSkeleton />);

    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });
});
