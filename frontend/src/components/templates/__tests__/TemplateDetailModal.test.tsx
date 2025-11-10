/**
 * Tests for TemplateDetailModal component
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { TemplateDetailModal } from '../TemplateDetailModal';
import { Template } from '../../../types/template';

const mockTemplate: Template = {
  id: 1,
  name: 'Research Assistant',
  description: 'A powerful research assistant template',
  category: 'research',
  tags: ['research', 'analysis', 'web-search'],
  config_template: {
    model_provider: 'anthropic',
    model_name: 'claude-3-5-sonnet-20241022',
    system_prompt: 'You are a helpful research assistant.',
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
  created_at: '2024-01-15T10:00:00Z',
  updated_at: '2024-01-20T15:30:00Z',
  is_active: true,
};

describe('TemplateDetailModal', () => {
  const mockOnClose = jest.fn();
  const mockOnUseTemplate = jest.fn();
  const mockOnEditTemplate = jest.fn();
  const mockOnDeleteTemplate = jest.fn();
  const mockOnExportTemplate = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('does not render when isOpen is false', () => {
    render(
      <TemplateDetailModal
        template={mockTemplate}
        isOpen={false}
        onClose={mockOnClose}
        onUseTemplate={mockOnUseTemplate}
        onExportTemplate={mockOnExportTemplate}
      />
    );

    expect(screen.queryByText('Research Assistant')).not.toBeInTheDocument();
  });

  it('renders modal when isOpen is true', () => {
    render(
      <TemplateDetailModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onUseTemplate={mockOnUseTemplate}
        onExportTemplate={mockOnExportTemplate}
      />
    );

    expect(screen.getByText('Research Assistant')).toBeInTheDocument();
  });

  it('displays template name and category', () => {
    render(
      <TemplateDetailModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onUseTemplate={mockOnUseTemplate}
        onExportTemplate={mockOnExportTemplate}
      />
    );

    expect(screen.getByText('Research Assistant')).toBeInTheDocument();
    expect(screen.getByText('Research')).toBeInTheDocument();
  });

  it('displays featured badge when template is featured', () => {
    render(
      <TemplateDetailModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onUseTemplate={mockOnUseTemplate}
        onExportTemplate={mockOnExportTemplate}
      />
    );

    expect(screen.getByText('Featured')).toBeInTheDocument();
  });

  it('displays use count', () => {
    render(
      <TemplateDetailModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onUseTemplate={mockOnUseTemplate}
        onExportTemplate={mockOnExportTemplate}
      />
    );

    expect(screen.getByText('42 uses')).toBeInTheDocument();
  });

  it('renders all three tabs', () => {
    render(
      <TemplateDetailModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onUseTemplate={mockOnUseTemplate}
        onExportTemplate={mockOnExportTemplate}
      />
    );

    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('Configuration')).toBeInTheDocument();
    expect(screen.getByText('System Prompt')).toBeInTheDocument();
  });

  it('displays overview tab content by default', () => {
    render(
      <TemplateDetailModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onUseTemplate={mockOnUseTemplate}
        onExportTemplate={mockOnExportTemplate}
      />
    );

    expect(screen.getByText('Description')).toBeInTheDocument();
    expect(screen.getByText('A powerful research assistant template')).toBeInTheDocument();
  });

  it('displays tags in overview tab', () => {
    render(
      <TemplateDetailModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onUseTemplate={mockOnUseTemplate}
        onExportTemplate={mockOnExportTemplate}
      />
    );

    expect(screen.getByText('research')).toBeInTheDocument();
    expect(screen.getByText('analysis')).toBeInTheDocument();
    expect(screen.getByText('web-search')).toBeInTheDocument();
  });

  it('switches to configuration tab when clicked', () => {
    render(
      <TemplateDetailModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onUseTemplate={mockOnUseTemplate}
        onExportTemplate={mockOnExportTemplate}
      />
    );

    const configTab = screen.getByText('Configuration');
    fireEvent.click(configTab);

    expect(screen.getByText('Model Provider')).toBeInTheDocument();
    expect(screen.getByText('Claude')).toBeInTheDocument();
    expect(screen.getByText('claude-3-5-sonnet-20241022')).toBeInTheDocument();
  });

  it('displays configuration details in configuration tab', () => {
    render(
      <TemplateDetailModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onUseTemplate={mockOnUseTemplate}
        onExportTemplate={mockOnExportTemplate}
      />
    );

    fireEvent.click(screen.getByText('Configuration'));

    expect(screen.getByText('Temperature')).toBeInTheDocument();
    expect(screen.getByText('0.7')).toBeInTheDocument();
    expect(screen.getByText('Max Tokens')).toBeInTheDocument();
    expect(screen.getByText('4096')).toBeInTheDocument();
  });

  it('switches to system prompt tab when clicked', () => {
    render(
      <TemplateDetailModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onUseTemplate={mockOnUseTemplate}
        onExportTemplate={mockOnExportTemplate}
      />
    );

    const promptTab = screen.getByText('System Prompt');
    fireEvent.click(promptTab);

    expect(screen.getByText('You are a helpful research assistant.')).toBeInTheDocument();
  });

  it('displays export button', () => {
    render(
      <TemplateDetailModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onUseTemplate={mockOnUseTemplate}
        onExportTemplate={mockOnExportTemplate}
      />
    );

    expect(screen.getByText('Export')).toBeInTheDocument();
  });

  it('calls onExportTemplate when export button is clicked', () => {
    render(
      <TemplateDetailModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onUseTemplate={mockOnUseTemplate}
        onExportTemplate={mockOnExportTemplate}
      />
    );

    const exportButton = screen.getByText('Export');
    fireEvent.click(exportButton);

    expect(mockOnExportTemplate).toHaveBeenCalledTimes(1);
    expect(mockOnExportTemplate).toHaveBeenCalledWith(1);
  });

  it('displays edit and delete buttons for owner', () => {
    render(
      <TemplateDetailModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onUseTemplate={mockOnUseTemplate}
        onEditTemplate={mockOnEditTemplate}
        onDeleteTemplate={mockOnDeleteTemplate}
        onExportTemplate={mockOnExportTemplate}
        currentUserId={1}
      />
    );

    expect(screen.getByText('Edit')).toBeInTheDocument();
    expect(screen.getByText('Delete')).toBeInTheDocument();
  });

  it('does not display edit and delete buttons for non-owner', () => {
    render(
      <TemplateDetailModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onUseTemplate={mockOnUseTemplate}
        onEditTemplate={mockOnEditTemplate}
        onDeleteTemplate={mockOnDeleteTemplate}
        onExportTemplate={mockOnExportTemplate}
        currentUserId={2}
      />
    );

    expect(screen.queryByText('Edit')).not.toBeInTheDocument();
    expect(screen.queryByText('Delete')).not.toBeInTheDocument();
  });

  it('calls onEditTemplate when edit button is clicked', () => {
    render(
      <TemplateDetailModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onUseTemplate={mockOnUseTemplate}
        onEditTemplate={mockOnEditTemplate}
        onDeleteTemplate={mockOnDeleteTemplate}
        onExportTemplate={mockOnExportTemplate}
        currentUserId={1}
      />
    );

    const editButton = screen.getByText('Edit');
    fireEvent.click(editButton);

    expect(mockOnEditTemplate).toHaveBeenCalledTimes(1);
    expect(mockOnEditTemplate).toHaveBeenCalledWith(mockTemplate);
  });

  it('calls onDeleteTemplate when delete button is clicked', () => {
    render(
      <TemplateDetailModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onUseTemplate={mockOnUseTemplate}
        onEditTemplate={mockOnEditTemplate}
        onDeleteTemplate={mockOnDeleteTemplate}
        onExportTemplate={mockOnExportTemplate}
        currentUserId={1}
      />
    );

    const deleteButton = screen.getByText('Delete');
    fireEvent.click(deleteButton);

    expect(mockOnDeleteTemplate).toHaveBeenCalledTimes(1);
    expect(mockOnDeleteTemplate).toHaveBeenCalledWith(mockTemplate);
  });

  it('calls onUseTemplate when Use This Template button is clicked', () => {
    render(
      <TemplateDetailModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onUseTemplate={mockOnUseTemplate}
        onExportTemplate={mockOnExportTemplate}
      />
    );

    const useButton = screen.getByText('Use This Template');
    fireEvent.click(useButton);

    expect(mockOnUseTemplate).toHaveBeenCalledTimes(1);
    expect(mockOnUseTemplate).toHaveBeenCalledWith(mockTemplate);
  });

  it('calls onClose when close button is clicked', () => {
    render(
      <TemplateDetailModal
        template={mockTemplate}
        isOpen={true}
        onClose={mockOnClose}
        onUseTemplate={mockOnUseTemplate}
        onExportTemplate={mockOnExportTemplate}
      />
    );

    const closeButton = screen.getByLabelText('Close modal');
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });
});
