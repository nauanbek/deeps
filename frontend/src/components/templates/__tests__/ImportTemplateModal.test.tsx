/**
 * Tests for ImportTemplateModal component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ImportTemplateModal } from '../ImportTemplateModal';

describe('ImportTemplateModal', () => {
  const mockOnClose = jest.fn();
  const mockOnImport = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('does not render when isOpen is false', () => {
    render(
      <ImportTemplateModal
        isOpen={false}
        onClose={mockOnClose}
        onImport={mockOnImport}
      />
    );

    expect(screen.queryByText('Import Template')).not.toBeInTheDocument();
  });

  it('renders modal when isOpen is true', () => {
    render(
      <ImportTemplateModal
        isOpen={true}
        onClose={mockOnClose}
        onImport={mockOnImport}
      />
    );

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-labelledby', 'import-template-title');
  });

  it('displays file upload area', () => {
    render(
      <ImportTemplateModal
        isOpen={true}
        onClose={mockOnClose}
        onImport={mockOnImport}
      />
    );

    expect(
      screen.getByText(/Drag and drop a JSON file here/i)
    ).toBeInTheDocument();
    expect(screen.getByText('browse files')).toBeInTheDocument();
  });

  it('displays file size limit', () => {
    render(
      <ImportTemplateModal
        isOpen={true}
        onClose={mockOnClose}
        onImport={mockOnImport}
      />
    );

    expect(screen.getByText('Maximum file size: 5MB')).toBeInTheDocument();
  });

  it('displays info about JSON format', () => {
    render(
      <ImportTemplateModal
        isOpen={true}
        onClose={mockOnClose}
        onImport={mockOnImport}
      />
    );

    expect(screen.getByText('Template JSON Format')).toBeInTheDocument();
  });

  it('allows file selection via input', () => {
    render(
      <ImportTemplateModal
        isOpen={true}
        onClose={mockOnClose}
        onImport={mockOnImport}
      />
    );

    const file = new File(['{"name": "test"}'], 'template.json', {
      type: 'application/json',
    });

    const input = screen.getByLabelText('File upload');
    Object.defineProperty(input, 'files', {
      value: [file],
    });

    fireEvent.change(input);

    expect(screen.getByText('template.json')).toBeInTheDocument();
  });

  it('displays selected file information', () => {
    render(
      <ImportTemplateModal
        isOpen={true}
        onClose={mockOnClose}
        onImport={mockOnImport}
      />
    );

    const file = new File(['{"name": "test"}'], 'template.json', {
      type: 'application/json',
    });

    const input = screen.getByLabelText('File upload');
    Object.defineProperty(input, 'files', {
      value: [file],
    });

    fireEvent.change(input);

    expect(screen.getByText('template.json')).toBeInTheDocument();
    expect(screen.getByText(/KB/)).toBeInTheDocument();
  });

  it('allows removing selected file', () => {
    render(
      <ImportTemplateModal
        isOpen={true}
        onClose={mockOnClose}
        onImport={mockOnImport}
      />
    );

    const file = new File(['{"name": "test"}'], 'template.json', {
      type: 'application/json',
    });

    const input = screen.getByLabelText('File upload');
    Object.defineProperty(input, 'files', {
      value: [file],
    });

    fireEvent.change(input);

    const removeButton = screen.getByLabelText('Remove file');
    fireEvent.click(removeButton);

    expect(screen.queryByText('template.json')).not.toBeInTheDocument();
  });

  it('disables import button when no file is selected', () => {
    render(
      <ImportTemplateModal
        isOpen={true}
        onClose={mockOnClose}
        onImport={mockOnImport}
      />
    );

    const importButton = screen.getByRole('button', { name: /import template/i });
    expect(importButton).toBeDisabled();
  });

  it('enables import button when file is selected', () => {
    render(
      <ImportTemplateModal
        isOpen={true}
        onClose={mockOnClose}
        onImport={mockOnImport}
      />
    );

    const file = new File(['{"name": "test"}'], 'template.json', {
      type: 'application/json',
    });

    const input = screen.getByLabelText('File upload');
    Object.defineProperty(input, 'files', {
      value: [file],
    });

    fireEvent.change(input);

    const importButton = screen.getByRole('button', { name: /import template/i });
    expect(importButton).not.toBeDisabled();
  });

  it('calls onImport when form is submitted with valid file', async () => {
    render(
      <ImportTemplateModal
        isOpen={true}
        onClose={mockOnClose}
        onImport={mockOnImport}
      />
    );

    const file = new File(['{"name": "test"}'], 'template.json', {
      type: 'application/json',
    });

    const input = screen.getByLabelText('File upload');
    Object.defineProperty(input, 'files', {
      value: [file],
    });

    fireEvent.change(input);

    const importButton = screen.getByRole('button', { name: /import template/i });
    fireEvent.click(importButton);

    await waitFor(() => {
      expect(mockOnImport).toHaveBeenCalledTimes(1);
      expect(mockOnImport).toHaveBeenCalledWith(file);
    });
  });

  it('displays loading state when importing', () => {
    render(
      <ImportTemplateModal
        isOpen={true}
        onClose={mockOnClose}
        onImport={mockOnImport}
        isLoading={true}
      />
    );

    expect(screen.getByText('Importing...')).toBeInTheDocument();
  });

  it('disables form when loading', () => {
    render(
      <ImportTemplateModal
        isOpen={true}
        onClose={mockOnClose}
        onImport={mockOnImport}
        isLoading={true}
      />
    );

    const importButton = screen.getByText('Importing...');
    const cancelButton = screen.getByText('Cancel');

    expect(importButton).toBeDisabled();
    expect(cancelButton).toBeDisabled();
  });

  it('calls onClose when cancel button is clicked', () => {
    render(
      <ImportTemplateModal
        isOpen={true}
        onClose={mockOnClose}
        onImport={mockOnImport}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when close icon is clicked', () => {
    render(
      <ImportTemplateModal
        isOpen={true}
        onClose={mockOnClose}
        onImport={mockOnImport}
      />
    );

    const closeButton = screen.getByLabelText('Close modal');
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('validates file type', () => {
    render(
      <ImportTemplateModal
        isOpen={true}
        onClose={mockOnClose}
        onImport={mockOnImport}
      />
    );

    const file = new File(['test'], 'template.txt', { type: 'text/plain' });

    const input = screen.getByLabelText('File upload');
    Object.defineProperty(input, 'files', {
      value: [file],
    });

    fireEvent.change(input);

    expect(
      screen.getByText('Please select a JSON file (.json)')
    ).toBeInTheDocument();
  });
});
